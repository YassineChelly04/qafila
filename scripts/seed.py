# Qafila — données de démonstration (exécuté dans `odoo shell`, voir install.sh)
# IDEMPOTENT : chaque enregistrement est recherché avant création (docs/05-AGENT-RULES.md).
# Les marqueurs __XXX__ sont remplacés par install.sh (secrets lus dans .env, images en base64).
import base64
import json
from datetime import timedelta

from odoo import fields

ASSETS = json.loads(base64.b64decode("__ASSETS_JSON_B64__"))  # {clé: base64 png}
ADMIN_PASSWORD = "__ODOO_ADMIN_PASSWORD__"
ADMIN_EMAIL = "__ODOO_ADMIN_EMAIL__"
USER_PASSWORD = "__ODOO_DEMO_USER_PASSWORD__"
ERP_URL = "https://__QAFILA_ERP_DOMAIN__"
DEMO_NOTE = "Relation commerciale fictive — démonstration académique (projet CNIS SI-ERP 2026-2027)."


def log(msg):
    print(f"[seed] {msg}")


def upsert(model, domain, values):
    rec = env[model].with_context(active_test=False).search(domain, limit=1)
    if rec:
        rec.write(values)
    else:
        rec = env[model].create(values)
    return rec


# ------------------------------------------------------------------ société
tn = env.ref("base.tn")
tnd = env.ref("base.TND")
tnd.active = True
company = env.company
company.write({
    "name": "Qafila Logistique",
    "currency_id": tnd.id,
    "country_id": tn.id,
    "street": "Zone Industrielle de Radès",
    "street2": "Rue de l'Énergie",
    "zip": "2040",
    "city": "Radès",
    "phone": "+216 71 000 000",
    "email": "contact@qafila.tn",
    "website": "https://qafila.tn",
    "logo": ASSETS["logo"],
    "primary_color": "#1F5FAD",
    "secondary_color": "#C27C2C",
    "report_header": "La route est tracée.",
    "report_footer": "Qafila Logistique SARL · Z.I. Radès 2040, Ben Arous · +216 71 000 000 · contact@qafila.tn · qafila.tn",
})
# Mentions légales (fictives) exigées sur une facture tunisienne : MF, RC, capital, RIB
company.write({
    "vat": "1789456/A/M/000",
    "company_registry": "B01234562026",
    "report_header": "La route est tracée.",
    "report_footer": "Qafila Logistique SARL au capital de 100 000 DT · MF 1789456/A/M/000 · RC B01234562026 · "
                     "BIAT, agence Radès · RIB 08 006 0001234567890 12 · Z.I. Radès 2040 Ben Arous · contact@qafila.tn · qafila.tn",
})
layout = env.ref("qafila_facture.external_layout_qafila", raise_if_not_found=False) \
    or env.ref("web.external_layout_boxed", raise_if_not_found=False)
if layout:
    company.external_report_layout_id = layout
bank = upsert("res.bank", [("name", "=", "BIAT")], {"name": "BIAT", "bic": "BIATTNTT", "country": tn.id})
if not env["res.partner.bank"].search([("acc_number", "=", "08 006 0001234567890 12")], limit=1):
    env["res.partner.bank"].create({  # « compte de confiance » modifiable seulement à la création
        "acc_number": "08 006 0001234567890 12", "bank_id": bank.id, "partner_id": company.partner_id.id,
        "allow_out_payment": True,
    })
company.partner_id.write({"lang": "fr_FR", "image_1920": ASSETS["symbol"]})
company.account_fiscal_country_id = tn
if company.chart_template != "tn":
    env["account.chart.template"].try_loading("tn", company, install_demo=False)
    log("plan comptable tunisien chargé")

# Toutes les listes de prix en dinar ; les autres devises désactivées
for pricelist in env["product.pricelist"].with_context(active_test=False).search([]):
    pricelist.currency_id = tnd
env["res.currency"].search([("id", "!=", tnd.id)]).write({"active": False})
upsert("product.pricelist", [("name", "=", "Tarif public Qafila (TND)")],
       {"name": "Tarif public Qafila (TND)", "currency_id": tnd.id, "company_id": company.id})

