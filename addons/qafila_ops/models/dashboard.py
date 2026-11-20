"""Tableau de bord d'exploitation Qafila (première vue de l'ERP).

Type : opérationnel (utilisé chaque matin par le responsable logistique).
Questions auxquelles l'écran répond, dans cet ordre :
  1. Qu'est-ce qui demande une action maintenant ?            → liste « À traiter »
  2. Les expéditions avancent-elles ?                            → indicateur principal + tableau
  3. La flotte est-elle disponible ?                             → disponibilité + exceptions
  4. L'argent rentre-t-il ?                                       → CA du mois vs mois précédent, encours
"""
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError

from .fleet_vehicle import QAFILA_STATUS

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
             "septembre", "octobre", "novembre", "décembre"]
DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
NBSP = " "


def _num(value, decimals=0):
    txt = f"{value:,.{decimals}f}".replace(",", NBSP).replace(".", ",")
    return txt


def _money_short(amount):
    """Vue d'ensemble : pas de millimes. 7 823,6 → « 7 824 DT » ; 1 234 567 → « 1,23 M DT »."""
    if abs(amount) >= 1_000_000:
        return f"{_num(amount / 1_000_000, 2)} M DT"
    return f"{_num(amount)} DT"


def _pl(n, one, many):
    """Accord en nombre : _pl(1, 'facture', 'factures') → « 1 facture »."""
    return f"{n} {one if abs(n) < 2 else many}"


STAGE_SHORT = {"recu": "Reçue", "prepare": "Prête", "en_route": "En route", "livre": "Livrée"}


def _fr(date):
    return date.strftime("%d/%m/%Y") if date else ""


def _act(name, model, domain, views=("list", "form"), context=None):
    return {
        "type": "ir.actions.act_window", "name": name, "res_model": model, "domain": domain,
        "views": [[False, v] for v in views], "context": context or {}, "target": "current",
    }


def _rec(model, res_id):
    return {"type": "ir.actions.act_window", "res_model": model, "res_id": res_id,
            "views": [[False, "form"]], "target": "current"}


