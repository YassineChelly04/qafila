# 01 — Vision & scope

> **Read order for any agent:** 01-VISION → 02-BRAND → 03-ARCHITECTURE → 04-ODOO-DATA → 05-AGENT-RULES.
> These 5 files are the single source of truth. If code and docs disagree, fix the code **or** update the docs in the same change — never leave them out of sync.

## The assignment (cahier des charges)

School mini-project 2026-2027, class SI-ERP (GSIL PROD), CNIS — team **Yassine Chelly & Karim Arouay**.
Subject n°8:

> *Implémentation d'une architecture d'ERP basée sur ODOO (Open source + OS Linux) hautement disponible pour une entreprise active dans le domaine de la logistique — simulation d'une base de données de 5 clients + 1 utilisateur.*

Brief requirements we must visibly satisfy:

| Requirement from the brief | How we meet it |
|---|---|
| Virtualisation (VMware / VirtualBox / Hyper-V) | RHEL VMs on a type-2 hypervisor; this VM is the **template** |
| Red Hat Enterprise Linux 9.5 / 9.6 / 10.0 (dev subscription) | Host runs **RHEL 10.2** |
| Containerisation (Docker, Docker Compose…) | Podman rootless + `compose.yaml` (works with `podman-compose` and Docker Compose) |
| Hardening of the template host | `scripts/harden.sh` (SELinux, firewalld, SSH, updates, audit) |
| Odoo Community as ERP | Odoo **19.0** Community, official image |
| Highly available | Template + **2 cloned nodes** (keepalived VIP, PG streaming replica, 2 Odoo nodes) |
| Logistics company | Fictional company **Qafila** |
| 5 clients + 1 user | 5 **real Tunisian companies** as demo clients + 1 logistics user (Karim Arouay; Yassine Chelly is the admin) |

## The company: Qafila (قافلة)

- **Name meaning:** "caravan". Caravans crossed Tunisia for centuries (Kairouan, Tozeur, Gafsa → the northern ports). Qafila is the modern caravan: same routes, real-time tracking.
- **Tagline (FR):** « Qafila — La route est tracée. »
- **Activity:** Tunisian 3PL (third-party logistics): road freight by pallet and full truckload, warehousing (ambient + cold), express delivery Grand Tunis, customs clearance.
- **HQ (fictional):** Zone Industrielle de Radès, 2040 Radès, Ben Arous. Second warehouse: Sfax (Route de Gabès).
- **Local domains (not purchased, resolved locally):** `qafila.tn` (landing) and `erp.qafila.tn` (Odoo).
- **Currency:** Tunisian dinar **TND** everywhere (3 decimals, millimes).
- **Language:** **French** for every user-facing text (landing page, Odoo UI, documents). Arabic only as brand accents (wordmark, small labels), always in the Thmanyah font.

## Deliverables (definition of done)

1. Brand system (logo, palette, type, voice) — `brand/` + brand book page.
2. Custom landing page, hand-written HTML/CSS/JS — `landing/` (NOT Odoo's website builder).
3. Odoo configured & branded — `addons/qafila_branding`, `addons/qafila_api`, `scripts/seed.py`.
4. Infrastructure as code — `compose.yaml`, `Caddyfile`, `install.sh`, HA configs for node1/node2.
5. Hardening — `scripts/harden.sh`.
6. French README + demo script for the oral presentation (including a live failover).

## Non-goals

- No real domain purchase, no public exposure to the internet.
- No Odoo Enterprise modules, no paid themes.
- Not a production system: data is demo data; tax setup must be validated by an accountant before any real use.
