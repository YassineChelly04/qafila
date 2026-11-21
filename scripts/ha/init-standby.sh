#!/usr/bin/env bash
# Qafila — (ré)initialise la base LOCALE comme réplique en continu du primaire.
# Usage : ./scripts/ha/init-standby.sh [IP_SOURCE]   (défaut : l'IP virtuelle = le primaire actuel)
#  - mise en place : sur qafila-node2, après ./install.sh sur qafila-node1 ;
#  - après une bascule : sur l'ancien primaire (clôturé), pour le réintégrer comme réplique.
# La réplique suit l'IP virtuelle (primary_conninfo host=VIP) : après une bascule elle n'a pas
# besoin d'être reconfigurée. ⚠ Efface la base locale (elle est recopiée depuis le primaire).
set -euo pipefail
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
SOURCE="${1:-$VIP}"
SLOT="qafila_$(hostname -s | tr -c 'a-z0-9\n' '_')"
PG_IMAGE=docker.io/library/postgres:16-alpine
psql_src() { podman run --rm --network host -e PGPASSWORD="$POSTGRES_PASSWORD" -e PGCONNECT_TIMEOUT=5 \
               "$PG_IMAGE" psql -h "$SOURCE" -U "$POSTGRES_USER" -d postgres -XtAc "$1"; }

if [[ "$SOURCE" == "$VIP" ]] && ip -o -4 addr show | grep -q " $VIP/"; then
  echo "Ce nœud porte l'IP virtuelle : c'est lui le primaire, il ne peut pas devenir réplique."; exit 1
fi
[[ $(psql_src "select pg_is_in_recovery()" 2>/dev/null) == f ]] || {
  echo "Aucun primaire PostgreSQL joignable sur $SOURCE."; exit 1; }

read -r -p "Effacer la base locale et la recopier depuis $SOURCE ? (oui/non) " ok
[[ "$ok" == oui ]] || { echo "Annulé."; exit 1; }

podman rm -f qafila-db >/dev/null 2>&1 || true
podman volume rm -f qafila_qafila-pg >/dev/null 2>&1 || true
podman volume create qafila_qafila-pg >/dev/null

# Réintégration répétée : l'ancien emplacement de réplication du même nom est supprimé
psql_src "select pg_drop_replication_slot('$SLOT') from pg_replication_slots where slot_name='$SLOT' and not active" >/dev/null

echo "Copie de base depuis $SOURCE (pg_basebackup)…"
podman run --rm --network host -e PGPASSWORD="$REPLICATION_PASSWORD" \
  -v qafila_qafila-pg:/var/lib/postgresql/data:Z "$PG_IMAGE" \
  sh -c "pg_basebackup -h $SOURCE -U replicator -D /var/lib/postgresql/data -R -X stream -C -S $SLOT -P \
         && chown -R postgres:postgres /var/lib/postgresql/data && chmod 700 /var/lib/postgresql/data"
echo "✔ Réplique initialisée (standby.signal, suit $SOURCE). Lancez maintenant ./install.sh"
echo "  Une éventuelle clôture de ce nœud est levée automatiquement dès que la réplique tourne."
