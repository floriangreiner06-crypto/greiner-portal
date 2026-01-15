#!/bin/bash
# Mount-Script für Stellantis Garantie-Verzeichnis
# TAG 189: Erstellt für Stellantis (Opel) Garantieaufträge

MOUNT_POINT="/mnt/stellantis-garantie"
WINDOWS_PATH="//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie"
CREDENTIALS_FILE="/root/.smbcredentials"
DOMAIN="auto-greiner.de"

echo "=========================================="
echo "Mount Stellantis Garantie-Verzeichnis"
echo "=========================================="
echo ""

# Prüfe ob Mount-Punkt bereits existiert
if [ -d "$MOUNT_POINT" ]; then
    echo "✅ Mount-Punkt existiert bereits: $MOUNT_POINT"
    
    # Prüfe ob bereits gemountet
    if mountpoint -q "$MOUNT_POINT"; then
        echo "⚠️  Bereits gemountet!"
        echo "   Zum Unmounten: sudo umount $MOUNT_POINT"
        exit 0
    fi
else
    echo "📁 Erstelle Mount-Punkt: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
    if [ $? -ne 0 ]; then
        echo "❌ Fehler beim Erstellen des Mount-Punkts"
        exit 1
    fi
fi

# Prüfe ob Credentials-Datei existiert
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Credentials-Datei nicht gefunden: $CREDENTIALS_FILE"
    echo "   Bitte erstelle die Datei mit:"
    echo "   username=..."
    echo "   password=..."
    exit 1
fi

echo "🔌 Mounte Stellantis Garantie-Verzeichnis..."
echo "   Von: $WINDOWS_PATH"
echo "   Nach: $MOUNT_POINT"
echo ""

sudo mount -t cifs "$WINDOWS_PATH" "$MOUNT_POINT" \
    -o credentials="$CREDENTIALS_FILE",domain="$DOMAIN",vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775

if [ $? -eq 0 ]; then
    echo "✅ Erfolgreich gemountet!"
    echo ""
    echo "📋 Nächste Schritte:"
    echo "   1. Füge zu /etc/fstab hinzu für automatisches Mounten:"
    echo "      $WINDOWS_PATH $MOUNT_POINT cifs credentials=$CREDENTIALS_FILE,domain=$DOMAIN,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0"
    echo ""
    echo "   2. Teste Schreibrechte:"
    echo "      touch $MOUNT_POINT/test.txt && rm $MOUNT_POINT/test.txt && echo '✅ OK'"
else
    echo "❌ Fehler beim Mounten!"
    echo "   Prüfe:"
    echo "   - Netzwerk-Verbindung zu srvrdb01"
    echo "   - Windows-Berechtigungen für $WINDOWS_PATH"
    echo "   - Credentials-Datei: $CREDENTIALS_FILE"
    exit 1
fi
