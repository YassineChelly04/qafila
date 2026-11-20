# 05 — Rules for agents & project status

## Hard rules

1. **Read docs 01→05 before changing anything.** Update the relevant doc in the same change when you alter a decision.
2. **Brand is strict** (02-BRAND): only Funnel Display, Familjen Grotesk, Thmanyah. Only palette tokens. No Inter/Poppins/Roboto/Montserrat/IBM Plex/monospace fonts, no purple gradients, no emoji as icons, no generic "AI SaaS" look.
3. **French** for every user-facing string. Arabic only in Thmanyah.
4. **TND only.** Never leave EUR/USD anywhere (products, pricelists, reports, landing).
5. **Landing page = hand-written HTML/CSS/JS in `landing/`.** Never use Odoo's `website` module or its builder. No frameworks, no build step, no external CDN at runtime (fonts and assets are self-hosted).
6. **Thmanyah font licence:** personal/school use only. The font files live in `landing/assets/fonts/thmanyah/` (and are copied into the branding addon at install time if needed). Never commit them to a public repo, never publish them online. The folder is in `.gitignore`.
7. **Real client companies:** use only public head-office info and their official logos. Never invent testimonials, quotes, figures or emails attributed to them. On the landing page, client logos carry the note « Démonstration académique ».
8. **Secrets** only in `.env` (git-ignored). `.env.example` holds placeholders. Never print passwords in logs or README.
9. **Containers:** official images, pinned tags, rootless Podman, compose must also work with Docker Compose. Only Caddy publishes ports.
10. **Seed is idempotent.** Re-running `install.sh` must never duplicate data.
11. **Commands needing sudo** (hosts file, CA trust, hardening, firewall) are written into scripts and given to the user — agents cannot run sudo here.
12. **Accessibility:** contrast ≥ 4.5:1 for text, visible focus states, `prefers-reduced-motion`, semantic HTML, alt text.
13. RAM is tight (~1.4 GB free on the template): no extra services beyond what 03-ARCHITECTURE lists.

## ERP screens & PDF documents — product UI rules (from `deslop-erp-dashboard-SKILL.md`)

The ERP is a work tool used all day, not a landing page. In `qafila_ops` (dashboard) and `qafila_facture` (PDFs):

- **Dashboard = operational overview.** Order: « À traiter » (actionable items, each clickable, severity word + colour) → KPI band (ONE anchor metric = shipments in progress, 3 secondary metrics in hairline-separated cells, each with period + comparison/context) → working tables (shipments, maintenance) → fleet availability + exceptions → revenue bar list whose title is the takeaway sentence.
- **Banned:** greetings ("Bonjour X 👋"), four identical KPI cards, cards inside cards, shadows on static panels, hover-lift, count-up animations, gradients, donuts/pies, "(s)" plurals (use `_pl()`), "No data"/bare spinners, decorative Arabic in the ERP.
- **Status colour map (fixed everywhere, always with a word):** success = disponible/livrée, info = en tournée/en route, warning = maintenance/à surveiller, critical = immobilisé/urgent/échu, neutral = reçue/prête/basse.
- Surfaces: neutral background `#F5F4F0`, white panels, 1 px `#E4E0D6` borders, radius 6 px. Type: 22 px page title, 16 px section, 14 px body, 13.5 px tables, 12 px metadata. Tables: 40 px rows, `table-layout: fixed` + `<colgroup>`, ellipsis, numbers right-aligned, tabular figures.
- States: skeleton while loading, error with « Réessayer », explicit empty-state sentences, "données mises à jour à HH:MM".
- Overview money has no millimes (`7 824 DT`); documents keep 3 decimals.
- **Invoice = accounting document:** ink on white, hairlines, currency in column headers (« P.U. HT (DT) »), one strong rule above « Net à payer TTC », status in words (« Payée le … », never a rotated stamp), amount in words as a plain legal sentence, no slogan/route motif/coloured boxes.
- wkhtmltopdf quirks: no `font-feature-settings` (drops spaces); a space right before an inline element is lost → use `class="qf-gapl"` (margin) or merge text into one `t-out`.

## Repository layout (target)

```text
odoo-logistique-ha/
├── docs/                  ← these 5 files
├── brand/                 ← logo, products/, clients/, team/ + generator scripts
├── landing/               ← static site (index.html, marque/, assets/css|js|img|fonts)
├── addons/qafila_branding/
├── addons/qafila_api/
├── addons/qafila_facture/  ← PDF layout + invoice
├── addons/qafila_ops/      ← dashboard, fleet, maintenance
├── config/                ← odoo.conf.template, Caddyfile, ha/ (compose.ha.yaml, keepalived.conf.tmpl)
├── scripts/               ← seed.py, harden.sh, backup.sh, ha/*.sh, sudo-setup.sh
├── compose.yaml
├── install.sh
├── .env.example
└── README.md              ← French, for the jury / teacher
```

## Status log (update when you finish something)

