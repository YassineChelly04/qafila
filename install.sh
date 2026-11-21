#!/usr/bin/env bash
# Qafila — installation / mise à jour. Idempotent : peut être relancé sans dupliquer les données.
# QAFILA_ROLE (dans .env) : single  = modèle mono-hôte (2 Odoo + 1 PostgreSQL sur cette machine)
#                           primary = nœud HA 1 (PostgreSQL primaire)   → config/ha/compose.ha.yaml
#                           standby = nœud HA 2 (PostgreSQL réplique)    → config/ha/compose.ha.yaml
set -euo pipefail
cd "$(dirname "$0")"

ODOO_IMAGE=docker.io/library/odoo:19.0
NET=qafila_backend
MODULES=contacts,crm,sale_management,purchase,stock,account,l10n_tn,fleet,maintenance,qafila_branding,qafila_api,qafila_facture,qafila_ops

say() { printf '\033[1;34m▸\033[0m %s\n' "$*"; }

command -v podman-compose >/dev/null || { echo "podman-compose introuvable (voir README)"; exit 1; }
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Fichier .env créé : remplacez toutes les valeurs change-me puis relancez ./install.sh"
  exit 1
fi
if grep -q 'change-me' .env; then
  echo ".env contient encore des valeurs change-me : remplacez-les avant d'installer."
  exit 1
fi
set -a; source .env; set +a
ROLE="${QAFILA_ROLE:-single}"
if [[ "$ROLE" == single ]]; then
  COMPOSE=(podman-compose -f compose.yaml); DB_HOST=db; NET_OPT=(--network "$NET")
else
  COMPOSE=(podman-compose -f config/ha/compose.ha.yaml); DB_HOST="$VIP"; NET_OPT=(--network host)
fi
export DB_HOST
say "Rôle de cette machine : $ROLE"

# ./install.sh --reset : repart d'une base vierge (données de démonstration recréées par le seed)
RESET=0; [[ "${1:-}" == "--reset" ]] && RESET=1

# 1. Configuration Odoo générée à partir du modèle (secrets jamais committés)
say "Génération de .runtime/odoo.conf"
mkdir -p .runtime
podman unshare rm -f .runtime/odoo.conf 2>/dev/null || true
python3 - <<'PY'
import os
from pathlib import Path
s = Path("config/odoo.conf.template").read_text()
for key in ("ODOO_MASTER_PASSWORD", "POSTGRES_USER", "POSTGRES_PASSWORD", "ODOO_DB", "DB_HOST"):
    s = s.replace(f"__{key}__", os.environ[key])
out = Path(".runtime/odoo.conf")
out.write_text(s)
out.chmod(0o400)
PY
podman unshare chown 100:101 .runtime/odoo.conf   # utilisateur « odoo » du conteneur