params = env["ir.config_parameter"].sudo()
params.set_param("web.base.url", ERP_URL)
params.set_param("web.base.url.freeze", "True")
params.set_param("report.url", "http://127.0.0.1:8069")  # wkhtmltopdf lit les CSS en local, pas via le domaine
params.set_param("auth_signup.invitation_scope", "b2b")  # pas d'inscription libre sur l'ERP
params.set_param("auth_signup.reset_password", "True")
# Pièces jointes en base : la réplication PostgreSQL couvre aussi les fichiers (HA, docs/03)
if params.get_param("ir_attachment.location") != "db":
    params.set_param("ir_attachment.location", "db")
    env["ir.attachment"].force_storage()
    log("pièces jointes déplacées en base de données")

# ------------------------------------------------------------------ entrepôts
wh_rades = env["stock.warehouse"].search([("company_id", "=", company.id)], order="id", limit=1)
wh_rades.write({"name": "Qafila Radès", "code": "QRD", "partner_id": company.partner_id.id})
sfax_partner = upsert("res.partner", [("name", "=", "Qafila — Entrepôt de Sfax")], {
    "name": "Qafila — Entrepôt de Sfax", "parent_id": company.partner_id.id, "type": "other",
    "street": "Route de Gabès Km 4", "zip": "3003", "city": "Sfax", "country_id": tn.id,
})
wh_sfax = env["stock.warehouse"].search([("code", "=", "QSF")], limit=1) or env["stock.warehouse"].create(
    {"name": "Qafila Sfax", "code": "QSF", "company_id": company.id, "partner_id": sfax_partner.id})

for xmlid, label in (("stock.stock_location_customers", "Clients"), ("stock.stock_location_suppliers", "Fournisseurs")):
    loc = env.ref(xmlid, raise_if_not_found=False)
    if loc:
        loc.name = label

# ------------------------------------------------------------------ 5 clients (sociétés tunisiennes réelles)
tag = upsert("res.partner.category", [("name", "=", "Client grand compte")], {"name": "Client grand compte", "color": 4})
CLIENTS = [
    ("Poulina Group Holding", "poulina-group-holding", "GP1 Km 12", "2034", "Ezzahra", "+216 71 454 545",
     "https://www.poulinagroupholding.com", "Agro-industrie, aviculture, emballage"),
    ("CHO Company (Terra Delyssa)", "cho-terra-delyssa", "Route de Mahdia Km 18", "3066", "Essaadi, Sfax", "+216 74 447 677",
     "https://terradelyssa.com", "Huile d'olive — export"),
    ("SOTUVER — Société Tunisienne de Verreries", "sotuver", "Zone Industrielle Djebel Oust", "1111", "Bir Mcherga, Zaghouan", False,
     "https://www.sotuver.com.tn", "Verre d'emballage"),
    ("Carthage Cement", "carthage-cement", "Rue 8002, Espace Tunis, Bloc H, 3e étage, Montplaisir", "1073", "Tunis", "+216 71 964 593",
     "https://www.carthagecement.com.tn", "Ciment et matériaux de construction"),
    ("SOTIPAPIER", "sotipapier", "13, rue Ibn Abi Dhiaf, Z.I. Saint Gobain, Mégrine Riadh", "2014", "Ben Arous", "+216 71 434 957",
     "https://sotipapier.com", "Papier kraft et carton"),
]
clients = {}
for name, key, street, zipcode, city, phone, website, sector in CLIENTS:
    clients[key] = upsert("res.partner", [("ref", "=", f"QF-C-{key}")], {
        "name": name, "ref": f"QF-C-{key}", "is_company": True, "customer_rank": 1,
        "street": street, "zip": zipcode, "city": city, "country_id": tn.id,
        "phone": phone, "website": website, "lang": "fr_FR",
        "image_1920": ASSETS[f"client:{key}"], "category_id": [(6, 0, tag.ids)],
        "comment": f"<p>Secteur : {sector}</p><p>{DEMO_NOTE}</p>",
        "property_payment_term_id": (env.ref("account.account_payment_term_30days", raise_if_not_found=False) or env["account.payment.term"]).id,
    })
