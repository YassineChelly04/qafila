#!/usr/bin/env bash
# Qafila — état du cluster vu depuis ce nœud (pratique pendant la soutenance)
set -uo pipefail
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
sql() { podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -XtAc "$1" 2>/dev/null; }

echo "Nœud           : $(hostname)  (rôle d'installation : $QAFILA_ROLE)"
if ip -o -4 addr show | grep -q " $VIP/"; then echo "IP virtuelle   : $VIP ✔ portée par CE nœud"
else echo "IP virtuelle   : $VIP (portée par l'autre nœud)"; fi
echo "keepalived     : $(systemctl is-active keepalived 2>/dev/null)"
[[ -f /var/lib/qafila/fenced ]] && echo "⚠ CLÔTURÉ depuis $(cat /var/lib/qafila/fenced) : ./scripts/ha/init-standby.sh pour réintégrer"

role=$(sql "select case when pg_is_in_recovery() then 'RÉPLIQUE' else 'PRIMAIRE' end")
echo "PostgreSQL     : ${role:-arrêté}  (timeline $(sql "select timeline_id from pg_control_checkpoint()"))"
[[ $role == RÉPLIQUE ]] && echo "  reçoit de     : $(sql "select sender_host||' ('||status||')' from pg_stat_wal_receiver")" \
  && echo "  retard        : $(sql "select coalesce(now()-pg_last_xact_replay_timestamp(), '0')::interval(0)")"
sql "select '  réplique connectée : '||client_addr||' ('||state||', retard '||coalesce(replay_lag::text,'0')||')' from pg_stat_replication"
for ip in "$NODE1_IP" "$NODE2_IP"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://$ip:8069/web/health")
  echo "Odoo $ip : $([[ $code == 200 ]] && echo 'en ligne ✔' || echo "hors ligne ($code)")"
done
podman ps --format '  {{.Names}}\t{{.Status}}'
