#!/bin/bash
# Mount des Locosoft-Stammverzeichnisses \\10.80.80.7\Loco (bzw. //srvloco01/Loco)
# Voraussetzung: AD-Dienstuser (svc_portal) hat am Locosoft-Server Freigabe für Loco erhalten.
# Credentials: /root/.smbcredentials (wie bei loco-bilder, loco-teilelieferscheine)
# Mit sudo ausführen: sudo bash scripts/mount_loco_stamm.sh

set -e
MOUNT_POINT="/mnt/loco"
SHARE="//srvloco01/Loco"
OPTS="credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0664,dir_mode=0775,nofail"

if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT"
    chown 1000:1000 "$MOUNT_POINT" 2>/dev/null || true
fi

if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    echo "$MOUNT_POINT ist bereits gemountet."
    ls -la "$MOUNT_POINT" | head -20
    exit 0
fi

echo "Mounte $SHARE nach $MOUNT_POINT ..."
mount -t cifs "$SHARE" "$MOUNT_POINT" -o "$OPTS"
echo "OK. Inhalt (erste 25 Einträge):"
ls -la "$MOUNT_POINT" | head -25

echo ""
echo "Für dauerhaften Mount in /etc/fstab eintragen:"
echo "//srvloco01/Loco $MOUNT_POINT cifs $OPTS 0 0"