# Anciennes données Nexora / clients fictifs : archivés
env["res.partner"].search([("customer_rank", ">", 0), ("ref", "not like", "QF-C-%"), ("is_company", "=", True),
                           ("id", "!=", company.partner_id.id)]).write({"active": False})
log(f"{len(clients)} clients prêts")

# ------------------------------------------------------------------ équipe : 1 administrateur + 1 utilisateur
admin = env.ref("base.user_admin")
# Équipe projet : Yassine Chelly (administrateur ERP) et Karim Arouay (l'utilisateur métier demandé)
admin.write({"password": ADMIN_PASSWORD, "login": ADMIN_EMAIL, "email": ADMIN_EMAIL, "lang": "fr_FR",
             "tz": "Africa/Tunis", "name": "Yassine Chelly", "image_1920": ASSETS["avatar:yassine-chelly"]})
admin.partner_id.write({"function": "Administrateur ERP", "phone": "+216 71 000 011"})
groups = env["res.groups"]
for xmlid in ("base.group_user", "sales_team.group_sale_salesman_all_leads", "stock.group_stock_user",
              "purchase.group_purchase_user", "account.group_account_invoice",
              "fleet.fleet_group_user", "maintenance.group_equipment_manager"):
    group = env.ref(xmlid, raise_if_not_found=False)
    if group:
        groups |= group
user = env["res.users"].with_context(active_test=False).search(
    [("login", "in", ["karim.arouay@qafila.tn", "amine.trabelsi@qafila.tn"])], order="login desc", limit=1)
user_vals = {
    "name": "Karim Arouay", "login": "karim.arouay@qafila.tn", "email": "karim.arouay@qafila.tn",
    "lang": "fr_FR", "tz": "Africa/Tunis", "image_1920": ASSETS["avatar:karim-arouay"],
    "group_ids": [(6, 0, groups.ids)], "active": True,
}
if user:
    user.write(user_vals)
else:
    user = env["res.users"].with_context(no_reset_password=True).create(user_vals)
user.password = USER_PASSWORD
user.partner_id.write({"function": "Responsable logistique", "phone": "+216 71 000 012"})
# Anciens utilisateurs de démonstration archivés : exactement 1 utilisateur métier
env["res.users"].search([("share", "=", False), ("id", "not in", [admin.id, user.id, env.ref("base.user_root").id])]).write({"active": False})
log("équipe prête : Yassine Chelly (admin), Karim Arouay (utilisateur)")

# ------------------------------------------------------------------ produits & services
price_precision = env.ref("product.decimal_price", raise_if_not_found=False)
if price_precision and price_precision.digits != 3:
    price_precision.digits = 3  # dinar tunisien : 3 décimales (millimes)
