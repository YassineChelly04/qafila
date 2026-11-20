from odoo import api, fields, models

QAFILA_STATUS = [
    ("disponible", "Disponible"),
    ("en_tournee", "En tournée"),
    ("maintenance", "En maintenance"),
    ("immobilise", "Immobilisé"),
]


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    qafila_payload = fields.Float("Charge utile (t)")
    qafila_pallets = fields.Integer("Capacité (palettes)")
    qafila_reefer = fields.Boolean("Frigorifique")
    qafila_warehouse_id = fields.Many2one("stock.warehouse", "Base d'exploitation")
    qafila_inspection_date = fields.Date("Prochaine visite technique", tracking=True)
    qafila_immobilised = fields.Boolean("Immobilisé", tracking=True,
                                        help="Hors service (sinistre, saisie, attente de pièces…)")
    qafila_equipment_ids = fields.One2many("maintenance.equipment", "qafila_vehicle_id", "Équipement maintenance")
    qafila_picking_ids = fields.One2many("stock.picking", "qafila_vehicle_id", "Expéditions")
    qafila_status = fields.Selection(QAFILA_STATUS, "Statut d'exploitation", compute="_compute_qafila_status",
                                     store=True, tracking=True)
    qafila_open_request_count = fields.Integer("Interventions ouvertes", compute="_compute_qafila_requests")

    @api.depends("qafila_immobilised", "qafila_picking_ids.qafila_stage", "qafila_picking_ids.state",
                 "qafila_equipment_ids.maintenance_ids.stage_id", "qafila_equipment_ids.maintenance_ids.archive")
    def _compute_qafila_status(self):
        in_progress = self.env.ref("maintenance.stage_1", raise_if_not_found=False)
        for vehicle in self:
            requests = vehicle.qafila_equipment_ids.maintenance_ids.filtered(lambda r: not r.archive)
            on_road = vehicle.qafila_picking_ids.filtered(
                lambda p: p.qafila_stage == "en_route" and p.state not in ("done", "cancel"))
            if vehicle.qafila_immobilised:
                vehicle.qafila_status = "immobilise"
            elif in_progress and requests.filtered(lambda r: r.stage_id == in_progress):
                vehicle.qafila_status = "maintenance"
            elif on_road:
                vehicle.qafila_status = "en_tournee"
            else:
                vehicle.qafila_status = "disponible"

    def _compute_qafila_requests(self):
        for vehicle in self:
            vehicle.qafila_open_request_count = len(vehicle.qafila_equipment_ids.maintenance_ids.filtered(
                lambda r: not r.archive and not r.stage_id.done))

    # ------------------------------------------------------------------ lien flotte ↔ maintenance
    def _qafila_ensure_equipment(self):
        category = self.env["maintenance.equipment.category"].search([("name", "=", "Camions et porteurs")], limit=1) \
            or self.env["maintenance.equipment.category"].create({"name": "Camions et porteurs"})
        for vehicle in self.filtered(lambda v: not v.qafila_equipment_ids):
            self.env["maintenance.equipment"].create({
                "name": f"{vehicle.model_id.brand_id.name or ''} {vehicle.model_id.name or ''} — {vehicle.license_plate or ''}".strip(),
                "category_id": category.id,
                "model": vehicle.model_id.name,
                "serial_no": vehicle.vin_sn or vehicle.license_plate,
                "qafila_vehicle_id": vehicle.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        vehicles = super().create(vals_list)
        vehicles._qafila_ensure_equipment()
        return vehicles

    def action_qafila_breakdown(self):
        """Déclarer une panne : crée une intervention corrective « en cours » sur le camion."""
        self.ensure_one()
        self._qafila_ensure_equipment()
        request = self.env["maintenance.request"].create({
            "name": f"Panne — {self.license_plate}",
            "equipment_id": self.qafila_equipment_ids[:1].id,
            "maintenance_type": "corrective",
            "priority": "3",
            "stage_id": self.env.ref("maintenance.stage_1").id,
            "schedule_date": fields.Datetime.now(),
        })
        return {
            "type": "ir.actions.act_window", "res_model": "maintenance.request", "res_id": request.id,
            "view_mode": "form", "views": [[False, "form"]], "target": "current",
        }

    def action_qafila_open_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "name": f"Maintenance — {self.license_plate}",
            "res_model": "maintenance.request", "view_mode": "list,form,kanban",
            "views": [[False, "list"], [False, "form"], [False, "kanban"]],
            "domain": [("equipment_id", "in", self.qafila_equipment_ids.ids)],
            "context": {"default_equipment_id": self.qafila_equipment_ids[:1].id},
        }
