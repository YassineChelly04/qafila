#!/usr/bin/env bash
# Qafila — réglages système nécessitant root (à lancer UNE fois) : sudo ./scripts/sudo-setup.sh [IP]
#  1. domaines locaux qafila.tn / erp.qafila.tn dans /etc/hosts (aucun achat de domaine)
#  2. approbation du certificat racine local de Caddy (plus d'alerte HTTPS)
#  3. pare-feu : HTTP/HTTPS ouverts
# IP par défaut : 127.0.0.1 (pile mono-hôte). Sur un poste client du cluster HA : l'IP virtuelle (VIP).
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $EUID -eq 0 ]] || { echo "À lancer avec sudo."; exit 1; }

IP="${1:-127.0.0.1}"
HOSTS_LINE="$IP qafila.tn www.qafila.tn erp.qafila.tn"

# 1. /etc/hosts — on retire les anciennes entrées (Nexora, Qafila) puis on ajoute la nouvelle
cp /etc/hosts "/etc/hosts.bak.$(date +%Y%m%d%H%M%S)"
sed -i -E '/[[:space:]](nexora\.com|qafila\.tn|www\.qafila\.tn|erp\.qafila\.tn)([[:space:]]|$)/d' /etc/hosts
echo "$HOSTS_LINE" >> /etc/hosts
echo "✔ /etc/hosts : $HOSTS_LINE"

# 2. Autorité de certification locale (exportée par install.sh)
if [[ -f config/caddy-root.crt ]]; then
  install -m 0644 config/caddy-root.crt /etc/pki/ca-trust/source/anchors/qafila-caddy-root.crt
  update-ca-trust extract
  echo "✔ Certificat racine Qafila approuvé (Firefox/Chromium du système l'utilisent via p11-kit)"
else
  echo "⚠ config/caddy-root.crt absent : lancez d'abord ./install.sh"
fi

# 3. Pare-feu
if systemctl is-active --quiet firewalld; then
  firewall-cmd --permanent --add-service=http --add-service=https >/dev/null
  firewall-cmd --reload >/dev/null
  echo "✔ firewalld : http/https autorisés"
fi

echo "Ouvrez https://qafila.tn et https://erp.qafila.tn (redémarrez le navigateur s'il était ouvert)."
