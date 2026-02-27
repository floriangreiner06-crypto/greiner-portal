#!/bin/bash
# Fügt den Buchhaltung-Mount in /etc/fstab ein (falls noch nicht vorhanden).
# Ausführen: sudo bash /opt/greiner-portal/scripts/add_fstab_buchhaltung.sh

FSTAB=/etc/fstab
LINE='//srvrdb01/Allgemein /mnt/buchhaltung cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=0,gid=0,nofail 0 0'

if grep -q '/mnt/buchhaltung' "$FSTAB"; then
  echo "Buchhaltung ist bereits in der fstab."
else
  echo "$LINE" >> "$FSTAB"
  echo "Buchhaltung-Zeile wurde angehängt."
fi

echo "Mountpunkt erstellen (falls nötig): sudo mkdir -p /mnt/buchhaltung"
echo "Jetzt mounten: sudo mount /mnt/buchhaltung"
echo "Prüfen: mount | grep buchhaltung"
