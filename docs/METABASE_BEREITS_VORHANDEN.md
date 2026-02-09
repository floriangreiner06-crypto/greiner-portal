# Metabase scheint bereits installiert zu sein!

## Status

✅ **Port 3000:** Aktiv und antwortet  
✅ **API Health:** Metabase-ähnliche Antwort (Version 12.3.1)  
❌ **Metabase Service:** Nicht als systemd Service gefunden  
❌ **Metabase Prozess:** Nicht als Java-Prozess gefunden  

## Mögliche Situationen

1. **Metabase läuft in Docker** (nicht als systemd Service)
2. **Metabase läuft als anderer Service** (anderer Name)
3. **Andere Anwendung** die Metabase-API nachahmt

## Nächste Schritte

### Option 1: Metabase bereits nutzen

Falls Metabase bereits läuft:

1. **Öffne:** http://10.80.80.20:3000
2. **Login:** Falls bereits konfiguriert
3. **Datenbank verbinden:** Falls noch nicht geschehen
   - Host: `localhost`
   - Database: `drive_portal`
   - User: `drive_user`

### Option 2: Installation auf Port 3001

Falls Port 3000 von anderer App belegt:

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_safe.sh
```

Das Skript erkennt automatisch, dass Port 3000 belegt ist und verwendet Port 3001.

### Option 3: Bestehende Installation finden

```bash
# Prüfe Docker
docker ps -a | grep -i metabase

# Prüfe alle Java-Prozesse
ps aux | grep java

# Prüfe alle Services
systemctl list-units --all | grep -E "3000|metabase"

# Prüfe Verzeichnisse
ls -la /opt/ | grep -i metabase
ls -la /home/*/metabase
find / -name "metabase.jar" 2>/dev/null
```

## Empfehlung

**Da Port 3000 bereits antwortet:**
1. Prüfe ob es Metabase ist: http://10.80.80.20:3000 öffnen
2. Falls ja → Direkt nutzen, nur DB verbinden
3. Falls nein → Installation auf Port 3001

## Installation trotzdem durchführen?

Falls Sie eine frische Installation auf Port 3001 möchten:

```bash
cd /opt/greiner-portal
sudo bash scripts/install_metabase_safe.sh
```

Das Skript:
- Erstellt Backup
- Installiert auf Port 3001 (da 3000 belegt)
- Ermöglicht Rollback bei Problemen
