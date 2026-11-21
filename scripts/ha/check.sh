#!/usr/bin/env bash
# Qafila — contrôle de santé appelé par keepalived toutes les 5 s.
# Installé par node-setup.sh en /usr/libexec/keepalived/qafila-check (chemin autorisé par SELinux,
# propriétaire root : keepalived refuse d'exécuter en root un script modifiable par un utilisateur).
#
# Code 0 = ce nœud peut porter l'IP virtuelle. Sinon keepalived le passe en FAULT et libère la VIP.
#  1. PostgreSQL local doit répondre.
#  2. Clôture (fencing) : si la base locale est PRIMAIRE alors que la VIP est portée par l'autre nœud
#     et que la base derrière la VIP est elle aussi primaire, la base locale est une ancienne primaire
#     périmée (l'autre nœud a été promu pendant notre panne). On l'arrête et on la marque « clôturée »
#     pour qu'elle ne reprenne jamais la VIP avec des données anciennes. Réintégration : init-standby.sh.
#  3. Caddy local doit répondre sur https://erp…/web/health (quel que soit l'état d'Odoo).
set -uo pipefail
source "${QAFILA_HA_ENV:-/etc/qafila/ha.env}"
STATE_DIR=${QAFILA_STATE_DIR:-/var/lib/qafila}
FENCE=$STATE_DIR/fenced
export PGPASSWORD=$POSTGRES_PASSWORD PGCONNECT_TIMEOUT=2

db_role() {  # $1 hôte, $2 port → primary | standby | down
  local r
  r=$(${QAFILA_PSQL:-psql} -h "$1" -p "${2:-5432}" -U "$POSTGRES_USER" -d postgres -XtAc \
      "select pg_is_in_recovery()" 2>/dev/null | tr -d '[:space:]')
  case $r in f) echo primary ;; t) echo standby ;; *) echo down ;; esac
}
has_vip() {
  [[ -n ${LAB_HAS_VIP:-} ]] && { [[ $LAB_HAS_VIP == 1 ]]; return; }   # banc d'essai (lab-test.sh)
  ip -o -4 addr show | grep -q " $VIP/"
}
as_user() {  # les conteneurs sont rootless : on agit en tant que propriétaire du projet
  if [[ $EUID -eq 0 ]]; then
    runuser -u "$QAFILA_USER" -- env XDG_RUNTIME_DIR="/run/user/$(id -u "$QAFILA_USER")" "$@"
  else "$@"; fi
}
fence() {
  mkdir -p "$STATE_DIR"; date -Is > "$FENCE"; chmod 644 "$FENCE"
  logger -t qafila-ha "CLÔTURE de la base locale sur $(hostname) : primaire périmée, la VIP est servie par l'autre nœud. Réintégration : scripts/ha/init-standby.sh"
  as_user podman stop -t 10 "${DB_CONTAINER:-qafila-db}" >/dev/null 2>&1
}

case $(db_role "${LOCAL_DB_HOST:-127.0.0.1}" "${LOCAL_DB_PORT:-5432}") in
  down) exit 1 ;;
  standby) rm -f "$FENCE" ;;   # base reconstruite en réplique : la clôture est levée
  primary)
    [[ -f $FENCE ]] && exit 1
    if ! has_vip && [[ $(db_role "$VIP" "${VIP_DB_PORT:-5432}") == primary ]]; then
      fence; exit 1
    fi ;;
esac

# Caddy doit répondre (n'importe quel code HTTP). On n'exige PAS qu'Odoo réponde :
#  - Odoo joint la base via l'IP virtuelle → au premier démarrage il attend la VIP, qui
#    attendrait Odoo : interblocage ;
#  - Caddy répartit déjà sur les Odoo des DEUX nœuds : un Odoo en panne est contourné sans bascule.
# On interroge /caddy-health, servi par Caddy lui-même : /web/health passerait par Odoo, et sans
# Odoo joignable Caddy retente pendant lb_try_duration (10 s) → curl (2 s) expirerait → faux échec.
if [[ ${CHECK_HTTP:-1} == 1 ]]; then
  curl -skf -o /dev/null --max-time 2 --resolve "$QAFILA_ERP_DOMAIN:443:127.0.0.1" \
    "https://$QAFILA_ERP_DOMAIN/caddy-health" || exit 1
fi
exit 0
