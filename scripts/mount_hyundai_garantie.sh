#!/bin/bash
# Mount-Script für Hyundai Garantie-Verzeichnis
# TAG 173: Separater Mount-Punkt für \\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie

MOUNT_POINT="/mnt/hyundai-garantie"
SHARE="//srvrdb01/Allgemein/DigitalesAutohaus/Hyundai_Garantie"

# Erstelle Mount-Punkt falls nicht vorhanden
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Erstelle Mount-Punkt: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
fi

# Prüfe ob bereits gemountet
if mountpoint -q "$MOUNT_POINT"; then
    echo "✅ $MOUNT_POINT ist bereits gemountet"
    exit 0
fi

# Mount mit Credentials
echo "Mounte $SHARE nach $MOUNT_POINT..."
sudo mount -t cifs "$SHARE" "$MOUNT_POINT" \
    -o credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775

if [ $? -eq 0 ]; then
    echo "✅ Mount erfolgreich!"
    echo "   Linux: $MOUNT_POINT"
    echo "   Windows: \\\\srvrdb01\\Allgemein\\DigitalesAutohaus\\Hyundai_Garantie"
    
    # Test Schreibrechte
    if touch "$MOUNT_POINT/.test_write" 2>/dev/null; then
        rm -f "$MOUNT_POINT/.test_write"
        echo "✅ Schreibrechte OK!"
    else
        echo "⚠️  Schreibrechte prüfen!"
    fi
else
    echo "❌ Mount fehlgeschlagen!"
    exit 1
fi