cat_services = upsert("product.category", [("name", "=", "Services logistiques")], {"name": "Services logistiques"})
cat_goods = upsert("product.category", [("name", "=", "Consommables d'emballage")], {"name": "Consommables d'emballage"})
uom_unit = env.ref("uom.product_uom_unit")
uom_hour = env.ref("uom.product_uom_hour", raise_if_not_found=False) or uom_unit
PRODUCTS = [
    # réf, nom, type, prix, coût, uom, description
    ("QF-TR-SOU", "Transport palette Tunis → Sousse", "service", 32.0, 0, uom_unit, "Enlèvement à Radès, livraison J+1 à Sousse. Prix par palette (≤ 800 kg)."),
    ("QF-TR-SFX", "Transport palette Tunis → Sfax", "service", 45.0, 0, uom_unit, "Groupage quotidien via le hub de Sfax. Prix par palette (≤ 800 kg)."),
    ("QF-TR-TOZ", "Transport palette Tunis → Tozeur", "service", 78.0, 0, uom_unit, "Ligne du Sud (Kairouan, Gafsa, Tozeur), 3 départs par semaine. Prix par palette."),
    ("QF-FTL-19", "Affrètement camion complet 19 t (journée)", "service", 950.0, 0, uom_unit, "Porteur 19 t avec chauffeur, 33 palettes, toute la Tunisie."),
    ("QF-EXP", "Livraison express Grand Tunis (colis ≤ 30 kg)", "service", 12.5, 0, uom_unit, "Livré dans les 24 h ouvrées dans le Grand Tunis, preuve de livraison signée."),
    ("QF-STK", "Entreposage palette / mois — Radès", "service", 28.0, 0, uom_unit, "Stockage ambiant sécurisé, inventaire tournant mensuel."),
    ("QF-FRD", "Entreposage froid 2–8 °C palette / mois", "service", 55.0, 0, uom_unit, "Chambre froide positive, relevés de température tracés."),
    ("QF-DOU", "Dédouanement import (par dossier)", "service", 180.0, 0, uom_unit, "Déclaration en douane, port de Radès ou aéroport Tunis-Carthage."),
    ("QF-MAN", "Manutention & préparation de commande (heure)", "service", 22.0, 0, uom_hour, "Préparation, étiquetage, filmage, chargement."),
    ("QF-PAL", "Palette Europe EPAL 1200×800", "goods", 38.0, 29.0, uom_unit, "Palette bois EPAL certifiée, charge dynamique 1 500 kg."),
    ("QF-CRT", "Cartons double cannelure 60×40×40 (lot de 25)", "goods", 42.5, 31.0, uom_unit, "Carton kraft brun double cannelure, résistance 20 kg."),
    ("QF-FLM", "Film étirable 500 mm × 300 m", "goods", 18.9, 12.4, uom_unit, "Film de palettisation 23 µm, rouleau manuel."),
]
products = {}
for ref, name, kind, price, cost, uom, desc in PRODUCTS:
    vals = {
        "name": name, "default_code": ref, "list_price": price, "standard_price": cost,
        "uom_id": uom.id, "description_sale": desc, "image_1920": ASSETS[f"product:{ref}"],
        "categ_id": (cat_services if kind == "service" else cat_goods).id,
        "sale_ok": True, "purchase_ok": kind == "goods",
        "type": "service" if kind == "service" else "consu",
    }
    if kind == "goods":
        vals["is_storable"] = True
    tmpl = upsert("product.template", [("default_code", "=", ref)], vals)
    products[ref] = tmpl.product_variant_id
log(f"{len(products)} produits/services prêts")

# ------------------------------------------------------------------ stock initial
STOCK = {("QF-PAL", wh_rades): 420, ("QF-CRT", wh_rades): 160, ("QF-FLM", wh_rades): 90,
         ("QF-PAL", wh_sfax): 180, ("QF-CRT", wh_sfax): 60, ("QF-FLM", wh_sfax): 40}
Quant = env["stock.quant"].with_context(inventory_mode=True)
for (ref, wh), qty in STOCK.items():
    loc = wh.lot_stock_id
    current = sum(Quant.search([("product_id", "=", products[ref].id), ("location_id", "=", loc.id)]).mapped("quantity"))
    if current < qty / 2:
        quant = Quant.search([("product_id", "=", products[ref].id), ("location_id", "=", loc.id)], limit=1) or \
            Quant.create({"product_id": products[ref].id, "location_id": loc.id})
        quant.inventory_quantity = qty
        quant.action_apply_inventory()
log("stock initial en place")

# ------------------------------------------------------------------ flotte (camions, chauffeurs) & maintenance
def brand(name):
    return env["fleet.vehicle.model.brand"].search([("name", "=ilike", name)], limit=1) \
        or env["fleet.vehicle.model.brand"].create({"name": name})

def category(name):
    return upsert("fleet.vehicle.model.category", [("name", "=", name)], {"name": name})

def vmodel(brand_name, name, cat):
    b = brand(brand_name)
    return upsert("fleet.vehicle.model", [("name", "=", name), ("brand_id", "=", b.id)],
                  {"name": name, "brand_id": b.id, "category_id": category(cat).id, "vehicle_type": "car",
                   "default_fuel_type": "diesel"})

def driver(name):
    return upsert("res.partner", [("name", "=", name), ("function", "=", "Chauffeur")], {
        "name": name, "function": "Chauffeur", "parent_id": False, "type": "contact", "country_id": tn.id,
        "comment": "Chauffeur fictif — données de démonstration.",
    })