| Date | Item | State |
|---|---|---|
| 2026-11-20 | Name Qafila, brand research, docs | ✅ |
| 2026-11-20 | Logo (route-q), product illustrations, client logos, team avatars (`brand/`) | ✅ |
| 2026-11-20 | Landing page `landing/` (map, services, tracking, platform, clients, team, devis form) + brand book `/marque/` | ✅ verified in headless Chromium (desktop + 390 px mobile) |
| 2026-11-20 | compose (Caddy + 2 Odoo + PG), local domains, TLS (`local_certs`) | ✅ running |
| 2026-11-20 | `qafila_branding`, `qafila_api` | ✅ installed, endpoints tested |
| 2026-11-20 | Seed: company, 5 real clients, Yassine (admin) + Karim (user), 12 products, 8 orders, 3 invoices, leads | ✅ idempotent (re-run 3×) |
| 2026-11-20 | `harden.sh`, `backup.sh`, `sudo-setup.sh` | ✅ written; backup tested; sudo scripts must be run by the user |
| 2026-11-20 | HA node configs (`config/ha`, `scripts/ha`) | ⚠ written, syntax-checked, not tested on real nodes |
| 2026-11-20 | Thmanyah font files | ⏳ waiting for the user to download them (fallback Noto Arabic meanwhile) |
| 2026-11-20 | README FR + demo scenario | ✅ |
| 2026-11-20 | Team photos (Yassine admin, Karim user) on site + Odoo avatars | ✅ |
| 2026-11-20 | `qafila_facture`: Qafila PDF layout + professional invoice (timbre, montant en lettres, MF/RC/RIB) | ✅ PDF verified |
| 2026-11-20 | `qafila_ops`: home dashboard, fleet (8 trucks), maintenance, truck on shipments | ✅ verified as Karim |
| 2026-11-20 | Module evaluation (docs/04) + removal of IAP enrichment & spreadsheet dashboards | ✅ |
| 2026-11-20 | De-slop pass on dashboard + invoice (rules above) | ✅ verified 1440/1280 px + PDF |
| 2026-11-20 | Landing « de-slop » pass: claim-led hero, bon-de-route label signature, lead offer + tariff list, journey merged into tracking, timetable network, team + demo clients merged; removed stats band (unsourced 98,4 %, count-ups), blanket fade-up, floating ticket | ✅ checked in headless Firefox (1440 px + 390 px) |
| 2026-11-20 | Landing v3: scroll-driven illustrated voyage background (`brand/build_world.py` → `world.html`), centred minimal copy, route rail, label-styled tracking & quote form | ✅ checked per stage in headless Firefox (1440 px + 390 px); real-browser scroll feel to confirm |

## Regenerating assets

- Scroll background: `python3 brand/build_world.py` → `landing/assets/img/world.html`. Bump the `?v=` query on the CSS/JS/world links in `landing/index.html` after changes (assets are cached 7 days by Caddy).

- Logo: `python brand/build_brand.py <dir with FunnelDisplay.ttf> [thmanyah.ttf]` (needs fontTools, uharfbuzz, rsvg-convert). With the Thmanyah file it adds «قافلة» to the lockup.
- Product illustrations: `python3 brand/build_products.py` (needs Familjen Grotesk installed for rsvg text).
- After changing anything in `brand/`, copy to `landing/assets/img/` and `addons/qafila_branding/static/img/` and re-run `./install.sh`.

## Known history / pitfalls

- Previous iteration was branded **Nexora** (fictional clients, `nexora_website` addon based on Odoo website). All Nexora traces must be gone.
- Previous `odoo.conf` had a typo in `addons_path` (`adoons`) and the custom addons folder was never mounted — check mounts when an addon "doesn't appear".
- Odoo 19 health endpoint: `/web/health`.
- Host has no `pip`; use `python3 -m venv` for helper tools. `podman-compose` lives in `~/.local/share/podman-compose-venv` (symlinked in `~/.local/bin`).
- `.runtime/odoo.conf` is chowned to the container's odoo uid via `podman unshare`; delete it with `podman unshare rm`.
- The landing CSP is strict (`style-src 'self'`): **no inline `style=""` attributes or inline scripts** in landing HTML. Setting styles from JS (CSSOM) is fine.
- Odoo 19: `res.users.group_ids` (not `groups_id`), `product.template.is_storable`, `type='jsonrpc'` (json deprecated), `without_demo = True` (not `all`).
- Odoo pages never reach "networkidle" in Playwright (websocket) — use fixed waits or wait for `.qf-dash__inner`.
- Running Odoo servers keep old Python code: `install.sh` restarts `qafila-odoo-*` after updating modules.
- Failed installs still consume PostgreSQL sequences (S0000x, OUT/0000x). The landing page hard-codes `QRD/OUT/00003` / `QSF/OUT/00001`: after a failed run use `./install.sh --reset` to get clean numbering.
- `res.users.action_id` must be an `ir.actions.actions` record: `env["ir.actions.actions"].browse(client_action.id)`.
- `res.partner.bank.allow_out_payment` can only be set at creation (trust rights) — never in a later write.
