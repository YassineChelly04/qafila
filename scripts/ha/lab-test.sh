#!/usr/bin/env bash
# Qafila — banc d'essai de la bascule PostgreSQL sur UNE seule machine (sans sudo, sans 2e VM).
# Usage : ./scripts/ha/lab-test.sh
# Lance deux PostgreSQL jetables en réseau « host » comme en production (« A » port 15432, « B » port 15433) et exécute les VRAIS scripts
# check.sh et promote.sh contre eux. Seuls l'IP virtuelle et keepalived sont simulés.
# Scénario : A primaire → B réplique → panne de A → B promu → A revient (périmé) → A clôturé
#            → A réintégré comme réplique de B → aucune donnée perdue.
set -uo pipefail
cd "$(dirname "$0")/../.."
IMG=docker.io/library/postgres:16-alpine
PW=lab-$RANDOM$RANDOM
LAB=$(mktemp -d); trap 'cleanup' EXIT
ok=0; ko=0
pass() { echo "  ✔ $*"; ok=$((ok+1)); }
fail() { echo "  ✘ $*"; ko=$((ko+1)); }
step() { printf '\n\033[1;34m▸ %s\033[0m\n' "$*"; }
lab_down() { podman rm -f qafila-lab-a qafila-lab-b >/dev/null 2>&1; podman volume rm -f qafila-lab-a qafila-lab-b >/dev/null 2>&1; }
cleanup() { lab_down; rm -rf "$LAB"; }

# psql de l'image officielle (pas de client PostgreSQL requis sur la machine)
cat > "$LAB/psql" <<EOF
#!/usr/bin/env bash
exec podman run --rm --network host -e PGPASSWORD -e PGCONNECT_TIMEOUT $IMG psql "\$@"
EOF
chmod +x "$LAB/psql"
printf 'VIP=127.0.0.2\nPOSTGRES_USER=odoo\nPOSTGRES_PASSWORD=%s\nQAFILA_ERP_DOMAIN=lab\nQAFILA_USER=%s\n' "$PW" "$(id -un)" > "$LAB/ha.env"
export QAFILA_HA_ENV=$LAB/ha.env QAFILA_PSQL=$LAB/psql CHECK_HTTP=0
sql() { PGPASSWORD=$PW "$LAB/psql" -h 127.0.0.1 -p "$1" -U odoo -d postgres -XtAc "$2" 2>/dev/null | tr -d '[:space:]'; }
# check.sh vu depuis un nœud : $1 port local, $2 port derrière la VIP, $3 porte la VIP (0/1), $4 conteneur
check() { LOCAL_DB_PORT=$1 VIP_DB_PORT=$2 LAB_HAS_VIP=$3 DB_CONTAINER=$4 QAFILA_STATE_DIR=$LAB/state-$4 \
            bash scripts/ha/check.sh; }
pg_start() {  # $1 nom, $2 port
  podman run -d --name "qafila-lab-$1" --network host -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD="$PW" \
    -v "qafila-lab-$1:/var/lib/postgresql/data:Z" "$IMG" \
    -c port="$2" -c listen_addresses='127.0.0.1,127.0.0.2' -c wal_level=replica -c max_wal_senders=5 -c wal_keep_size=64MB -c max_slot_wal_keep_size=256MB -c hot_standby=on >/dev/null
  for _ in $(seq 60); do [[ $(sql "$2" "select 1") == 1 ]] && break; sleep 1; done
  # équivalent de install.sh : réplication autorisée (ici depuis toute adresse, banc local)
  podman exec "qafila-lab-$1" sh -c "grep -q '^host replication all all' \$PGDATA/pg_hba.conf || \
    echo 'host replication all all scram-sha-256' >> \$PGDATA/pg_hba.conf"
  sql "$2" "select pg_reload_conf()" >/dev/null
}
basebackup() {  # $1 nom de la nouvelle réplique, $2 port du primaire source
  podman rm -f "qafila-lab-$1" >/dev/null 2>&1; podman volume rm -f "qafila-lab-$1" >/dev/null 2>&1
  podman volume create "qafila-lab-$1" >/dev/null
  sql "$2" "select pg_drop_replication_slot('lab_$1') from pg_replication_slots where slot_name='lab_$1'" >/dev/null
  podman run --rm --network host -e PGPASSWORD="$PW" -v "qafila-lab-$1:/var/lib/postgresql/data:Z" "$IMG" \
    sh -c "pg_basebackup -h 127.0.0.1 -p $2 -U odoo -D /var/lib/postgresql/data -R -X stream -C -S lab_$1 \
           && chown -R postgres:postgres /var/lib/postgresql/data && chmod 700 /var/lib/postgresql/data"
}
wait_row() {  # $1 port, $2 valeur attendue
  for _ in $(seq 20); do [[ $(sql "$1" "select count(*) from colis where ref='$2'") == 1 ]] && return 0; sleep 1; done; return 1
}