d = fields.Date.today()
FLEET = [
    # plaque, marque, modèle, catégorie, chauffeur, base, charge t, palettes, frigo, km, visite technique, immobilisé
    ("214 TU 3871", "Renault Trucks", "D Wide 19 t", "Porteur poids lourd", "Hichem Gharbi", wh_rades, 10.5, 18, False, 184200, d + timedelta(days=12), False),
    ("219 TU 5520", "Renault Trucks", "D Wide 19 t", "Porteur poids lourd", "Mounir Jlassi", wh_rades, 10.5, 18, False, 142900, d + timedelta(days=140), False),
    ("205 TU 1194", "Mercedes-Benz", "Actros 1845 + semi frigorifique", "Ensemble articulé", "Slim Haddad", wh_rades, 25.0, 33, True, 412300, d + timedelta(days=75), False),
    ("226 TU 0457", "Iveco", "Eurocargo 120E", "Porteur moyen", "Walid Ben Amor", wh_sfax, 6.0, 12, False, 96400, d + timedelta(days=200), False),
    ("231 TU 7702", "Isuzu", "NPR frigorifique", "Porteur frigorifique", "Anis Mansouri", wh_rades, 3.5, 6, True, 118750, d + timedelta(days=55), False),
    ("233 TU 9015", "Iveco", "Daily 35S fourgon", "Utilitaire express", "Rami Khelifi", wh_rades, 1.2, 0, False, 64300, d + timedelta(days=240), False),
    ("234 TU 1288", "Iveco", "Daily 35S fourgon", "Utilitaire express", "Nour Ayari", wh_rades, 1.2, 0, False, 31800, d + timedelta(days=300), False),
    ("228 TU 6631", "Renault", "Master fourgon", "Utilitaire express", "Fares Trabelsi", wh_sfax, 1.4, 0, False, 158200, d - timedelta(days=9), True),
]
vehicles = {}
for plate, bname, mname, cat, dname, base, payload, pallets, reefer, km, insp, immob in FLEET:
    vals = {
        "license_plate": plate, "model_id": vmodel(bname, mname, cat).id, "driver_id": driver(dname).id,
        "qafila_warehouse_id": base.id, "qafila_payload": payload, "qafila_pallets": pallets, "qafila_reefer": reefer,
        "qafila_inspection_date": insp, "qafila_immobilised": immob, "location": base.name,
    }
    v = env["fleet.vehicle"].search([("license_plate", "=", plate)], limit=1)
    if v:
        v.write(vals)
    else:
        v = env["fleet.vehicle"].create(vals)
        v.odometer = km
    v._qafila_ensure_equipment()
    vehicles[plate] = v

insurance = upsert("fleet.service.type", [("name", "=", "Assurance flotte")], {"name": "Assurance flotte", "category": "contract"})
insurer = upsert("res.partner", [("name", "=", "Assureur flotte (démo)")], {"name": "Assureur flotte (démo)", "is_company": True})
for i, (plate, v) in enumerate(vehicles.items()):
    if not env["fleet.vehicle.log.contract"].search([("vehicle_id", "=", v.id)], limit=1):
        env["fleet.vehicle.log.contract"].create({
            "vehicle_id": v.id, "cost_subtype_id": insurance.id, "insurer_id": insurer.id, "amount": 2400.0 + 300 * i,
            "start_date": d - timedelta(days=345 - 40 * i), "expiration_date": d + timedelta(days=20 + 40 * i),
            "cost_frequency": "yearly", "state": "open",
        })

team = upsert("maintenance.team", [("name", "=", "Atelier Qafila — Radès")], {"name": "Atelier Qafila — Radès"})
def eq_cat(name):
    return upsert("maintenance.equipment.category", [("name", "=", name)], {"name": name})
