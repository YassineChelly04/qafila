#!/usr/bin/env bash
# Qafila — préparation système d'un nœud HA (root) : sudo ./scripts/ha/node-setup.sh
# Prérequis : VM clonée depuis le modèle durci, .env rempli (NODE1_IP, NODE2_IP, VIP, QAFILA_ROLE).
#  - installe keepalived et génère sa configuration (IP virtuelle VRRP)
#  - pare-feu : VRRP + PostgreSQL/Odoo ouverts uniquement au nœud pair
#  - /etc/hosts : qafila.tn et erp.qafila.tn → IP virtuelle
set -euo pipefail
cd "$(dirname "$0")/../.."
[[ $EUID -eq 0 ]] || { echo "À lancer avec sudo."; exit 1; }
set -a; source .env; set +a
PROJECT_DIR="$PWD"

case "$QAFILA_ROLE" in
  primary) SELF=$NODE1_IP; PEER=$NODE2_IP; STATE=MASTER; PRIO=150; NAME=qafila-node1 ;;
  standby) SELF=$NODE2_IP; PEER=$NODE1_IP; STATE=BACKUP; PRIO=100; NAME=qafila-node2 ;;
  *) echo "QAFILA_ROLE doit valoir primary ou standby dans .env"; exit 1 ;;
esac
IFACE=$(ip -o -4 addr show | awk -v ip="$SELF" '$4 ~ "^"ip"/" {print $2; exit}')
[[ -n "$IFACE" ]] || { echo "Aucune interface ne porte l'adresse $SELF : vérifiez NODE1_IP/NODE2_IP."; exit 1; }

hostnamectl set-hostname "$NAME"
dnf -y install keepalived

sed -e "s/__ROUTER_ID__/$NAME/; s/__STATE__/$STATE/; s/__PRIORITY__/$PRIO/" \
    -e "s/__IFACE__/$IFACE/g; s/__SELF_IP__/$SELF/; s/__PEER_IP__/$PEER/; s/__VIP__/$VIP/" \
    -e "s/__VRRP_PASSWORD__/$VRRP_PASSWORD/; s#__PROJECT_DIR__#$PROJECT_DIR#" \
    config/ha/keepalived.conf.tmpl > /etc/keepalived/keepalived.conf
chmod 600 /etc/keepalived/keepalived.conf
# Le script de promotion appelle podman en tant que propriétaire du projet
echo "QAFILA_USER=${SUDO_USER:-$(stat -c %U "$PROJECT_DIR")}" > /etc/sysconfig/qafila
systemctl enable --now keepalived
systemctl restart keepalived

firewall-cmd --permanent --add-service=http --add-service=https >/dev/null
firewall-cmd --permanent --add-rich-rule="rule protocol value=\"vrrp\" accept" >/dev/null
for port in 5432 8069; do
  firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$PEER/32 port port=$port protocol=tcp accept" >/dev/null
done
firewall-cmd --reload >/dev/null

sed -i -E '/[[:space:]](nexora\.com|qafila\.tn|www\.qafila\.tn|erp\.qafila\.tn)([[:space:]]|$)/d' /etc/hosts
echo "$VIP qafila.tn www.qafila.tn erp.qafila.tn" >> /etc/hosts

echo "✔ $NAME prêt : keepalived ($STATE, priorité $PRIO, interface $IFACE), IP virtuelle $VIP"
echo "  Suite : en tant qu'utilisateur → ./install.sh"
[[ "$QAFILA_ROLE" == standby ]] && echo "  (node2 : d'abord ./scripts/ha/init-standby.sh, une fois le nœud 1 installé)"
exit 0
