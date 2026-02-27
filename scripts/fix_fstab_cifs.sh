#!/bin/bash
# Korrigiert Leerzeichen in CIFS-Pfaden in /etc/fstab (\ -> \040)
# Ausführen: sudo bash /opt/greiner-portal/scripts/fix_fstab_cifs.sh

set -e
FSTAB=/etc/fstab

if [ ! -w "$FSTAB" ]; then
  echo "Bitte mit sudo ausführen: sudo bash $0"
  exit 1
fi

# Backup
cp -a "$FSTAB" "${FSTAB}.bak.$(date +%Y%m%d%H%M%S)"

# Zeile 1: Greiner\ Portal -> Greiner\040Portal
sed -i 's|Greiner\\ Portal|Greiner\\040Portal|g' "$FSTAB"

# Zeile 2: Teilelieferscheine\ -\ XQ0093 -> Teilelieferscheine\040-\040XQ0093
sed -i 's|Teilelieferscheine\\ \\-\\ XQ0093|Teilelieferscheine\\040-\\040XQ0093|g' "$FSTAB"

echo "fstab angepasst. Prüfe mit: mount -a"