EQUIPMENT = [
    ("Chariot élévateur électrique 1,5 t — Radès n°1", "Chariots élévateurs", "Toyota Traigo 48", "QRD-CE-01"),
    ("Chariot élévateur électrique 1,5 t — Radès n°2", "Chariots élévateurs", "Toyota Traigo 48", "QRD-CE-02"),
    ("Transpalette électrique — Sfax", "Chariots élévateurs", "Jungheinrich EJE", "QSF-TP-01"),
    ("Chambre froide positive CF-1 (2–8 °C) — Radès", "Froid (chambres et groupes)", "Panneaux 100 mm, groupe 12 kW", "QRD-CF-01"),
    ("Porte sectionnelle quai 3 — Radès", "Quais et portes", "Niveleur hydraulique", "QRD-Q3"),
]
equipment = {}
for name, cat, model, serial in EQUIPMENT:
    equipment[serial] = upsert("maintenance.equipment", [("serial_no", "=", serial)], {
        "name": name, "category_id": eq_cat(cat).id, "model": model, "serial_no": serial, "maintenance_team_id": team.id,
    })
for v in vehicles.values():
    v.qafila_equipment_ids.write({"maintenance_team_id": team.id})

stage_new = env.ref("maintenance.stage_0")
stage_progress = env.ref("maintenance.stage_1")
stage_done = env.ref("maintenance.stage_3")
now = fields.Datetime.now()
REQUESTS = [
    ("Groupe froid — perte de température (231 TU 7702)", vehicles["231 TU 7702"].qafila_equipment_ids[:1], "corrective", "3", stage_progress, 0, False),
    ("Vidange + filtres — 185 000 km (214 TU 3871)", vehicles["214 TU 3871"].qafila_equipment_ids[:1], "preventive", "2", stage_new, 5, True),
    ("Contrôle freins avant (205 TU 1194)", vehicles["205 TU 1194"].qafila_equipment_ids[:1], "corrective", "2", stage_new, 2, False),
    ("Carrosserie — sinistre arrière (228 TU 6631)", vehicles["228 TU 6631"].qafila_equipment_ids[:1], "corrective", "1", stage_new, 14, False),
    ("Révision annuelle chariot élévateur", equipment["QRD-CE-01"], "preventive", "1", stage_new, 10, True),
    ("Joint de porte chambre froide CF-1", equipment["QRD-CF-01"], "corrective", "2", stage_done, -6, False),
]
for name, eq, mtype, prio, stage, days, recurring in REQUESTS:
    vals = {"name": name, "equipment_id": eq.id, "maintenance_type": mtype, "priority": prio, "stage_id": stage.id,
            "maintenance_team_id": team.id, "schedule_date": now + timedelta(days=days), "user_id": user.id}
    if recurring:
        vals.update({"recurring_maintenance": True, "repeat_interval": 3, "repeat_unit": "month", "repeat_type": "forever"})
    if stage == stage_done:
        vals["close_date"] = fields.Date.today() + timedelta(days=days)
    upsert("maintenance.request", [("name", "=", name)], vals)
log(f"flotte : {len(vehicles)} véhicules, {len(REQUESTS)} interventions de maintenance")

# ------------------------------------------------------------------ commandes, livraisons, factures
today = fields.Datetime.now()
ORDERS = [
    # réf client, client, entrepôt, lignes, issue
    ("QF-DEMO-01", "cho-terra-delyssa", wh_sfax, [("QF-TR-SFX", 12), ("QF-PAL", 12), ("QF-FLM", 4)], "paid"),
    ("QF-DEMO-02", "poulina-group-holding", wh_rades, [("QF-FRD", 30), ("QF-MAN", 16), ("QF-PAL", 30)], "invoiced"),
    ("QF-DEMO-03", "carthage-cement", wh_rades, [("QF-FTL-19", 3), ("QF-PAL", 20)], "invoiced"),
    ("QF-DEMO-04", "sotuver", wh_rades, [("QF-TR-SOU", 18), ("QF-PAL", 18), ("QF-CRT", 10)], "en_route"),
    ("QF-DEMO-05", "sotipapier", wh_rades, [("QF-TR-TOZ", 6), ("QF-PAL", 6), ("QF-FLM", 3)], "prepare"),
    ("QF-DEMO-06", "poulina-group-holding", wh_rades, [("QF-EXP", 40), ("QF-CRT", 8)], "delivered"),
    ("QF-DEMO-07", "cho-terra-delyssa", wh_sfax, [("QF-DOU", 2), ("QF-STK", 45)], "confirmed"),
    ("QF-DEMO-08", "carthage-cement", wh_rades, [("QF-STK", 60), ("QF-MAN", 10)], "draft"),
]
ORDER_VEHICLE = {"QF-DEMO-01": "226 TU 0457", "QF-DEMO-02": "231 TU 7702", "QF-DEMO-03": "214 TU 3871",
                 "QF-DEMO-04": "219 TU 5520", "QF-DEMO-05": "205 TU 1194", "QF-DEMO-06": "233 TU 9015"}
