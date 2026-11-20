#!/usr/bin/env bash
# Qafila — (ré)initialise la base LOCALE comme réplique en continu d'un primaire.
# Usage : ./scripts/ha/init-standby.sh [IP_DU_PRIMAIRE]   (défaut : NODE1_IP)
#  - mise en place : sur qafila-node2, après ./install.sh sur qafila-node1 ;
#  - après une bascule : sur l'ancien primaire revenu en ligne, avec l'IP du nouveau primaire.
# ⚠ Efface la base locale (elle est recopiée depuis le primaire).
set -euo pipefail
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
SOURCE="${1:-$NODE1_IP}"
SLOT="qafila_$(hostname -s | tr -c 'a-z0-9\n' '_')"
read -r -p "Effacer la base locale et la recopier depuis $SOURCE ? (oui/non) " ok
[[ "$ok" == oui ]] || { echo "Annulé."; exit 1; }

podman rm -f qafila-db >/dev/null 2>&1 || true
podman volume rm -f qafila_qafila-pg >/dev/null 2>&1 || true
podman volume create qafila_qafila-pg >/dev/null

echo "Copie de base depuis $SOURCE (pg_basebackup)…"
podman run --rm --network host -e PGPASSWORD="$REPLICATION_PASSWORD" \
  -v qafila_qafila-pg:/var/lib/postgresql/data:Z docker.io/library/postgres:16-alpine \
  sh -c "pg_basebackup -h $SOURCE -U replicator -D /var/lib/postgresql/data -R -X stream -C -S $SLOT -P \
         && chown -R postgres:postgres /var/lib/postgresql/data && chmod 700 /var/lib/postgresql/data"
echo "✔ Réplique initialisée (standby.signal + primary_conninfo). Mettez QAFILA_ROLE=standby dans .env puis lancez ./install.sh"
