# 03 — Architecture & infrastructure

## Machines

| Host | Role | Notes |
|---|---|---|
| `qafila-tpl` (this VM, RHEL 10.2, ~5 GB RAM) | **Template** + single-node dev/demo stack | Hardened, then cloned to make the nodes |
| `qafila-node1` | HA node A — PostgreSQL **primary**, Odoo, Caddy, keepalived (MASTER) | clone of template |
| `qafila-node2` | HA node B — PostgreSQL **standby** (streaming replica), Odoo, Caddy, keepalived (BACKUP) | clone of template |

Node IPs and the virtual IP (VIP) are set in `.env` (`NODE1_IP`, `NODE2_IP`, `VIP`). Defaults (192.168.56.10–12) are placeholders until the user sets up the two clone VMs. The HA path is written but **not yet tested on real nodes**.

## Single-node stack (template / dev) — `compose.yaml`

```text
browser ──https──► Caddy :443 (qafila.tn → landing/, erp.qafila.tn → Odoo)
                     │  lb_policy cookie, health check /web/health
                     ├──► odoo-1 :8069 ┐
                     └──► odoo-2 :8069 ┘──► db (PostgreSQL 16)
                                         filestore volume shared by both Odoo containers
```

- Container runtime: **Podman rootless** (RHEL native). `compose.yaml` must stay compatible with Docker Compose too.
- Images: `docker.io/library/odoo:19.0`, `docker.io/library/postgres:16-alpine`, `docker.io/library/caddy:2-alpine` — official images only, pinned tags.
- `net.ipv4.ip_unprivileged_port_start=80` is already set, so rootless Caddy binds 80/443.
- Only Caddy publishes ports. PostgreSQL and Odoo are on the internal network only.

## HA stack (node1 + node2)

```text
                    VIP (keepalived, VRRP) = qafila.tn / erp.qafila.tn
                 ┌───────────────┴────────────────┐
           node1 (MASTER)                    node2 (BACKUP)
      Caddy ─► odoo(node1)+odoo(node2)   Caddy ─► odoo(node1)+odoo(node2)
      PostgreSQL PRIMARY ──streaming replication──► PostgreSQL STANDBY (hot)
```

- Implemented in `config/ha/compose.ha.yaml` (one Odoo per node, **host networking** because rootless container networks cannot reliably reach the host-held VIP; exposure is limited by firewalld rich rules: 5432/8069 only from the peer node).
- Odoo on both nodes connects to PostgreSQL **through the VIP**; the standby's `primary_conninfo` also points to the VIP, so after a failover nothing needs reconfiguring.
- `QAFILA_ROLE` in `.env` (`single` | `primary` | `standby`) only drives the **first** install (hostname, keepalived priority 150/100, who creates the DB). After that, `install.sh` reads the **real** role from the local DB (`pg_is_in_recovery()`), because roles swap after a failover. It refuses to run on a fenced node or on a primary while another primary serves the VIP.
- **keepalived** (`config/ha/keepalived.conf.tmpl`): both nodes `state BACKUP` + `nopreempt` (a node that comes back never takes the VIP back → no split brain), health script without `weight` (failure ⇒ FAULT ⇒ VIP released), `notify_master` ⇒ promote.
- Root scripts are installed by `node-setup.sh` into `/usr/libexec/keepalived/` (root-owned; that path has the SELinux type `keepalived_unconfined_script_exec_t`). Scripts in the user-owned project dir would be refused by `enable_script_security` and blocked by SELinux. Their settings/secrets: `/etc/qafila/ha.env` (0600). Re-run `node-setup.sh` after editing `scripts/ha/check.sh` or `promote.sh`.
  - `qafila-check` (= `scripts/ha/check.sh`, every 5 s): local PostgreSQL up, local Caddy serves `/web/health`, and **fencing**: local DB primary + VIP elsewhere + the DB behind the VIP is primary ⇒ this node is a stale ex-primary ⇒ stop its DB, write `/var/lib/qafila/fenced`, fail forever until rebuilt. The flag clears itself once the local DB runs as a replica.
  - `qafila-promote` (= `scripts/ha/promote.sh`): `pg_promote()` if the local DB is in recovery.
