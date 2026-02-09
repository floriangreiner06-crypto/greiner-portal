# Metabase Installation Status

## Aktueller Status

**Port 3000:** Bereits belegt (HTTP 302 Redirect zu /login)

**Mögliche Ursachen:**
- Metabase läuft bereits
- Andere Anwendung nutzt Port 3000

## Nächste Schritte

### Option 1: Prüfen ob Metabase bereits läuft

```bash
# Prüfe Prozesse
ps aux | grep -i metabase

# Prüfe Service
systemctl status metabase

# Prüfe Metabase-Verzeichnis
ls -la /opt/metabase
```

Falls Metabase bereits läuft:
- Zugriff: http://10.80.80.20:3000
- Admin-Account vorhanden? → Direkt nutzen
- Kein Account? → Installation überspringen, nur DB verbinden

### Option 2: Installation mit alternativem Port

Das Installationsskript verwendet automatisch Port 3001, falls 3000 belegt ist.

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_safe.sh
```

Dann Zugriff über: http://10.80.80.20:3001

### Option 3: Port 3000 freigeben (falls andere App)

```bash
# Prüfe was auf Port 3000 läuft
sudo lsof -i :3000

# Falls nötig, stoppe die Anwendung
# Dann installiere Metabase auf Port 3000
```

## Empfehlung

1. **Zuerst prüfen:** Ist Metabase bereits installiert?
   ```bash
   systemctl status metabase
   ls -la /opt/metabase
   ```

2. **Falls ja:** Direkt nutzen, nur DB verbinden
3. **Falls nein:** Installation mit Port 3001 durchführen

## Rollback

Falls Installation Probleme macht:

```bash
BACKUP_DIR=$(ls -td /opt/greiner-portal/backups/metabase_* | head -1)
sudo bash /opt/greiner-portal/scripts/metabase_rollback.sh $BACKUP_DIR
```
