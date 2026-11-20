#!/usr/bin/env bash
# Qafila — sauvegarde de la base (pièces jointes incluses : ir_attachment.location = db)
# Usage : ./scripts/backup.sh            → backups/qafila-AAAAMMJJ-HHMM.dump(.gpg)
#         ./scripts/backup.sh restore F  → restaure le fichier F (ARRÊTE Odoo pendant l'opération)
# Chiffrement : si BACKUP_PASSPHRASE est défini dans .env, le dump est chiffré (gpg AES256).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
mkdir -p backups && chmod 700 backups
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

if [[ "${1:-}" == "restore" ]]; then
  file="${2:?Fichier de sauvegarde attendu}"
  podman stop qafila-odoo-1 qafila-odoo-2 >/dev/null
  if [[ "$file" == *.gpg ]]; then
    gpg --batch --quiet --passphrase "$BACKUP_PASSPHRASE" --decrypt "$file"
  else
    cat "$file"
  fi | podman exec -i qafila-db pg_restore -U "$POSTGRES_USER" -d "$ODOO_DB" --clean --if-exists --no-owner
  podman start qafila-odoo-1 qafila-odoo-2 >/dev/null
  echo "✔ Restauration terminée depuis $file"
  exit 0
fi

out="backups/${ODOO_DB}-$(date +%Y%m%d-%H%M).dump"
podman exec qafila-db pg_dump -U "$POSTGRES_USER" -Fc "$ODOO_DB" > "$out"
if [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
  gpg --batch --yes --quiet --symmetric --cipher-algo AES256 --passphrase "$BACKUP_PASSPHRASE" -o "$out.gpg" "$out"
  rm -f "$out"; out="$out.gpg"
fi
chmod 600 "$out"
find backups -name "${ODOO_DB}-*.dump*" -mtime +"$KEEP_DAYS" -delete
echo "✔ Sauvegarde : $out ($(du -h "$out" | cut -f1)). Copiez-la hors de cette machine."