# 2. Police Thmanyah (usage scolaire, jamais redistribuée) copiée dans l'addon si présente
if compgen -G "landing/assets/fonts/thmanyah/*.woff2" >/dev/null; then
  mkdir -p addons/qafila_branding/static/fonts/thmanyah
  cp landing/assets/fonts/thmanyah/*.woff2 addons/qafila_branding/static/fonts/thmanyah/
fi

# 3. Base de données
say "Démarrage de PostgreSQL"
# Passage mono-hôte → nœud HA : les conteneurs du modèle (réseau isolé) portent les mêmes noms.
# On les retire (les volumes, donc les données, sont conservés) pour recréer la pile en réseau « host ».
if [[ "$ROLE" != single ]] && podman container exists qafila-db \
   && [[ $(podman inspect -f '{{.HostConfig.NetworkMode}}' qafila-db) != host ]]; then
  say "Retrait de l'ancienne pile mono-hôte (données conservées)"
  podman-compose -f compose.yaml down >/dev/null 2>&1 || true
  podman rm -f qafila-caddy qafila-odoo-1 qafila-odoo-2 qafila-db >/dev/null 2>&1 || true
fi
"${COMPOSE[@]}" up -d db >/dev/null
for _ in $(seq 1 60); do
  podman exec qafila-db pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1 && break
  sleep 2
done

DB_ONCE=()   # options de connexion ajoutées aux commandes Odoo ponctuelles (HA : base locale)
odoo_once() {
  podman run --rm -i "${NET_OPT[@]}" \
    -v "$PWD/.runtime/odoo.conf:/etc/odoo/odoo.conf:ro,Z" \
    -v "$PWD/addons:/mnt/extra-addons:ro,z" \
    -v qafila_qafila-filestore:/var/lib/odoo:z \
    "$ODOO_IMAGE" "$@" "${DB_ONCE[@]}"
}

if [[ "$ROLE" != single ]]; then
  # En HA, QAFILA_ROLE ne sert qu'à la première installation : après une bascule les rôles
  # s'inversent. Le rôle RÉEL est lu dans la base locale.
  if [[ -f /var/lib/qafila/fenced ]] && \
     [[ $(podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc "select pg_is_in_recovery()" 2>/dev/null) != t ]]; then
    podman stop qafila-db >/dev/null 2>&1 || true
    echo "Ce nœud est CLÔTURÉ : sa base est une ancienne primaire périmée (l'autre nœud a pris le relais)."
    echo "Réintégrez-le comme réplique : ./scripts/ha/init-standby.sh  puis ./install.sh"
    exit 1
  fi
  if [[ $(podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc "select pg_is_in_recovery()") == t ]]; then
    # Réplique : elle reçoit la base du primaire, ni création ni données ici.
    say "Nœud de secours : base répliquée depuis le primaire (via $VIP), démarrage des services"
    "${COMPOSE[@]}" up -d >/dev/null
    say "Terminé. État : ./scripts/ha/status.sh"
    exit 0
  fi
  # Base locale primaire : on refuse si un AUTRE primaire sert déjà l'IP virtuelle.
  if ! ip -o -4 addr show | grep -q " $VIP/"; then
    vip_role=$(podman exec -e PGPASSWORD="$POSTGRES_PASSWORD" -e PGCONNECT_TIMEOUT=3 qafila-db \
      psql -h "$VIP" -U "$POSTGRES_USER" -d postgres -tAc "select pg_is_in_recovery()" 2>/dev/null || true)
    if [[ "$vip_role" == f || "$ROLE" == standby ]]; then
      podman stop qafila-db >/dev/null 2>&1 || true
      echo "La base de ce nœud n'est pas une réplique, alors que le primaire est ailleurs."
      echo "Initialisez-la comme réplique : ./scripts/ha/init-standby.sh  puis ./install.sh"
      exit 1
    fi
  fi
  # Première installation : la VIP n'existe pas encore (Caddy pas démarré) → base locale directe
  DB_ONCE=(--db_host 127.0.0.1)
  say "Autorisation de la réplication entre $NODE1_IP et $NODE2_IP"
  podman exec -i qafila-db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 >/dev/null <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
    CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '$REPLICATION_PASSWORD';
  ELSE
    ALTER ROLE replicator WITH PASSWORD '$REPLICATION_PASSWORD';
  END IF;
END \$\$;
SQL
  # Les deux nœuds sont autorisés : après une bascule, l'ancien primaire redevient réplique
  for ip in "$NODE1_IP" "$NODE2_IP"; do
    podman exec qafila-db sh -c "grep -q 'replication replicator $ip/32' \$PGDATA/pg_hba.conf || \
      echo 'host replication replicator $ip/32 scram-sha-256' >> \$PGDATA/pg_hba.conf"
  done
  podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc "select pg_reload_conf()" >/dev/null
fi

if [[ $RESET == 1 ]]; then
  say "Réinitialisation : suppression de la base $ODOO_DB"
  podman stop qafila-odoo-1 qafila-odoo-2 >/dev/null 2>&1 || true
  podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$ODOO_DB\" WITH (FORCE)" >/dev/null
fi

if podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc \
     "select 1 from pg_database where datname='$ODOO_DB'" | grep -q 1; then
  say "Mise à jour des modules Qafila"
  odoo_once odoo -c /etc/odoo/odoo.conf -d "$ODOO_DB" -i "$MODULES" -u qafila_branding,qafila_api,qafila_facture,qafila_ops --stop-after-init --no-http
else
  say "Création de la base $ODOO_DB (plusieurs minutes)"
  odoo_once odoo -c /etc/odoo/odoo.conf -d "$ODOO_DB" -i "$MODULES" --load-language fr_FR \
    --stop-after-init --no-http
fi

# 3b. Modules retirés après évaluation (docs/04-ODOO-DATA.md) :
#     - enrichissement IAP : envoie les données société/pistes à odoo.com ;
#     - tableaux de bord « spreadsheet » : remplacés par le tableau de bord Qafila (qafila_ops).
say "Retrait des modules non retenus"
echo "mods = env['ir.module.module'].search([('name', 'in', ['partner_autocomplete', 'crm_iap_enrich', 'crm_iap_mine', 'spreadsheet_dashboard']), ('state', '=', 'installed')])
if mods: mods.button_immediate_uninstall()
env.cr.commit()" | odoo_once odoo shell -c /etc/odoo/odoo.conf -d "$ODOO_DB" --no-http >/dev/null 2>&1 || true

# 4. Données de démonstration (société, 5 clients, 1 utilisateur, produits, commandes)
say "Chargement des données Qafila"
python3 - <<'PY' | odoo_once odoo shell -c /etc/odoo/odoo.conf -d "$ODOO_DB" --no-http
import base64, json, os
from pathlib import Path
b64 = lambda p: base64.b64encode(Path(p).read_bytes()).decode()
assets = {
    "logo": b64("brand/logo/qafila-logo-600.png"),
    "symbol": b64("brand/logo/qafila-symbol-512.png"),
}
for p in Path("brand/team").glob("*.png"):
    assets[f"avatar:{p.stem}"] = b64(p)
for p in Path("brand/clients").glob("*.png"):
    assets[f"client:{p.stem}"] = b64(p)
for p in Path("brand/products").glob("*.png"):
    assets[f"product:{p.stem}"] = b64(p)
s = Path("scripts/seed.py").read_text()
s = s.replace("__ASSETS_JSON_B64__", base64.b64encode(json.dumps(assets).encode()).decode())
for key in ("ODOO_ADMIN_PASSWORD", "ODOO_ADMIN_EMAIL", "ODOO_DEMO_USER_PASSWORD", "QAFILA_ERP_DOMAIN"):
    s = s.replace(f"__{key}__", os.environ[key].replace("\\", "\\\\").replace('"', '\\"'))
print(s)
PY

# 5. Pile complète : 2 nœuds Odoo + Caddy
say "Démarrage d'Odoo et de Caddy"
"${COMPOSE[@]}" up -d >/dev/null
# Les serveurs déjà lancés gardent l'ancien code Python : on les redémarre après une mise à jour
running=$(podman ps --format '{{.Names}}' | grep '^qafila-odoo' || true)
[[ -n "$running" ]] && podman restart $running >/dev/null

# 6. Certificat racine local à approuver (scripts/sudo-setup.sh)
for _ in $(seq 1 30); do
  podman cp qafila-caddy:/data/caddy/pki/authorities/local/root.crt config/caddy-root.crt 2>/dev/null && break
  sleep 2
done

say "Terminé."
echo "  • Site vitrine : https://${QAFILA_DOMAIN}"
echo "  • ERP          : https://${QAFILA_ERP_DOMAIN}  (${ODOO_ADMIN_EMAIL} / ODOO_ADMIN_PASSWORD, karim.arouay@qafila.tn / ODOO_DEMO_USER_PASSWORD)"
grep -q "${QAFILA_ERP_DOMAIN}" /etc/hosts && trust list 2>/dev/null | grep -q "Caddy Local Authority" || \
  echo "  ⚠ Première fois ? Lancez : sudo ./scripts/sudo-setup.sh  (domaines locaux + certificat)"
