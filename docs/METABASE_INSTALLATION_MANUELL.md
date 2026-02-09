# Metabase Installation - Manuelle Ausführung

Da die Installation sudo-Rechte benötigt, muss sie manuell ausgeführt werden.

## Schnellstart

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_safe.sh
```

Das Skript führt automatisch aus:
1. ✅ Backup des aktuellen Zustands
2. ✅ Installation von Java (falls nötig)
3. ✅ Download und Installation von Metabase
4. ✅ Service-Erstellung und Start
5. ✅ Verifikation

## Bei Problemen - Rollback

Falls etwas schief geht, können Sie jederzeit zurücksetzen:

```bash
# Finde das neueste Backup
BACKUP_DIR=$(ls -td /opt/greiner-portal/backups/metabase_* | head -1)

# Führe Rollback aus
sudo bash /opt/greiner-portal/scripts/metabase_rollback.sh $BACKUP_DIR
```

## Alternative: Schrittweise Installation

Falls Sie die Installation Schritt für Schritt durchführen möchten:

### Schritt 1: Backup
```bash
bash /opt/greiner-portal/scripts/metabase_backup.sh
```

### Schritt 2: Installation
```bash
sudo bash /opt/greiner-portal/scripts/install_metabase_jar.sh
```

### Schritt 3: Verifikation
```bash
# Warte 30-60 Sekunden, dann:
sudo systemctl status metabase
sudo journalctl -u metabase -f
```

## Nach der Installation

1. **Öffne Browser:** http://10.80.80.20:3001 (Grafana läuft auf Port 3000)
2. **Erstelle Admin-Account**
3. **Verbinde Datenbank:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `drive_portal`
   - User: `drive_user`
   - Password: [aus DB-Konfiguration]

## Troubleshooting

### Installation schlägt fehl

```bash
# Prüfe Logs
sudo journalctl -u metabase -n 50

# Prüfe Java
java -version

# Prüfe Port
sudo netstat -tlnp | grep 3001
```

### Rollback durchführen

```bash
# Liste verfügbare Backups
ls -ltr /opt/greiner-portal/backups/metabase_*

# Rollback mit neuestem Backup
BACKUP_DIR=$(ls -td /opt/greiner-portal/backups/metabase_* | head -1)
sudo bash /opt/greiner-portal/scripts/metabase_rollback.sh $BACKUP_DIR
```

### Metabase startet nicht

```bash
# Prüfe Service-Status
sudo systemctl status metabase

# Prüfe Logs
sudo journalctl -u metabase -f

# Starte manuell
sudo systemctl start metabase
```

### Port 3001 bereits belegt

```bash
# Prüfe was auf Port 3001 läuft
sudo netstat -tlnp | grep 3001

# Falls nötig, ändere Port in /etc/systemd/system/metabase.service
# Ändere: Environment="MB_JETTY_PORT=3002" (oder anderer freier Port)
# Dann: sudo systemctl daemon-reload && sudo systemctl restart metabase
```

## Deinstallation (komplett)

```bash
# Stoppe Service
sudo systemctl stop metabase
sudo systemctl disable metabase

# Entferne Service
sudo rm /etc/systemd/system/metabase.service
sudo systemctl daemon-reload

# Entferne Verzeichnis
sudo rm -rf /opt/metabase

# Prüfe ob alles entfernt
systemctl status metabase  # sollte "not found" sein
ls -la /opt/metabase       # sollte "not found" sein
```
