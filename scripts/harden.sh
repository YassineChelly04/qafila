#!/usr/bin/env bash
# Qafila — durcissement de l'hôte modèle RHEL 9/10 : sudo ./scripts/harden.sh
# Idempotent. Chaque bloc est commenté pour la soutenance. Relisez avant d'exécuter.
# ⚠ SSH : l'authentification par mot de passe est désactivée → vérifiez d'abord que votre clé
#   publique est dans ~/.ssh/authorized_keys (sinon lancez avec KEEP_SSH_PASSWORD=1).
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "À lancer avec sudo."; exit 1; }
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
step() { printf '\n\033[1;34m▸ %s\033[0m\n' "$*"; }

step "1. Mises à jour de sécurité + mises à jour automatiques"
dnf -y upgrade --security || true
dnf -y install dnf-automatic audit policycoreutils-python-utils firewalld chrony
sed -i 's/^upgrade_type.*/upgrade_type = security/; s/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf
systemctl enable --now dnf-automatic.timer

step "2. SELinux en mode enforcing"
setenforce 1 || true
sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
getenforce

step "3. Pare-feu : uniquement SSH, HTTP, HTTPS"
systemctl enable --now firewalld
firewall-cmd --set-default-zone=public >/dev/null
for svc in $(firewall-cmd --permanent --list-services); do
  case "$svc" in ssh|http|https) ;; *) firewall-cmd --permanent --remove-service="$svc" >/dev/null ;; esac
done
firewall-cmd --permanent --add-service=ssh --add-service=http --add-service=https >/dev/null
firewall-cmd --reload >/dev/null
firewall-cmd --list-services

step "4. SSH : pas de root, clés uniquement, sessions limitées"
cat > /etc/ssh/sshd_config.d/50-qafila-hardening.conf <<EOF
PermitRootLogin no
PasswordAuthentication $([[ "${KEEP_SSH_PASSWORD:-0}" == 1 ]] && echo yes || echo no)
KbdInteractiveAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowAgentForwarding no
EOF
sshd -t && systemctl reload sshd

step "5. Politique de mots de passe et verrouillage"
sed -i 's/^#\? *minlen.*/minlen = 12/; s/^#\? *minclass.*/minclass = 3/' /etc/security/pwquality.conf
authselect current >/dev/null 2>&1 && authselect enable-feature with-faillock >/dev/null 2>&1 || true
sed -i 's/^#\? *deny.*/deny = 5/; s/^#\? *unlock_time.*/unlock_time = 900/' /etc/security/faillock.conf

step "6. Journalisation et audit"
systemctl enable --now auditd chronyd
cat > /etc/audit/rules.d/50-qafila.rules <<'EOF'
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers
-w /etc/ssh/sshd_config -p wa -k sshd
-w /etc/ssh/sshd_config.d/ -p wa -k sshd
EOF
augenrules --load >/dev/null 2>&1 || true

step "7. Noyau : paramètres réseau défensifs"
cat > /etc/sysctl.d/90-qafila.conf <<'EOF'
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.tcp_syncookies = 1
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
# Caddy sans privilèges (Podman rootless) doit écouter sur 80/443
net.ipv4.ip_unprivileged_port_start = 80
EOF
sysctl --system >/dev/null

step "8. Conteneurs : rootless + démarrage au boot sans session ouverte"
loginctl enable-linger "$RUN_USER"
echo "Conteneurs exécutés par l'utilisateur non privilégié : $RUN_USER"

step "9. Services inutiles désactivés"
for svc in cups avahi-daemon bluetooth; do
  systemctl disable --now "$svc" 2>/dev/null && echo "désactivé : $svc" || true
done

step "10. Sauvegarde quotidienne (02:30) via timer systemd utilisateur"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
USER_HOME=$(getent passwd "$RUN_USER" | cut -d: -f6)
install -d -o "$RUN_USER" -g "$RUN_USER" "$USER_HOME/.config/systemd/user"
cat > "$USER_HOME/.config/systemd/user/qafila-backup.service" <<EOF
[Unit]
Description=Sauvegarde Qafila (PostgreSQL)
[Service]
Type=oneshot
ExecStart=$PROJECT_DIR/scripts/backup.sh
EOF
cat > "$USER_HOME/.config/systemd/user/qafila-backup.timer" <<'EOF'
[Unit]
Description=Sauvegarde quotidienne Qafila
[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
[Install]
WantedBy=timers.target
EOF
chown "$RUN_USER:$RUN_USER" "$USER_HOME/.config/systemd/user/qafila-backup."*
echo "Activez-le (en tant que $RUN_USER) : systemctl --user daemon-reload && systemctl --user enable --now qafila-backup.timer"

printf '\n\033[1;32m✔ Durcissement terminé.\033[0m Redémarrage conseillé.\n'
