from num2words import num2words

from odoo import models

STAMP_CODE = "QF-TIMBRE"


def _fr_words(number):
    return num2words(int(number), lang="fr")


class AccountMove(models.Model):
    _inherit = "account.move"

    # ------------------------------------------------------------------ timbre fiscal
    def _qafila_stamp_tax(self):
        self.ensure_one()
        return self.env["account.chart.template"].with_company(self.company_id).ref(
            "l10n_tn_tax_vat_sale_tax_stamp", raise_if_not_found=False
        )

    def _qafila_add_stamp(self):
        """Ajoute la ligne « Droit de timbre » (1,000 DT, taxe fixe l10n_tn) aux factures clients tunisiennes."""
        product = self.env.ref("qafila_facture.product_timbre_fiscal", raise_if_not_found=False)
        if not product:
            return
        for move in self:
            if (move.move_type != "out_invoice" or move.state != "draft"
                    or move.company_id.account_fiscal_country_id.code != "TN"
                    or move.invoice_line_ids.filtered(lambda l: l.product_id == product)):
                continue
            tax = move._qafila_stamp_tax()
            if not tax:
                continue
            move.write({"invoice_line_ids": [(0, 0, {
                "product_id": product.id,
                "name": "Droit de timbre",
                "quantity": 1,
                "price_unit": 0.0,
                "tax_ids": [(6, 0, tax.ids)],
                "sequence": 9999,
            })]})

    def _post(self, soft=True):
        self._qafila_add_stamp()
        return super()._post(soft=soft)

    # ------------------------------------------------------------------ aides pour le rapport PDF
    def _qafila_is_stamp_line(self, line):
        return line.product_id.default_code == STAMP_CODE

    def _qafila_report_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda l: not self._qafila_is_stamp_line(l)).sorted("sequence")

    def _qafila_tax_summary(self):
        """[(libellé, base HT, montant)] pour la TVA, et le montant du timbre séparément."""
        self.ensure_one()
        sign = -1 if self.move_type in ("out_invoice", "in_refund") else 1
        vat, stamp = {}, 0.0
        for line in self.line_ids.filtered(lambda l: l.display_type == "tax" and l.tax_line_id):
            amount = sign * line.amount_currency
            if line.tax_line_id.amount_type == "fixed":
                stamp += amount
                continue
            key = line.tax_line_id.tax_group_id.name or line.tax_line_id.name
            base, tax = vat.get(key, (0.0, 0.0))
            vat[key] = (base + abs(line.tax_base_amount), tax + amount)
        return [(k, b, t) for k, (b, t) in vat.items()], stamp

    def _qafila_untaxed(self):
        self.ensure_one()
        return sum(self._qafila_report_lines().mapped("price_subtotal"))

    def _qafila_amount_in_words(self, amount=None):
        """Montant en toutes lettres : « Mille neuf cent vingt-sept dinars et huit cents millimes »."""
        self.ensure_one()
        amount = round(abs(self.amount_total if amount is None else amount), 3)
        dinars = int(amount)
        millimes = int(round((amount - dinars) * 1000))
        text = f"{_fr_words(dinars)} dinar{'s' if dinars > 1 else ''}"
        if millimes:
            text += f" et {_fr_words(millimes)} millime{'s' if millimes > 1 else ''}"
        return text[:1].upper() + text[1:]
