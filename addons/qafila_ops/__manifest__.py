{
    "name": "Qafila — Exploitation (tableau de bord, flotte, maintenance)",
    "summary": "Tableau de bord d'accueil, état de la flotte, maintenance des camions et affectation des véhicules aux expéditions",
    "description": """
Exploitation logistique Qafila :
- tableau de bord Qafila (première vue à la connexion) : chiffre d'affaires, encours, expéditions,
  état de la flotte, maintenance, échéances, stock palettes, pistes CRM ;
- flotte (module Flotte) : charge utile, capacité palettes, frigorifique, base, visite technique,
  statut d'exploitation calculé (Disponible / En tournée / En maintenance / Immobilisé) ;
- maintenance (module Maintenance) : chaque camion est un équipement, déclaration de panne en un clic ;
- expéditions : véhicule et chauffeur affectés, statut du camion mis à jour automatiquement.
    """,
    "version": "19.0.1.0.0",
    "category": "Inventory/Delivery",
    "author": "Qafila — Yassine Chelly & Karim Arouay",
    "website": "https://qafila.tn",
    "license": "LGPL-3",
    "depends": ["sale_management", "stock", "account", "crm", "fleet", "maintenance", "qafila_api"],
    "data": [
        "views/fleet_vehicle_views.xml",
        "views/maintenance_views.xml",
        "views/stock_picking_views.xml",
        "views/dashboard_action.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "qafila_ops/static/src/dashboard/dashboard.js",
            "qafila_ops/static/src/dashboard/dashboard.xml",
            "qafila_ops/static/src/dashboard/dashboard.scss",
        ],
    },
    "installable": True,
    "application": True,
}
