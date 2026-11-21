#!/usr/bin/env bash
# Qafila — préparation système d'un nœud HA (root) : sudo ./scripts/ha/node-setup.sh
# Prérequis : VM clonée depuis le modèle durci, .env rempli (NODE1_IP, NODE2_IP, VIP, QAFILA_ROLE).
# À relancer après toute modification de scripts/ha/check.sh ou promote.sh (ils sont recopiés).
#  - installe keepalived + client PostgreSQL, et la configuration VRRP (IP virtuelle)
#  - copie les scripts de contrôle/promotion dans /usr/libexec/keepalived (root, SELinux)
#  - conteneurs rootless relancés au démarrage de la machine (linger + podman-restart)
#  - pare-feu : VRRP + PostgreSQL/Odoo ouverts uniquement au nœud pair
#  - /etc/hosts : qafila.tn et erp.qafila.tn → IP virtuelle
set -euo pipefail
cd "$(dirname "$0")/../.."
[[ $EUID -eq 0 ]] || { echo "À lancer avec sudo."; exit 1; }
set -a; source .env; set +a
PROJECT_DIR="$PWD"
QAFILA_USER="${SUDO_USER:-$(stat -c %U "$PROJECT_DIR")}"

case "$QAFILA_ROLE" in
  primary) SELF=$NODE1_IP; PEER=$NODE2_IP; PRIO=150; NAME=qafila-node1 ;;
  standby) SELF=$NODE2_IP; PEER=$NODE1_IP; PRIO=100; NAME=qafila-node2 ;;
  *) echo "QAFILA_ROLE doit valoir primary ou standby dans .env"; exit 1 ;;
esac
IFACE=$(ip -o -4 addr show | awk -v ip="$SELF" '$4 ~ "^"ip"/" {print $2; exit}')
[[ -n "$IFACE" ]] || { echo "Aucune interface ne porte l'adresse $SELF : vérifiez NODE1_IP/NODE2_IP."; exit 1; }

hostnamectl set-hostname "$NAME"
dnf -y install keepalived postgresql curl >/dev/null

# Paramètres lus par les scripts root (secrets : lisibles par root uniquement)
install -d -m 0700 /etc/qafila
install -d -m 0755 /var/lib/qafila
umask 077
cat > /etc/qafila/ha.env <<EOF
VIP=$VIP
SELF_IP=$SELF
PEER_IP=$PEER
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
QAFILA_ERP_DOMAIN=$QAFILA_ERP_DOMAIN
QAFILA_USER=$QAFILA_USER
EOF
umask 022
install -o root -g root -m 0755 scripts/ha/check.sh   /usr/libexec/keepalived/qafila-check
install -o root -g root -m 0755 scripts/ha/promote.sh /usr/libexec/keepalived/qafila-promote
restorecon -R /usr/libexec/keepalived /etc/qafila /var/lib/qafila 2>/dev/null || true

sed -e "s/__ROUTER_ID__/$NAME/; s/__PRIORITY__/$PRIO/" \
    -e "s/__IFACE__/$IFACE/g; s/__SELF_IP__/$SELF/; s/__PEER_IP__/$PEER/; s/__VIP__/$VIP/; s/__PREFIX__/${NET_PREFIX:-24}/" \
    -e "s/__VRRP_PASSWORD__/$VRRP_PASSWORD/" \
    config/ha/keepalived.conf.tmpl > /etc/keepalived/keepalived.conf
chmod 600 /etc/keepalived/keepalived.conf
rm -f /etc/sysconfig/qafila   # ancienne version
systemctl enable keepalived >/dev/null
systemctl restart keepalived

# Conteneurs rootless relancés au boot, sans session ouverte
loginctl enable-linger "$QAFILA_USER"
systemctl --user -M "$QAFILA_USER@" enable podman-restart.service >/dev/null 2>&1 || \
  echo "⚠ Activez à la main (en tant que $QAFILA_USER) : systemctl --user enable podman-restart.service"

firewall-cmd --permanent --add-service=http --add-service=https >/dev/null
firewall-cmd --permanent --add-rich-rule="rule protocol value=\"vrrp\" accept" >/dev/null
for port in 5432 8069; do
  firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$PEER/32 port port=$port protocol=tcp accept" >/dev/null
done
firewall-cmd --reload >/dev/null

sed -i -E '/[[:space:]](nexora\.com|qafila\.tn|www\.qafila\.tn|erp\.qafila\.tn)([[:space:]]|$)/d' /etc/hosts
echo "$VIP qafila.tn www.qafila.tn erp.qafila.tn" >> /etc/hosts

echo "✔ $NAME prêt : keepalived (priorité $PRIO, interface $IFACE), IP virtuelle $VIP"
if [[ "$QAFILA_ROLE" == primary ]]; then
  echo "  Suite (utilisateur $QAFILA_USER) : ./install.sh"
else
  echo "  Suite (utilisateur $QAFILA_USER), une fois le nœud 1 installé : ./scripts/ha/init-standby.sh puis ./install.sh"
fi