tracking_refs = []
for i, (cref, ckey, wh, lines, outcome) in enumerate(ORDERS):
    order = env["sale.order"].search([("client_order_ref", "=", cref)], limit=1)
    if not order:
        order = env["sale.order"].create({
            "partner_id": clients[ckey].id,
            "client_order_ref": cref,
            "user_id": user.id,
            "warehouse_id": wh.id,
            "date_order": today - timedelta(days=(len(ORDERS) - i) * 3),
            "order_line": [(0, 0, {"product_id": products[r].id, "product_uom_qty": q}) for r, q in lines],
        })
        if outcome != "draft":
            order.action_confirm()
        for picking in order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel")):
            picking.action_assign()
            if cref in ORDER_VEHICLE and picking.picking_type_code == "outgoing":
                picking.qafila_vehicle_id = vehicles[ORDER_VEHICLE[cref]]
            if outcome in ("en_route",):
                picking.action_qafila_en_route()
            if outcome in ("delivered", "invoiced", "paid"):
                for move in picking.move_ids:
                    move.quantity = move.product_uom_qty
                    move.picked = True
                picking.with_context(skip_backorder=True, skip_sms=True).button_validate()
        if outcome in ("invoiced", "paid"):
            invoice = order._create_invoices()
            invoice.action_post()
            if outcome == "paid":
                env["account.payment.register"].with_context(
                    active_model="account.move", active_ids=invoice.ids).create({}).action_create_payments()
        log(f"commande {order.name} ({cref}) → {outcome}")
    if order.user_id != user:
        order.user_id = user
    order.invoice_ids.filtered(lambda m: m.invoice_user_id != user).write({"invoice_user_id": user.id})
    tracking_refs += [p.name for p in order.picking_ids if p.picking_type_code == "outgoing"]

# ------------------------------------------------------------------ pistes CRM
for title, contact, company_name, email, desc in [
    ("Devis Transport routier — Dar Jerba Artisanat", "Sonia Mejri", "Dar Jerba Artisanat (fictive)", "sonia.mejri@example.com",
     "Besoin : 4 palettes / semaine Houmt Souk → Tunis."),
    ("Devis Entreposage — Biscuiterie du Cap Bon", "Karim Ayadi", "Biscuiterie du Cap Bon (fictive)", "k.ayadi@example.com",
     "Stockage de 120 palettes à Radès pour la saison de Ramadan."),
]:
    upsert("crm.lead", [("name", "=", title)], {
        "name": title, "contact_name": contact, "partner_name": company_name, "email_from": email,
        "description": desc, "user_id": user.id,
        # la première piste illustre le formulaire du site (source « Site qafila.tn »)
        "source_id": env.ref("qafila_api.utm_source_site").id if "Dar Jerba" in title else False,
    })

env.ref("base.partner_root").write({"name": "Assistant Qafila", "image_1920": ASSETS["symbol"]})

home = env.ref("qafila_ops.action_qafila_dashboard", raise_if_not_found=False)
for u in env["res.users"].search([]):
    u.write({"lang": "fr_FR", "tz": "Africa/Tunis"})
    if home and not u.share:
        u.action_id = env["ir.actions.actions"].browse(home.id)  # première vue à la connexion : le tableau de bord, pas Discussion

env.cr.commit()
log("terminé ✔")
log("références de suivi utilisables sur qafila.tn : " + ", ".join(sorted(set(tracking_refs))))
