from odoo import api, fields, models

QAFILA_STAGES = [
    ("recu", "Commande reçue"),
    ("prepare", "Préparée à l'entrepôt"),
    ("en_route", "En route"),
    ("livre", "Livrée"),
]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    qafila_stage = fields.Selection(
        QAFILA_STAGES,
        string="Étape de suivi",
        compute="_compute_qafila_stage",
        store=True,
        readonly=False,
        tracking=True,
        help="Étape affichée au client sur qafila.tn (suivi d'expédition).",
    )

    @api.depends("state")
    def _compute_qafila_stage(self):
        for picking in self:
            if picking.state == "done":
                picking.qafila_stage = "livre"
            elif picking.qafila_stage == "en_route":
                picking.qafila_stage = "en_route"  # posée à la main par l'équipe transport
            elif picking.state == "assigned":
                picking.qafila_stage = "prepare"
            else:
                picking.qafila_stage = "recu"

    def action_qafila_en_route(self):
        self.filtered(lambda p: p.state not in ("done", "cancel")).qafila_stage = "en_route"
