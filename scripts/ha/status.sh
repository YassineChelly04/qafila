#!/usr/bin/env bash
# Qafila — état du cluster vu depuis ce nœud (pratique pendant la soutenance)
set -uo pipefail
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
echo "Nœud           : $(hostname)  (rôle configuré : $QAFILA_ROLE)"
ip -o -4 addr show | grep -q " $VIP/" && echo "IP virtuelle   : $VIP ✔ portée par CE nœud" || echo "IP virtuelle   : $VIP (portée par l'autre nœud)"
role=$(podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc "select case when pg_is_in_recovery() then 'SECOURS (réplique)' else 'PRIMAIRE' end" 2>/dev/null)
echo "PostgreSQL     : ${role:-arrêté}"
podman exec qafila-db psql -U "$POSTGRES_USER" -d postgres -tAc \
  "select '  réplique connectée : '||client_addr||' ('||state||', retard '||coalesce(replay_lag::text,'0')||')' from pg_stat_replication" 2>/dev/null
for ip in "$NODE1_IP" "$NODE2_IP"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://$ip:8069/web/health")
  echo "Odoo $ip : $([[ $code == 200 ]] && echo 'en ligne ✔' || echo "hors ligne ($code)")"
done
podman ps --format '  {{.Names}}\t{{.Status}}'
