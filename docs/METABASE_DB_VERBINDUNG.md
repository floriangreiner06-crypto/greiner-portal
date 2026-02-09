# Metabase - PostgreSQL Verbindung

## Verbindungsdaten für Metabase

### Schritt-für-Schritt Anleitung

1. **In Metabase öffnen:** http://10.80.80.20:3001
2. **Login:** admin@auto-greiner.de / Drive2026!
3. **Datenbank hinzufügen:**
   - Klicke auf **"Daten"** (links) → **"Datenbanken"**
   - Klicke auf **"Datenbank hinzufügen"**
   - Wähle **"PostgreSQL"**

4. **Verbindungsdaten eingeben:**

```
Anzeigename: DRIVE Portal
Host: localhost
Port: 5432
Datenbankname: drive_portal
Benutzername: drive_user
Passwort: [siehe unten - aus DB-Konfiguration]
```

### Passwort finden

Das Passwort steht in:
- `/opt/greiner-portal/.env` (falls vorhanden)
- Oder in der PostgreSQL-Konfiguration

**Falls Passwort unbekannt:**
```bash
# Prüfe .env Datei
cat /opt/greiner-portal/.env | grep DB_PASSWORD

# Oder prüfe PostgreSQL direkt
sudo -u postgres psql -c "\du drive_user"
```

### Nach der Verbindung

1. **Test-Query ausführen:**
   - Klicke auf **"Neu"** → **"Frage"** → **"Native query"**
   - Wähle Datenbank: **"DRIVE Portal"**
   - Test-Query:
   ```sql
   SELECT COUNT(*) as anzahl_tabellen
   FROM information_schema.tables
   WHERE table_schema = 'public';
   ```
   - Klicke auf **"Abfrage ausführen"**

2. **Falls erfolgreich:** Du siehst die Anzahl der Tabellen in der Datenbank

## Verfügbare Tabellen für TEK/BWA

Wichtige Tabellen:
- `controlling_data` - TEK-Daten
- `bwa_monatswerte` - BWA-Monatswerte
- `loco_journal_accountings` - Buchhaltungsdaten
- `bereiche` - Bereiche (NW, GW, Teile, Werkstatt)
- `standorte` - Standorte (DEG, HYU, LAN)
- `loco_nominal_accounts` - Konten-Stammdaten

## Nächste Schritte

Nach erfolgreicher Verbindung:
1. Verwende Queries aus `docs/metabase_queries.sql`
2. Erstelle erste Dashboards
3. Integriere in DRIVE Portal