class QafilaDashboard(models.AbstractModel):
    _name = "qafila.dashboard"
    _description = "Tableau de bord Qafila"

    @api.model
    def get_data(self):
        if not self.env.user._is_internal():
            raise AccessError("Le tableau d'exploitation est réservé à l'équipe Qafila.")
        env = self.env(su=True)  # chiffres agrégés, identiques pour toute l'équipe interne
        today = fields.Date.context_today(self)
        now_local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        soon = today + timedelta(days=30)
        attention = []

        # ---------------------------------------------------------- expéditions
        Picking = env["stock.picking"]
        out = [("picking_type_code", "=", "outgoing"), ("state", "not in", ("cancel", "draft"))]
        open_out = out + [("state", "!=", "done")]
        counts = {k: Picking.search_count(open_out + [("qafila_stage", "=", k)]) for k in ("recu", "prepare", "en_route")}
        open_total = sum(counts.values())
        delivered_dom = out + [("state", "=", "done"), ("date_done", ">=", fields.Datetime.now() - timedelta(days=30))]
        delivered_30 = Picking.search_count(delivered_dom)
        stage_labels = dict(Picking._fields["qafila_stage"].selection)
        open_pickings = Picking.search(open_out, order="scheduled_date asc")
        shipments = [{
            "id": p.id, "name": p.name,
            "client": p.partner_id.commercial_partner_id.name or "",
            "city": p.partner_id.city or "",
            "stage": p.qafila_stage, "stage_label": STAGE_SHORT.get(p.qafila_stage, ""),
            "stage_title": stage_labels.get(p.qafila_stage, ""),
            "vehicle": p.qafila_vehicle_id.license_plate or "",
            "date": _fr(p.scheduled_date),
            "late": bool(p.scheduled_date and p.scheduled_date.date() < today),
        } for p in open_pickings[:8]]
        no_truck = open_pickings.filtered(lambda p: p.qafila_stage == "prepare" and not p.qafila_vehicle_id)
        if no_truck:
            attention.append({"level": "warning", "text": f"{_pl(len(no_truck), 'expédition prête', 'expéditions prêtes')} sans camion affecté",
                              "detail": ", ".join(no_truck[:3].mapped("name")),
                              "action": _act("Expéditions prêtes sans camion", "stock.picking", [("id", "in", no_truck.ids)])})
        late_ship = open_pickings.filtered(lambda p: p.scheduled_date and p.scheduled_date.date() < today)
        if late_ship:
            attention.append({"level": "critical", "text": f"{_pl(len(late_ship), 'expédition', 'expéditions')} en retard sur la date prévue",
                              "detail": ", ".join(late_ship[:3].mapped("name")),
                              "action": _act("Expéditions en retard", "stock.picking", [("id", "in", late_ship.ids)])})

        # ---------------------------------------------------------- flotte & maintenance
        vehicles = env["fleet.vehicle"].search([])
        status_labels = dict(QAFILA_STATUS)
        fleet = [{"code": code, "label": label,
                  "count": len(vehicles.filtered(lambda v, c=code: v.qafila_status == c))} for code, label in QAFILA_STATUS]
        total = len(vehicles) or 1
        for seg in fleet:
            seg["pct"] = round(100 * seg["count"] / total, 1)
        available = next(s["count"] for s in fleet if s["code"] == "disponible")
        Request = env["maintenance.request"]
        open_req_dom = [("stage_id.done", "=", False), ("archive", "=", False)]
        open_requests = Request.search(open_req_dom, order="priority desc, schedule_date asc")

        fleet_exceptions = []
        for v in vehicles.filtered(lambda v: v.qafila_status != "disponible").sorted("qafila_status", reverse=True):
            if v.qafila_status == "en_tournee":
                ref = v.qafila_picking_ids.filtered(lambda p: p.qafila_stage == "en_route" and p.state not in ("done", "cancel"))[:1]
                reason = f"{ref.name} → {ref.partner_id.city or ref.partner_id.name}" if ref else "En tournée"
            elif v.qafila_status == "maintenance":
                req = open_requests.filtered(lambda r, v=v: r.equipment_id.qafila_vehicle_id == v)[:1]
                reason = req.name.split(" (")[0] if req else "Intervention en cours"
            else:
                reason = "Hors service"
            fleet_exceptions.append({"id": v.id, "plate": v.license_plate, "status": v.qafila_status,
                                     "status_label": status_labels[v.qafila_status],
                                     "model": v.model_id.name or "", "reason": reason})

        for v in vehicles.filtered(lambda v: v.qafila_inspection_date and v.qafila_inspection_date < today):
            attention.append({"level": "critical", "text": f"Visite technique dépassée : {v.license_plate}",
                              "detail": f"échue le {_fr(v.qafila_inspection_date)} · {status_labels[v.qafila_status]}",
                              "action": _rec("fleet.vehicle", v.id)})
        for r in open_requests.filtered(lambda r: r.priority == "3"):
            attention.append({"level": "warning", "text": f"Intervention prioritaire : {r.name.split(' (')[0]}",
                              "detail": f"{r.equipment_id.qafila_plate or r.equipment_id.name} · {r.stage_id.name}",
                              "action": _rec("maintenance.request", r.id)})

        deadlines = []
        for v in vehicles.filtered(lambda v: v.qafila_inspection_date and today <= v.qafila_inspection_date <= soon):
            deadlines.append({"sort": str(v.qafila_inspection_date), "date": _fr(v.qafila_inspection_date),
                              "what": "Visite technique", "who": v.license_plate, "id": v.id})
        for c in env["fleet.vehicle.log.contract"].search([("state", "=", "open"), ("expiration_date", ">=", today),
                                                         ("expiration_date", "<=", soon)]):
            deadlines.append({"sort": str(c.expiration_date), "date": _fr(c.expiration_date),
                              "what": c.cost_subtype_id.name or "Contrat", "who": c.vehicle_id.license_plate, "id": c.vehicle_id.id})
        deadlines.sort(key=lambda d: d["sort"])

        priority_labels = {"0": "Basse", "1": "Basse", "2": "Normale", "3": "Haute"}
        requests = [{
            "id": r.id, "name": r.name.split(" (")[0],
            "asset": r.equipment_id.qafila_plate or r.equipment_id.name or "",
            "type": "Préventive" if r.maintenance_type == "preventive" else "Corrective",
            "stage": r.stage_id.name, "in_progress": r.stage_id == env.ref("maintenance.stage_1", raise_if_not_found=False),
            "priority": priority_labels.get(r.priority or "0", "Basse"), "high": r.priority == "3",
            "date": _fr(r.schedule_date),
        } for r in open_requests[:6]]

        # ---------------------------------------------------------- finances
        Move = env["account.move"]
        posted = [("move_type", "=", "out_invoice"), ("state", "=", "posted")]
        month_dom = posted + [("invoice_date", ">=", month_start)]
        ca_month = sum(Move.search(month_dom).mapped("amount_untaxed_signed"))
        ca_prev = sum(Move.search(posted + [("invoice_date", ">=", prev_month_start),
                                            ("invoice_date", "<=", prev_month_end)]).mapped("amount_untaxed_signed"))
        due_dom = posted + [("payment_state", "in", ("not_paid", "partial"))]
        due_moves = Move.search(due_dom)
        overdue = due_moves.filtered(lambda m: m.invoice_date_due and m.invoice_date_due < today)
        if overdue:
            attention.append({"level": "critical", "text": _pl(len(overdue), "facture échue non réglée", "factures échues non réglées"),
                              "detail": _money_short(sum(overdue.mapped("amount_residual_signed"))),
                              "action": _act("Factures échues", "account.move", [("id", "in", overdue.ids)])})
        if ca_prev:
            delta = 100 * (ca_month - ca_prev) / ca_prev
            ca_context = f"{'+' if delta >= 0 else '−'}{_num(abs(delta), 1)} % vs {MONTHS_FR[prev_month_start.month - 1]}"
        else:
            ca_context = f"{MONTHS_FR[prev_month_start.month - 1]} : aucune facture"

        by_client = {}
        for move in Move.search(posted + [("invoice_date", ">=", today.replace(month=1, day=1))]):
            partner = move.partner_id.commercial_partner_id
            by_client.setdefault(partner.id, [partner.name, 0.0])[1] += move.amount_untaxed_signed
        clients = sorted(by_client.items(), key=lambda kv: kv[1][1], reverse=True)
        year_total = sum(v[1] for _k, v in clients) or 1.0
        top_value = clients[0][1][1] if clients else 1.0
        revenue = [{"id": pid, "name": name, "label": _money_short(amount),
                    "share": f"{_num(100 * amount / year_total)} %",
                    "pct": round(100 * amount / top_value, 1)} for pid, (name, amount) in clients[:6]]
        revenue_headline = (f"{clients[0][1][0]} représente {_num(100 * clients[0][1][1] / year_total)} % "
                            f"du chiffre d'affaires {today.year}") if clients else ""

        # ---------------------------------------------------------- commercial & stock
        Lead = env["crm.lead"]
        site = env.ref("qafila_api.utm_source_site", raise_if_not_found=False)
        lead_dom = [("active", "=", True), ("won_status", "=", "pending")] if "won_status" in Lead._fields \
            else [("active", "=", True)]
        site_leads = Lead.search(lead_dom + [("source_id", "=", site.id)]) if site else Lead
        if site_leads:
            attention.append({"level": "info", "text": f"{_pl(len(site_leads), 'demande de devis reçue', 'demandes de devis reçues')} via qafila.tn",
                              "detail": ", ".join(site_leads[:2].mapped("partner_name") or site_leads[:2].mapped("name")),
                              "action": _act("Demandes de devis du site", "crm.lead", [("id", "in", site_leads.ids)],
                                             views=("list", "form", "kanban"))})
        pallet = env["product.product"].search([("default_code", "=", "QF-PAL")], limit=1)
        stock = [{"name": wh.name.replace("Qafila ", ""),
                  "pallets": _num(pallet.with_context(warehouse_id=wh.id).qty_available if pallet else 0)}
                 for wh in env["stock.warehouse"].search([])]

        order = {"critical": 0, "warning": 1, "info": 2}
        attention.sort(key=lambda a: order[a["level"]])
        return {
            "date_label": f"{DAYS_FR[today.weekday()].capitalize()} {today.day} {MONTHS_FR[today.month - 1]} {today.year}",
            "updated": now_local.strftime("%H:%M"),
            "attention": attention,
            "band": {
                "shipments": {"value": open_total,
                              "en_route": _pl(counts["en_route"], "en route", "en route"),
                              "prepare": _pl(counts["prepare"], "prête au départ", "prêtes au départ"),
                              "recu": _pl(counts["recu"], "à préparer", "à préparer"),
                              "delivered_30": _pl(delivered_30, "livrée sur les 30 derniers jours", "livrées sur les 30 derniers jours")},
                "ca": {"value": _money_short(ca_month), "context": ca_context,
                       "label": f"CA facturé HT · {MONTHS_FR[today.month - 1]}"},
                "due": {"value": _money_short(sum(due_moves.mapped("amount_residual_signed"))),
                        "context": _pl(len(overdue), "facture échue", "factures échues") if overdue
                        else f"{_pl(len(due_moves), 'facture', 'factures')}, aucune échue",
                        "alert": bool(overdue)},
                "fleet": {"value": f"{available}/{len(vehicles)}", "context": f"{_num(100 * available / total)} % de la flotte disponible"},
            },
            "shipments": shipments, "shipments_more": max(0, len(open_pickings) - len(shipments)),
            "fleet": fleet, "fleet_total": len(vehicles), "fleet_exceptions": fleet_exceptions,
            "deadlines": deadlines[:4],
            "requests": requests, "requests_open": len(open_requests),
            "revenue": revenue, "revenue_headline": revenue_headline, "revenue_year": today.year,
            "stock": stock,
            "actions": {
                "shipments": _act("Expéditions en cours", "stock.picking", open_out),
                "en_route": _act("Expéditions en route", "stock.picking", open_out + [("qafila_stage", "=", "en_route")]),
                "prepare": _act("Expéditions prêtes", "stock.picking", open_out + [("qafila_stage", "=", "prepare")]),
                "recu": _act("Commandes à préparer", "stock.picking", open_out + [("qafila_stage", "=", "recu")]),
                "delivered": _act("Livrées (30 jours)", "stock.picking", delivered_dom),
                "ca": _act("Factures du mois", "account.move", month_dom),
                "due": _act("Factures à encaisser", "account.move", due_dom),
                "fleet": _act("Flotte", "fleet.vehicle", [], views=("list", "form", "kanban")),
                "requests": _act("Interventions ouvertes", "maintenance.request", open_req_dom, views=("list", "form", "kanban")),
                "stock": _act("Stock palettes EPAL", "stock.quant",
                              [("location_id.usage", "=", "internal"), ("product_id.default_code", "=", "QF-PAL")]),
            },
        }
