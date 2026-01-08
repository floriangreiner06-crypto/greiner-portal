# /deploy - Dateien auf Server syncen

Synchronisiere geänderte Dateien vom Windows-Sync-Verzeichnis auf den Linux-Server.

## Anweisungen

1. Prüfe welche Dateien sich geändert haben (git status)
2. Frage den User welche Dateien/Ordner gesynct werden sollen
3. Führe den Sync via SSH aus:
   - Einzelne Dateien: `cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]`
   - Ordner: `rsync -av --exclude '.git' /mnt/greiner-portal-sync/[ordner]/ /opt/greiner-portal/[ordner]/`
4. Bei Python-Änderungen: Frage ob Neustart gewünscht (User muss `sudo systemctl restart greiner-portal` manuell ausführen)
5. Bei Template-Änderungen: Informiere dass nur Browser-Refresh nötig ist

## Server-Details
- Host: 10.80.80.20
- User: ag-admin
- Sync-Quelle: /mnt/greiner-portal-sync/
- Ziel: /opt/greiner-portal/
