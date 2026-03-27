# /db - Datenbank-Abfragen

Führe Datenbank-Abfragen auf dem Greiner Portal aus.

## Anweisungen

### SQLite (Lokal - greiner_controlling.db)
```
ssh ag-admin@10.80.80.20 "sqlite3 /opt/greiner-portal/data/greiner_controlling.db \"[QUERY]\""
```

### PostgreSQL (Locosoft)
```
ssh ag-admin@10.80.80.20 "PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db -c \"[QUERY]\""
```

## Häufige Abfragen

1. **User mit Rollen:**
   ```sql
   SELECT u.display_name, GROUP_CONCAT(r.name) as roles
   FROM users u
   LEFT JOIN user_roles ur ON u.id = ur.user_id
   LEFT JOIN roles r ON ur.role_id = r.id
   GROUP BY u.id;
   ```

2. **Letzte Logins:**
   ```sql
   SELECT display_name, last_login FROM users ORDER BY last_login DESC LIMIT 10;
   ```

3. **Tabellen-Liste:**
   ```sql
   SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
   ```

## Sicherheit
- Nur SELECT-Queries ohne Bestätigung
- INSERT/UPDATE/DELETE nur nach Rückfrage
