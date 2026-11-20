# 04 — Odoo configuration & demo data

## Modules

Installed: `contacts, crm, sale_management, purchase, stock, account (Invoicing), l10n_tn, calendar, fleet, maintenance` + our addons:

- `qafila_branding` — backend theme (primary = Bleu Sidi Bou Saïd, navbar Ink), fonts, login page, favicon, window title "Qafila" (no "Odoo" visible), user menu without odoo.com links.
- `qafila_api` — public JSON endpoints for the landing page (`/qafila/api/lead`, `/qafila/api/track`) + `qafila_stage` on outgoing pickings. Rules: `auth='public'`, `csrf=False` only on these routes, strict validation, per-IP throttle (per process — with 2 Odoo nodes the effective limit doubles), **tracking returns stage/date/city/truck plate only — never names, addresses, prices, driver**.
- `qafila_facture` — Qafila PDF layout for ALL documents (`external_layout_qafila`, set on the company) + professional invoice (replaces `account.report_invoice_document` body at priority 99; keeps hidden anchors `#qrcode`, `#payment_term`, `#right-elements` and `layout_document_title` for other modules' xpaths). Adds the **1,000 DT droit de timbre** line (product `QF-TIMBRE`, l10n_tn tax `l10n_tn_tax_vat_sale_tax_stamp`) automatically when a TN customer invoice is posted. Amount in words in French (dinars + millimes, `num2words`). PDF fonts are **static TTF** in `qafila_facture/static/fonts/` (wkhtmltopdf can't read woff2/variable fonts); `report.url = http://127.0.0.1:8069` so wkhtmltopdf loads CSS locally; tables use `border-collapse: separate` (collapse draws hairlines in wkhtmltopdf); no `t-field`/`t-options` directly on `<td>` (QWeb assertion) — wrap in `<span>`.
- `qafila_ops` — **home dashboard** (client action `qafila_dashboard`, first menu, set as `action_id` of every internal user — never Discuss), fleet extension (payload, pallets, reefer, base warehouse, next technical inspection, immobilised, computed `qafila_status` Disponible/En tournée/En maintenance/Immobilisé), fleet ↔ maintenance link (each vehicle = one `maintenance.equipment`, "Déclarer une panne" button), truck + driver on outgoing pickings ("Marquer en route" requires a truck).

No `website` module (the landing page is outside Odoo). The old `nexora_website` addon is removed.

## Module evaluation (2026-11-20) — kept / added / rejected, from Qafila's 3PL point of view

| Module | Verdict | Why (Qafila) |
|---|---|---|
| Contacts | ✅ keep | Clients, drivers, suppliers, insurer |
| CRM | ✅ keep | Receives quote requests from qafila.tn (source "Site qafila.tn") |
| Ventes | ✅ keep | Quotes/orders for transport, storage, customs services |
| Inventaire | ✅ keep — core | 2 warehouses (QRD Radès, QSF Sfax); outgoing pickings = tracked shipments |
| Achats | ✅ keep | Pallets, cartons, film, parts, fuel suppliers |
| Facturation + l10n_tn | ✅ keep | TND, TVA 19 %, timbre fiscal, Qafila invoice |
| Calendrier | ✅ keep (light) | Pickups / client appointments |
| Discussion (mail) | ⚙ technical | Required by everything; **no longer the home screen** |
| **Flotte** | ➕ added | Trucks, drivers, odometer, insurance contracts, inspections |
| **Maintenance** | ➕ added | Preventive/corrective work orders on trucks, forklifts, cold room, dock doors |
| partner_autocomplete, crm_iap_enrich, crm_iap_mine | ❌ removed | Send company/lead data to odoo.com (IAP), paid credits — privacy |
| spreadsheet_dashboard (+ _sale, _account, _stock_account) | ❌ removed | Replaced by the Qafila dashboard (lighter, logistics-specific) |
| Website / eCommerce | ❌ no | Landing page is hand-made (`landing/`) |
| Employés (hr), hr_fleet, hr_maintenance | ⏳ later | Drivers as employees (licence, contracts) — not needed for the demo, RAM |
| stock_fleet (batch transfers per vehicle) | ⏳ later | Useful for multi-stop routes; our direct picking→truck link is enough now |
| stock_delivery (carriers) | ❌ no | Qafila *is* the carrier |
| Réparation (repair) | ❌ no | Customer product repairs; Maintenance covers our assets |
| Projet, Feuilles de temps, Fabrication, PdV | ❌ no | Out of scope |
| SMS / snailmail (auto-installed) | ⚠ left | Paid IAP services, unused; uninstalling cascades into sale/stock/crm |
| Enterprise-only (Code-barres, Field Service, Documents, Studio, Planning, Helpdesk) | — n/a | Not in Community; barcode scanning would be the most useful upgrade |

Known functional gaps (future work): customer-owned stock in our warehouses (stock "owner" / consignment), per-client contract pricelists, cold-chain temperature logs, fuel logs per truck, multi-stop routes.

## Company

| Field | Value |
|---|---|
| Name | Qafila Logistique SARL |
| Address | Zone Industrielle de Radès, 2040 Radès, Ben Arous, Tunisie |
| Phone / email | +216 71 000 000 (fictional) / contact@qafila.tn |
| Report layout | `qafila_facture.external_layout_qafila` (all PDFs) |
| Legal (fictional) | MF `1789456/A/M/000`, RC `B01234562026`, capital 100 000 DT, BIAT RIB `08 006 0001234567890 12` (fictional numbers) |
| Currency | **TND** (3 decimals) — all pricelists, products, orders, invoices |
| Fiscal localisation | `l10n_tn` chart of accounts; default sales tax TVA 19 % |
| Language / TZ | fr_FR / Africa/Tunis |
| Warehouses | **QRD** Radès (main), **QSF** Sfax |