lab_down
step "1. A démarre en primaire, B est construite comme réplique de A"
pg_start a 15432
sql 15432 "create table colis(ref text primary key)" >/dev/null
sql 15432 "insert into colis values ('QRD/OUT/00001')" >/dev/null
basebackup b 15432 >/dev/null 2>&1
pg_start b 15433
[[ $(sql 15433 "select pg_is_in_recovery()") == t ]] && pass "B est une réplique" || fail "B n'est pas une réplique"
sql 15432 "insert into colis values ('QRD/OUT/00002')" >/dev/null
wait_row 15433 QRD/OUT/00002 && pass "écriture sur A répliquée sur B en continu" || fail "réplication absente"
check 15432 15432 1 qafila-lab-a && pass "contrôle A (primaire, porte la VIP) : sain" || fail "contrôle A en échec"
check 15433 15432 0 qafila-lab-b && pass "contrôle B (réplique) : sain, prêt à prendre le relais" || fail "contrôle B en échec"
sql 15433 "insert into colis values ('X')" >/dev/null 2>&1; [[ $(sql 15433 "select count(*) from colis where ref='X'") == 0 ]] \
  && pass "B refuse les écritures (lecture seule)" || fail "B accepte des écritures"

step "2. Panne de A : la VIP passe sur B, keepalived lance promote.sh sur B"
podman stop -t 2 qafila-lab-a >/dev/null
check 15432 15433 0 qafila-lab-a; [[ $? != 0 ]] && pass "contrôle A en échec → A libère la VIP" || fail "A toujours déclaré sain"
LOCAL_DB_PORT=15433 bash scripts/ha/promote.sh >/dev/null
[[ $(sql 15433 "select pg_is_in_recovery()") == f ]] && pass "B promue en primaire" || fail "B non promue"
sql 15433 "insert into colis values ('QRD/OUT/00003')" >/dev/null
[[ $(sql 15433 "select count(*) from colis") == 3 ]] && pass "B accepte les écritures (3 expéditions, rien de perdu)" || fail "écriture impossible sur B"

step "3. A redémarre avec son ancienne base primaire (périmée) : elle doit être clôturée"
podman start qafila-lab-a >/dev/null
for _ in $(seq 30); do [[ -n $(sql 15432 "select 1") ]] && break; sleep 1; done
[[ $(sql 15432 "select pg_is_in_recovery()") == f ]] && echo "  (A se croit encore primaire : deux primaires = risque de divergence)"
check 15432 15433 0 qafila-lab-a; [[ $? != 0 ]] && pass "contrôle A refuse la VIP" || fail "A accepterait la VIP avec des données périmées"
[[ -f $LAB/state-qafila-lab-a/fenced ]] && pass "A marquée « clôturée »" || fail "pas de marque de clôture"
[[ $(podman inspect -f '{{.State.Running}}' qafila-lab-a) == false ]] && pass "base de A arrêtée (aucune écriture possible)" || fail "base de A toujours active"
podman start qafila-lab-a >/dev/null; sleep 3
check 15432 15433 0 qafila-lab-a; [[ $? != 0 ]] && pass "relancée à la main, A reste refusée tant qu'elle n'est pas réintégrée" || fail "clôture contournée"

step "4. Réintégration de A comme réplique de B (init-standby.sh)"
basebackup a 15433 >/dev/null 2>&1
pg_start a 15432
[[ $(sql 15432 "select pg_is_in_recovery()") == t ]] && pass "A est maintenant une réplique de B" || fail "A n'est pas réplique"
check 15432 15433 0 qafila-lab-a && pass "contrôle A sain, clôture levée automatiquement" || fail "A toujours en échec"
[[ ! -f $LAB/state-qafila-lab-a/fenced ]] || fail "marque de clôture restée"
sql 15433 "insert into colis values ('QRD/OUT/00004')" >/dev/null
wait_row 15432 QRD/OUT/00004 && pass "les nouvelles écritures sur B arrivent sur A" || fail "réplication B → A absente"
[[ $(sql 15432 "select count(*) from colis") == 4 ]] && pass "A contient les 4 expéditions" || fail "données manquantes sur A"

printf '\n%s réussis, %s échecs\n' "$ok" "$ko"
[[ $ko == 0 ]]
