# /db - Datenbank-Abfragen

Direkte PostgreSQL-Abfragen -- kein SSH, kein SQLite.

## Umgebung auto-erkennen

Aktuelles Verzeichnis bestimmt die Datenbank:

| Verzeichnis | Datenbank | Verwendung |
|-------------|-----------|------------|
| /opt/greiner-portal/ | drive_portal | Production |
| /opt/greiner-test/ | drive_portal_dev | Develop |

```bash
pwd
```

## Verbindungs-Befehle

### Production (drive_portal)

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "[QUERY]"
```

### Develop (drive_portal_dev)

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "[QUERY]"
```

### Locosoft (read-only, extern)

```bash
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c "[QUERY]"
```

## Haeufige Abfragen

### Tabellen auflisten

```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
```

### Tabellen-Struktur anzeigen

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "\d tabellenname"
```

### User und Rollen

```sql
SELECT u.display_name, u.username, u.role FROM users u ORDER BY u.display_name;
```

### Letzte Logins

```sql
SELECT display_name, last_login FROM users ORDER BY last_login DESC LIMIT 10;
```

### Navigation-Eintraege

```sql
SELECT id, parent_id, label, url, order_index FROM navigation_items ORDER BY parent_id, order_index;
```

## /db refresh-dev - Develop-DB aus Production kopieren

Kopiert die Production-DB in die Develop-DB (pg_dump + pg_restore).

**Achtung:** Die gesamte Develop-DB wird ueberschrieben. Bestaetigung einholen.

```bash
# Backup der aktuellen Dev-DB
PGPASSWORD=DrivePortal2024 pg_dump -h 127.0.0.1 -U drive_user -d drive_portal_dev > /tmp/drive_portal_dev_backup_$(date +%Y%m%d_%H%M%S).sql

# Production dumpen
PGPASSWORD=DrivePortal2024 pg_dump -h 127.0.0.1 -U drive_user -d drive_portal > /tmp/drive_portal_prod_dump.sql

# Dev-DB zuruecksetzen und neu befuellen
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev < /tmp/drive_portal_prod_dump.sql

# Temp-Dateien loeschen
rm /tmp/drive_portal_prod_dump.sql
```

## Sicherheitsregeln

- **SELECT-Abfragen:** Direkt ausfuehren, keine Rueckfrage noetig
- **INSERT / UPDATE / DELETE:** Zuerst die Abfrage zeigen und Bestaetigung einholen
- **DROP / TRUNCATE:** Explizite Bestaetigung + Warnung ausgeben
- **Kein SQLite:** Ausschliesslich PostgreSQL -- niemals sqlite3 verwenden

## Wichtige Tabellen

| Tabelle | Inhalt |
|---------|--------|
| users | Portal-User, Rollen |
| employees | Mitarbeiter (Urlaubsplaner) |
| navigation_items | Menuestruktur |
| vacation_bookings | Urlaubsantraege |
| konten, transaktionen | Bankenspiegel |
| budget_plan | Verkaufs-Budget |
| fahrzeugfinanzierungen | Fahrzeug-Zinsen |
