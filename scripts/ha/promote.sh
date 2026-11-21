#!/usr/bin/env bash
# Qafila — appelé par keepalived (notify_master) quand ce nœud récupère l'IP virtuelle.
# Installé par node-setup.sh en /usr/libexec/keepalived/qafila-promote.
# Si la base locale est une réplique, elle est promue en primaire : Odoo (qui passe par la VIP)
# reprend l'écriture sur ce nœud. Lancement manuel possible : sudo /usr/libexec/keepalived/qafila-promote
set -uo pipefail
source "${QAFILA_HA_ENV:-/etc/qafila/ha.env}"
export PGPASSWORD=$POSTGRES_PASSWORD PGCONNECT_TIMEOUT=3
q() { ${QAFILA_PSQL:-psql} -h "${LOCAL_DB_HOST:-127.0.0.1}" -p "${LOCAL_DB_PORT:-5432}" \
        -U "$POSTGRES_USER" -d postgres -XtAc "$1" 2>/dev/null | tr -d '[:space:]'; }

if [[ $(q "select pg_is_in_recovery()") == t ]]; then
  if [[ $(q "select pg_promote(true, 30)") == t ]]; then
    logger -t qafila-ha "Base promue en PRIMAIRE sur $(hostname) (bascule)"
    echo "✔ Base promue en primaire."
  else
    logger -t qafila-ha "ÉCHEC de la promotion de la base sur $(hostname)"
    echo "✘ Échec de la promotion." >&2; exit 1
  fi
else
  logger -t qafila-ha "$(hostname) maître VRRP ; base déjà primaire (rien à faire)"
  echo "Base déjà primaire."
fi
