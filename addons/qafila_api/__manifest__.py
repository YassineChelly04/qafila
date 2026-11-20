{
    "name": "Qafila — API du site vitrine",
    "summary": "Demande de devis (piste CRM) et suivi d'expédition pour qafila.tn",
    "description": """
Points d'accès publics utilisés par la landing page statique (via Caddy) :
- POST /qafila/api/lead  : crée une piste CRM à partir du formulaire de devis ;
- GET  /qafila/api/track : renvoie l'étape d'une expédition (aucune donnée personnelle).
Ajoute l'étape de suivi Qafila sur les transferts sortants.
    """,
    "version": "19.0.1.0.0",
    "category": "Inventory/Delivery",
    "author": "Qafila — Arouay Karim & Chelly Yassine",
    "website": "https://qafila.tn",
    "license": "LGPL-3",
    "depends": ["crm", "stock", "utm"],
    "data": [
        "data/utm_data.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
}
