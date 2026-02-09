# Locosoft-Kunden-Sync – bessere Adressbuch-Suche

**TAG 211** – Kundendaten aus Locosoft in DRIVE PostgreSQL syncen, Volltextsuche nutzen.

**SOAP vs. Sync:** Siehe `docs/LOCOSOFT_SOAP_VS_POSTGRESQL_SYNC.md` – für die Adressbuch-Suche bleibt der Sync (PostgreSQL) empfohlen; SOAP sinnvoll für Einzellookup oder später inkrementellen Sync.

---

## Ablauf

1. **Migration ausführen** (einmalig) ✅ erledigt
2. **Sync-Script ausführen** (einmalig oder regelmäßig) ✅ einmalig erledigt (49.202 Kunden)
3. **Adressbuch nutzen** – API nutzt automatisch die Sync-Tabelle, wenn sie befüllt ist

---

## 1. Migration

```bash
cd /opt/greiner-portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal \
  -f migrations/add_locosoft_kunden_sync_tag211.sql
```

Erstellt die Tabelle `locosoft_kunden_sync` inkl. Volltext-Spalte `search_vector` (tsvector, GIN-Index).

---

## 2. Sync ausführen

```bash
cd /opt/greiner-portal
./venv/bin/python scripts/sync_locosoft_kunden.py
```

- Liest alle Kunden aus Locosoft (customers_suppliers + customer_com_numbers)
- Schreibt/aktualisiert `locosoft_kunden_sync` in DRIVE
- Pro Kunde: eine Zeile mit Haupttelefon, Handy (falls vorhanden), E-Mail

**Regelmäßig:** z. B. per Cron oder Celery-Task (z. B. täglich).

---

## 3. Suche

- **Mit Sync:** Adressbuch-API fragt `locosoft_kunden_sync` ab, Suche mit **Volltext** (`plainto_tsquery('german', …)`) und ILIKE-Fallback
- **Ohne Sync / Fallback:** wie bisher Live-Abfrage an Locosoft (ILIKE auf Name/Kundennr.)

Filter **„Nur Handynummern“** funktioniert in beiden Modi (Sync: `phone_mobile IS NOT NULL`).

---

## Dateien

| Zweck | Datei |
|-------|-------|
| Migration | `migrations/add_locosoft_kunden_sync_tag211.sql` |
| Sync-Script | `scripts/sync_locosoft_kunden.py` |
| API (Suche) | `api/locosoft_addressbook_api.py` (nutzt Sync, Fallback Locosoft) |
