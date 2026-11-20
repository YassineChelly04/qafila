from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    qafila_vehicle_id = fields.Many2one(
        "fleet.vehicle", "Véhicule", tracking=True, index="btree_not_null",
        domain="[('qafila_status', 'in', ('disponible', 'en_tournee'))]",
        help="Camion affecté à l'expédition (seuls les véhicules disponibles ou déjà en tournée sont proposés).")
    qafila_driver_id = fields.Many2one("res.partner", "Chauffeur", related="qafila_vehicle_id.driver_id")

    def action_qafila_en_route(self):
        missing = self.filtered(lambda p: p.picking_type_code == "outgoing" and not p.qafila_vehicle_id)
        if missing:
            raise UserError(_("Affectez d'abord un véhicule à : %s", ", ".join(missing.mapped("name"))))
        return super().action_qafila_en_route()
