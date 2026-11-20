{
    "name": "Qafila — Facture professionnelle",
    "summary": "Mise en page Qafila des documents, facture conforme (mentions tunisiennes, timbre fiscal, montant en lettres)",
    "description": """
- Mise en page Qafila pour tous les documents PDF (devis, bons de livraison, factures) ;
- facture professionnelle : en-tête légal (MF, RC), client, détail HT/TVA, droit de timbre,
  total TTC, montant arrêté en toutes lettres (dinars et millimes), RIB, zone cachet et signature ;
- droit de timbre de 1,000 DT ajouté automatiquement à la validation des factures clients (l10n_tn).
    """,
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Qafila — Yassine Chelly & Karim Arouay",
    "website": "https://qafila.tn",
    "license": "LGPL-3",
    "depends": ["account", "l10n_tn", "qafila_branding"],
    "data": [
        "views/report_layout.xml",
        "data/product_data.xml",
        "views/report_invoice.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "qafila_facture/static/src/scss/report_qafila.scss",
        ],
    },
    "installable": True,
}
