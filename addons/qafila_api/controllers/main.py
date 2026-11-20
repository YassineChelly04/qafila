"""API publique du site qafila.tn.

Règles (docs/04-ODOO-DATA.md) : validation stricte, limites de longueur,
limitation de débit par IP, et le suivi ne renvoie jamais de nom, d'adresse ni de prix.
"""
import json
import re
import threading
import time
from collections import defaultdict, deque

from odoo import http
from odoo.http import request

_LOCK = threading.Lock()
_HITS = defaultdict(deque)
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[a-zA-Z]{2,24}$")
REF_RE = re.compile(r"^[A-Z]{2,5}/[A-Z]{2,5}/\d{1,6}$")
SERVICES = {
    "transport": "Transport routier",
    "entreposage": "Entreposage",
    "express": "Livraison express",
    "douane": "Dédouanement",
    "autre": "Autre besoin",
}


def _throttled(bucket, limit, window=60):
    ip = request.httprequest.remote_addr or "?"
    now = time.monotonic()
    with _LOCK:
        hits = _HITS[(bucket, ip)]
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            return True
        hits.append(now)
    return False


def _error(message, status=400):
    return request.make_json_response({"ok": False, "error": message}, status=status)


def _clean(value, max_len):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:max_len]


class QafilaApi(http.Controller):

    @http.route("/qafila/api/lead", type="http", auth="public", methods=["POST"], csrf=False, save_session=False)
    def create_lead(self, **_kw):
        if _throttled("lead", limit=5):
            return _error("Trop de demandes, réessayez dans une minute.", 429)
        try:
            data = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except ValueError:
            return _error("Requête invalide.")
        if not isinstance(data, dict):
            return _error("Requête invalide.")
        if data.get("site"):  # champ piège anti-robot, invisible pour les humains
            return request.make_json_response({"ok": True})

        name = _clean(data.get("nom"), 120)
        company = _clean(data.get("societe"), 160)
        email = _clean(data.get("email"), 254).lower()
        phone = _clean(data.get("telephone"), 32)
        service = data.get("service") if data.get("service") in SERVICES else "autre"
        origin = _clean(data.get("depart"), 80)
        destination = _clean(data.get("arrivee"), 80)
        message = str(data.get("message") or "").strip()[:2000]

        if len(name) < 2:
            return _error("Merci d'indiquer votre nom.")
        if not EMAIL_RE.match(email):
            return _error("Adresse e-mail invalide.")
        if phone and not re.fullmatch(r"[+0-9 ().-]{6,32}", phone):
            return _error("Numéro de téléphone invalide.")

        env = request.env(su=True)
        route = f"{origin} → {destination}" if origin or destination else ""
        description = "\n".join(filter(None, [
            f"Service : {SERVICES[service]}",
            f"Trajet : {route}" if route else "",
            "",
            message,
        ]))
        lead = env["crm.lead"].create({
            "name": f"Devis {SERVICES[service]} — {company or name}",
            "contact_name": name,
            "partner_name": company,
            "email_from": email,
            "phone": phone,
            "description": description.replace("\n", "<br/>"),
            "source_id": env.ref("qafila_api.utm_source_site", raise_if_not_found=False).id or False,
            "medium_id": env.ref("utm.utm_medium_website", raise_if_not_found=False).id or False,
        })
        return request.make_json_response({"ok": True, "reference": f"QF-L{lead.id:05d}"})

    @http.route("/qafila/api/track", type="http", auth="public", methods=["GET"], save_session=False)
    def track(self, ref=None, **_kw):
        if _throttled("track", limit=30):
            return _error("Trop de recherches, réessayez dans une minute.", 429)
        ref = _clean(ref, 32).upper()
        if not REF_RE.match(ref):
            return _error("Format attendu : QRD/OUT/00012")
        picking = request.env["stock.picking"].sudo().search(
            [("name", "=", ref), ("picking_type_code", "=", "outgoing"), ("state", "!=", "cancel")], limit=1
        )
        if not picking:
            return _error("Aucune expédition ne correspond à cette référence.", 404)

        stages = dict(picking._fields["qafila_stage"].selection)
        order = [key for key, _label in picking._fields["qafila_stage"].selection]
        current = picking.qafila_stage or "recu"
        warehouse = picking.picking_type_id.warehouse_id
        when = picking.date_done or picking.scheduled_date
        return request.make_json_response({
            "ok": True,
            "reference": picking.name,
            "etape": current,
            "libelle": stages[current],
            "etapes": [{"code": k, "libelle": stages[k], "fait": order.index(k) <= order.index(current)} for k in order],
            "depart": warehouse.partner_id.city or warehouse.name,
            "destination": picking.partner_id.commercial_partner_id.city or "",
            "date": when and when.strftime("%d/%m/%Y") or "",
            "date_label": "Livrée le" if current == "livre" else "Livraison prévue le",
            # immatriculation du camion (module qafila_ops) — jamais le nom du chauffeur
            "vehicule": picking.qafila_vehicle_id.license_plate if "qafila_vehicle_id" in picking._fields
                        and picking.qafila_vehicle_id else "",
        })
