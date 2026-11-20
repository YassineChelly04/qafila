from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    qafila_vehicle_id = fields.Many2one("fleet.vehicle", "Véhicule", index="btree_not_null", ondelete="set null")
    qafila_plate = fields.Char("Immatriculation", related="qafila_vehicle_id.license_plate")


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    qafila_vehicle_id = fields.Many2one("fleet.vehicle", "Véhicule", related="equipment_id.qafila_vehicle_id", store=True)