- `scripts/ha/init-standby.sh [source]` (default: VIP) rebuilds the local DB as a replica (pg_basebackup -R, replication slot recreated). Used for node2's first setup and to reintegrate a fenced node.
- `max_slot_wal_keep_size=2GB`: a long-dead replica cannot fill the primary's disk; it then needs `init-standby.sh`.
- `node-setup.sh` also enables linger + `podman-restart.service` so rootless containers come back after a reboot.
- `scripts/ha/lab-test.sh`: runs the real `check.sh`/`promote.sh` against two throw-away PostgreSQL (host network, ports 15432/15433) on one machine — replication, failover, fencing, reintegration (16 assertions). Only keepalived/VIP are simulated. Use it to demo HA without two VMs.
- Caddy upstreams come from env `ODOO_UPSTREAMS` (single: `odoo-1:8069 odoo-2:8069`; HA: `NODE1_IP:8069 NODE2_IP:8069`) — one shared `config/Caddyfile`.
- The Caddy local CA lives in the `caddy-data` volume; cloning the template VM gives both nodes the same CA (same trusted root).
- **Attachments stored in the database** (`ir_attachment.location = db`) so PostgreSQL replication covers the filestore — no NFS single point of failure.
- Sessions: Odoo filesystem sessions are per node → after a node failover users may need to log in again. Acceptable and documented.
- **Known limits of 2 nodes (no witness):** replication is asynchronous (a failover can lose the last ~second of writes); if node A dies, B takes over, then B dies *before* A comes back, A would restart as primary with stale data — preventing that needs a 3rd voter. Production target (README only): Patroni + etcd (3 nodes), HAProxy, off-site encrypted backups.

## Local domains (no purchase)

- `/etc/hosts` on each client machine: `<VIP or 127.0.0.1> qafila.tn www.qafila.tn erp.qafila.tn`.
- TLS: Caddy `tls internal` (its own local CA). The root CA (`caddy-root.crt`) is trusted with `sudo trust anchor` → no browser warning, no port, no IP in the URL.
- Old `nexora.com` hosts entry must be removed.

## Routing contract (Caddy)

| URL | Backend |
|---|---|
| `https://qafila.tn/` | static files `landing/` (brand book at `/marque/`) |
| `https://qafila.tn/api/devis` (POST) | Odoo `/qafila/api/lead` → creates `crm.lead` |
| `https://qafila.tn/api/suivi?ref=…` (GET) | Odoo `/qafila/api/track` → delivery status only |
| `https://erp.qafila.tn/` | Odoo (load balanced) |
| `https://erp.qafila.tn/web/database/*` | **blocked** (403) |

Security headers set in Caddy: HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options SAMEORIGIN`, CSP on the landing.

## Odoo config essentials

`proxy_mode = True`, `report.url = http://127.0.0.1:8069` (system parameter, for wkhtmltopdf), `list_db = False`, `dbfilter = ^qafila$`, `workers = 0` (threaded, RAM is tight), DB name **`qafila`**, addons mounted at `/mnt/extra-addons`. Secrets only in `.env` (never committed).

## Hardening (template) — `scripts/harden.sh` (run with sudo by the user)

SELinux enforcing; firewalld allows only ssh, http, https (+ VRRP between nodes); SSH: no root login, keys only; `dnf-automatic` security updates; `auditd`; password quality policy; containers rootless, `no-new-privileges`, memory limits; backups via `scripts/backup.sh` (pg_dump + filestore, rotation).

## RAM budget (template, ~1.4 GB free)

Odoo ×2 ≈ 2×350 MB, PostgreSQL ≈ 150 MB, Caddy ≈ 30 MB. Keep `limit_memory_*` conservative. Do not add Elasticsearch/Redis/etc.
