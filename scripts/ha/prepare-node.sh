#!/usr/bin/env bash
# Qafila — prépare UN nœud HA (à lancer en utilisateur normal, pas en root) :
#   ./scripts/ha/prepare-node.sh primary NODE1_IP NODE2_IP VIP     (sur la VM 1)
#   ./scripts/ha/prepare-node.sh standby NODE1_IP NODE2_IP VIP     (sur la VM 2)
# Exemple : ./scripts/ha/prepare-node.sh primary 192.168.1.241 192.168.1.242 192.168.1.240
#
#  - fixe l'adresse IP du nœud (statique, via NetworkManager) pour qu'elle ne change plus ;
#  - primary : crée .env (secrets aléatoires, rôle primary) ;
#  - standby : récupère le .env du nœud 1 par scp (mêmes mots de passe), rôle standby ;
#  - n'installe rien d'autre : la suite est affichée à la fin.
# Option : --no-static  → ne touche pas à la configuration réseau.
set -euo pipefail
cd "$(dirname "$0")/../.."

STATIC=1
ARGS=()
for a in "$@"; do [[ "$a" == --no-static ]] && STATIC=0 || ARGS+=("$a"); done
set -- "${ARGS[@]}"
[[ $# -eq 4 ]] || { sed -n '2,11p' "$0"; exit 1; }
ROLE=$1; N1=$2; N2=$3; VIP=$4
[[ $EUID -ne 0 ]] || { echo "Lancez ce script en utilisateur normal (il appelle sudo si besoin)."; exit 1; }

valid_ip() { [[ $1 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; }
for ip in "$N1" "$N2" "$VIP"; do valid_ip "$ip" || { echo "Adresse invalide : $ip"; exit 1; }; done
[[ "$N1" != "$N2" && "$N1" != "$VIP" && "$N2" != "$VIP" ]] || { echo "Les 3 adresses doivent être différentes."; exit 1; }
case "$ROLE" in
  primary) SELF=$N1 ;;
  standby) SELF=$N2 ;;
  *) echo "Rôle : primary ou standby."; exit 1 ;;
esac
say() { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
setkey() { if grep -q "^$1=" .env; then sed -i "s|^$1=.*|$1=$2|" .env; else echo "$1=$2" >> .env; fi; }
ip2int() { local IFS=.; set -- $1; echo $(( ($1<<24) + ($2<<16) + ($3<<8) + $4 )); }
same_net() { local m=$(( (0xFFFFFFFF << (32-PREFIX)) & 0xFFFFFFFF )); (( ($(ip2int "$1") & m) == ($(ip2int "$2") & m) )); }

# Réseau actuel (DHCP) : interface, passerelle, taille du réseau (/24 box, /28 partage iPhone…)
IFACE=$(ip -o -4 route show default | awk '{print $5; exit}')
GW=$(ip -o -4 route show default | awk '{print $3; exit}')
[[ -n "$IFACE" && -n "$GW" ]] || { echo "Aucune route par défaut : la VM n'a pas de réseau (voir mode pont/NAT de la VM)."; exit 1; }
PREFIX=$(ip -o -4 addr show dev "$IFACE" | awk '{split($4,a,"/"); print a[2]; exit}')
[[ -n "$PREFIX" ]] || PREFIX=24
for ip in "$N1" "$N2" "$VIP"; do
  same_net "$ip" "$GW" || { echo "$ip n'est pas dans le réseau de la passerelle $GW/$PREFIX. Vérifiez les adresses (ip -4 addr)."; exit 1; }
done

# 1. Adresse IP statique -------------------------------------------------------
if [[ $STATIC == 1 ]]; then
  CON=$(nmcli -g GENERAL.CONNECTION device show "$IFACE")
  [[ -n "$CON" ]] || { echo "Connexion NetworkManager introuvable pour $IFACE."; exit 1; }
  say "Adresse statique $SELF/$PREFIX sur $IFACE (connexion « $CON », passerelle $GW)"
  sudo nmcli con mod "$CON" ipv4.method manual ipv4.addresses "$SELF/$PREFIX" ipv4.gateway "$GW" ipv4.dns "$GW 1.1.1.1"
  sudo nmcli con up "$CON" >/dev/null
  sleep 3
fi
ip -o -4 addr show | grep -q " $SELF/" || { echo "L'adresse $SELF n'est pas active sur cette machine."; exit 1; }
if [[ "$ROLE" == primary ]] && ping -c1 -W1 "$VIP" >/dev/null 2>&1; then
  echo "⚠ L'adresse virtuelle $VIP répond déjà au ping : choisissez une adresse libre."; exit 1
fi

# 2. .env ----------------------------------------------------------------------
if [[ "$ROLE" == primary ]]; then
  [[ -f .env ]] || cp .env.example .env
  for key in POSTGRES_PASSWORD ODOO_MASTER_PASSWORD ODOO_ADMIN_PASSWORD ODOO_DEMO_USER_PASSWORD VRRP_PASSWORD REPLICATION_PASSWORD; do
    if ! grep -q "^$key=" .env || grep -q "^$key=.*change-me" .env; then setkey "$key" "$(openssl rand -hex 16)"; fi
  done
else
  # Le nœud 2 doit avoir EXACTEMENT les mêmes mots de passe que le nœud 1
  say "Récupération du .env du nœud 1 ($N1)"
  scp -o StrictHostKeyChecking=accept-new "$USER@$N1:$PWD/.env" .env \
    || { echo "scp a échoué : vérifiez que le nœud 1 est allumé, que sshd tourne et que le projet est au même chemin ($PWD)."; exit 1; }
fi
chmod 600 .env
setkey NODE1_IP "$N1"; setkey NODE2_IP "$N2"; setkey VIP "$VIP"; setkey NET_PREFIX "$PREFIX"; setkey QAFILA_ROLE "$ROLE"

say "Nœud préparé : rôle $ROLE, adresse $SELF (nœuds : $N1 / $N2, IP virtuelle : $VIP)"
if [[ "$ROLE" == primary ]]; then
  echo "  Suite (VM 1) : sudo ./scripts/ha/node-setup.sh   puis   ./install.sh"
  echo "  Mots de passe générés : voir .env (ODOO_ADMIN_PASSWORD, ODOO_DEMO_USER_PASSWORD)"
else
  echo "  Suite (VM 2) : sudo subscription-manager register (si besoin), sudo ./scripts/ha/node-setup.sh,"
  echo "                 ./scripts/ha/init-standby.sh   puis   ./install.sh   (après l'install de la VM 1)"
fi
