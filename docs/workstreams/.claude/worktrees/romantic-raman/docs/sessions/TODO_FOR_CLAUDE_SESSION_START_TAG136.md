# TODO fuer Session TAG 136

**Erstellt:** 2025-12-23
**Letzte Session:** TAG 135 - PostgreSQL Migration

---

## Aktueller Stand

**PostgreSQL ist AKTIV!** Das Portal laeuft jetzt mit PostgreSQL als Datenbank-Backend.

### Konfiguration (.env auf Server)
```
DB_TYPE=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=drive_portal
DB_USER=drive_user
DB_PASSWORD=DrivePortal2024
```

### Rollback bei Problemen
```bash
# In /opt/greiner-portal/config/.env:
DB_TYPE=sqlite
sudo systemctl restart greiner-portal
```

---

## Noch zu syncen (TAG 135)

```bash
# Auth Manager Bug Fix (details -> details_json)
cp /mnt/greiner-portal-sync/auth/auth_manager.py /opt/greiner-portal/auth/
sudo systemctl restart greiner-portal
```

---

## Bekannte Issues

### 1. loco_journal_accountings Differenz
- SQLite: 605,744 Zeilen
- PostgreSQL: 599,298 Zeilen
- **Ursache:** Ungueltige Datumsformate wurden uebersprungen
- **Auswirkung:** Minimal (~1%), betrifft historische Daten

### 2. Monitoring
- PostgreSQL-Performance noch nicht langzeit-getestet
- Empfehlung: Logs beobachten fuer erste Wochen

---

## Offene Features/Aufgaben

### A. Report Registry System (TAG 134)
- Dynamische E-Mail-Empfaenger aus DB
- Admin UI unter "E-Mail Reports" Tab
- Noch nicht alle Reports migriert

### B. Ersatzwagen-Modul
- API angelegt (`api/ersatzwagen_api.py`)
- Noch nicht fertig implementiert

### C. Carloop Integration
- Analyse in `docs/CARLOOP_INTEGRATION_ANALYSE.md`
- API-Tests in `tools/scrapers/`

---

## Wichtige Dateien dieser Migration

| Datei | Zweck |
|-------|-------|
| `api/db_connection.py` | Dual-Mode SQLite/PostgreSQL |
| `scripts/migrations/migrate_sqlite_to_pg.py` | Hauptmigration |
| `scripts/migrations/rollback_to_sqlite.sh` | Rollback Script |
| `scripts/migrations/verify_migration.py` | Verifizierung |

---

## Bei Problemen

1. **Service Status:** `sudo systemctl status greiner-portal`
2. **Logs:** `journalctl -u greiner-portal -f`
3. **PostgreSQL Status:** `sudo systemctl status postgresql`
4. **DB Verbindung testen:**
   ```bash
   PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT 1"
   ```
5. **Rollback:** DB_TYPE=sqlite in .env setzen, restart

---

## Naechste Schritte (Vorschlaege)

1. PostgreSQL-Betrieb beobachten (Performance, Fehler)
2. Report Registry fuer alle Reports aktivieren
3. Ersatzwagen-Modul fertigstellen
4. Backup-Strategie fuer PostgreSQL definieren
