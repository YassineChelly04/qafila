{
    "name": "Qafila — Identité visuelle",
    "summary": "Thème Qafila pour Odoo : couleurs, polices, page de connexion, titre, favicon, documents",
    "description": """
Identité Qafila appliquée à Odoo 19 Community (voir docs/02-BRAND.md) :
- couleur principale Bleu Sidi Bou Saïd, barre de navigation Encre de Kairouan ;
- polices Familjen Grotesk (texte) et Funnel Display (titres), auto-hébergées ;
- page de connexion personnalisée, favicon et titre « Qafila » ;
- liens Odoo.com retirés du menu utilisateur ;
- (mise en page PDF : module qafila_facture).
    """,
    "version": "19.0.1.0.0",
    "category": "Theme/Backend",
    "author": "Qafila — Arouay Karim & Chelly Yassine",
    "website": "https://qafila.tn",
    "license": "LGPL-3",
    "depends": ["web", "base_setup"],
    "data": [
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            ("before", "web/static/src/scss/primary_variables.scss",
             "qafila_branding/static/src/scss/primary_variables.scss"),
        ],
        "web.assets_backend": [
            "qafila_branding/static/src/scss/fonts.scss",
            "qafila_branding/static/src/scss/backend.scss",
            "qafila_branding/static/src/js/branding.js",
        ],
        "web.assets_frontend": [
            "qafila_branding/static/src/scss/fonts.scss",
            "qafila_branding/static/src/scss/login.scss",
        ],
    },
    "installable": True,
    "application": False,
}
