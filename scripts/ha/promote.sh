#!/usr/bin/env bash
# Qafila — appelé par keepalived (notify_master) quand ce nœud récupère l'IP virtuelle.
# Si la base locale est une réplique, elle est promue en primaire : Odoo (via la VIP) reprend l'écriture.
# Peut aussi être lancé à la main lors de la démonstration de bascule.
set -uo pipefail
source /etc/sysconfig/qafila 2>/dev/null || QAFILA_USER=$(id -un)
cd "$(dirname "$0")/../.."
set -a; source .env; set +a

as_user() { if [[ $EUID -eq 0 ]]; then runuser -l "$QAFILA_USER" -c "$*"; else bash -c "$*"; fi; }
in_recovery=$(as_user "podman exec qafila-db psql -U $POSTGRES_USER -d postgres -tAc 'select pg_is_in_recovery()'" 2>/dev/null | tr -d '[:space:]')

if [[ "$in_recovery" == "t" ]]; then
  as_user "podman exec qafila-db psql -U $POSTGRES_USER -d postgres -tAc 'select pg_promote()'"
  logger -t qafila-ha "Base promue en PRIMAIRE sur $(hostname) (bascule)"
  echo "✔ Base promue en primaire."
else
  logger -t qafila-ha "$(hostname) maître VRRP ; base déjà primaire (rien à faire)"
  echo "Base déjà primaire."
fi
