#!/usr/bin/env bash
# Qafila — attribue à / l'espace ajouté au disque virtuel (à lancer UNE fois) : sudo ./scripts/grow-disk.sh
# Agrandir le disque dans l'hyperviseur ne suffit pas : il faut aussi agrandir
# la partition LVM (nvme0n1p3), le volume physique, puis le volume logique rhel-root (XFS, à chaud).
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "À lancer avec sudo."; exit 1; }

DISK=/dev/nvme0n1
PART=3
PV=${DISK}p${PART}
LV=/dev/rhel/root

echo "Avant :"; df -h /
parted -s "$DISK" ---pretend-input-tty resizepart "$PART" 100% 2>/dev/null \
  || echo Yes | parted "$DISK" ---pretend-input-tty resizepart "$PART" 100%
partprobe "$DISK" 2>/dev/null || true
pvresize "$PV"
lvextend -r -l +100%FREE "$LV" || echo "(aucun espace libre supplémentaire dans le groupe de volumes)"
dnf clean all >/dev/null
journalctl --vacuum-size=100M >/dev/null
echo "Après :"; df -h /