## The 5 clients (real Tunisian companies — public info only)

Relationship with Qafila is **fictional** (school demo). Store only publicly listed head-office data, no personal contacts, no invented emails at their real domains. Logos are taken from their official websites, saved in `addons/qafila_api/data/img/clients/` (or seed assets) and used only inside this local demo.

| # | Company | Sector | Head office (public sources) | Phone (public) |
|---|---|---|---|---|
| 1 | **Poulina Group Holding (PGH)** | Agro-industry, poultry, packaging | GP1 Km 12, 2034 Ezzahra, Ben Arous | +216 71 454 545 |
| 2 | **CHO Company (Terra Delyssa)** | Olive oil export | Route de Mahdia Km 18, 3066 Essaadi, Sfax | +216 74 447 677 |
| 3 | **SOTUVER** — Société Tunisienne de Verreries | Glass packaging | Z.I. Djebel Oust, 1111 Bir Mcherga, Zaghouan | — |
| 4 | **Carthage Cement** | Cement / construction | Rue 8002, Espace Tunis Bloc H, 3e étage, Montplaisir, 1073 Tunis | +216 71 964 593 |
| 5 | **SOTIPAPIER** | Kraft paper & cardboard | 13 rue Ibn Abi Dhiaf, Z.I. Saint Gobain, Mégrine Riadh, 2014 Ben Arous | +216 71 434 957 |

Sources: BVMT / CMF issuer filings, ilboursa.com, official sites (poulinagroupholding.com, terradelyssa.com, sotuver.com.tn, carthagecement.com.tn, sotipapier.com).

## The team: 1 admin + the 1 user required by the brief

| | Admin (technical) | **The user** (counted by the brief) |
|---|---|---|
| Name | **Yassine Chelly** — Administrateur ERP | **Karim Arouay** — Responsable logistique |
| Login | `yassine.chelly@qafila.tn` (= `ODOO_ADMIN_EMAIL`), password `ODOO_ADMIN_PASSWORD` | `karim.arouay@qafila.tn`, password `ODOO_DEMO_USER_PASSWORD` |
| Rights | Settings / all | Sales (all documents), Inventory user, Purchase user, Invoicing (billing), CRM. **Not** admin |
| Avatar | `brand/team/yassine-chelly.png` | `brand/team/karim-arouay.png` |

Both are the real project authors (the team requested by the user). All demo orders/invoices/leads are assigned to Karim Arouay so his dashboards are populated. Any other internal user is archived by the seed (exactly 1 business user). OdooBot is renamed "Assistant Qafila". Both users also get Fleet user + Maintenance rights; their home action is the Qafila dashboard.

## Products & services (prices in TND, HT)

Internal refs prefixed `QF-`. Each has a generated flat illustration (palette colours) as image.

| Ref | Name | Type | Price |
|---|---|---|---|
| QF-TR-SOU | Transport palette Tunis → Sousse | Service | 32.000 |
| QF-TR-SFX | Transport palette Tunis → Sfax | Service | 45.000 |
| QF-TR-TOZ | Transport palette Tunis → Tozeur | Service | 78.000 |
| QF-FTL-19 | Affrètement camion complet 19 t (journée) | Service | 950.000 |
| QF-EXP | Livraison express Grand Tunis (colis ≤ 30 kg) | Service | 12.500 |
| QF-STK | Entreposage palette / mois — Radès | Service | 28.000 |
| QF-FRD | Entreposage froid (2–8 °C) palette / mois | Service | 55.000 |
| QF-DOU | Dédouanement import (par dossier) | Service | 180.000 |
| QF-MAN | Manutention & préparation de commande (heure) | Service | 22.000 |
| QF-PAL | Palette Europe EPAL 1200×800 | Goods (stock) | 38.000 (cost 29.000) |
| QF-CRT | Cartons double cannelure 60×40×40 (lot de 25) | Goods (stock) | 42.500 (cost 31.000) |
| QF-FLM | Film étirable 500 mm × 300 m | Goods (stock) | 18.900 (cost 12.400) |

## Transactions (so dashboards are not empty)

- Initial stock of QF-PAL / QF-CRT / QF-FLM in QRD and QSF.
- ~8 sales orders spread over the 5 clients (mix of draft quotation, confirmed, delivered, invoiced).
- Deliveries named like `QRD/OUT/00003` — these refs work in the landing page tracking widget. Current demo refs: `QRD/OUT/00003` = En route (SOTUVER), `QRD/OUT/00004` = Préparée (SOTIPAPIER), `QSF/OUT/00001` = Livrée (CHO). The landing page hard-codes `QRD/OUT/00003` and `QSF/OUT/00001` as examples — keep them valid.
- A few posted customer invoices in TND, one paid.
- 2–3 CRM leads (one coming from the landing form test).

## Fleet & maintenance demo data

8 vehicles (Tunisian plates `NNN TU NNNN`) with fictional drivers: 2× Renault Trucks D Wide 19 t, Mercedes Actros + reefer trailer, Iveco Eurocargo (Sfax), Isuzu NPR reefer (**in maintenance**: groupe froid), 2× Iveco Daily express, Renault Master (Sfax, **immobilised**, inspection overdue). Insurance contracts (one expiring within 30 days), maintenance team "Atelier Qafila — Radès", equipment (2 forklifts, pallet truck, cold room CF-1, dock door), 6 work orders (preventive recurring + corrective). Shipments carry trucks: `QRD/OUT/00003` → 219 TU 5520 (en tournée).

## Seed rules

`scripts/seed.py` runs inside `odoo shell` and must be **idempotent** (search by `ref`/`default_code`/name before create; re-running must not duplicate anything).
