# Metabase - Datenbank erfolgreich verbunden ✅

## Status

**Datenbank:** DRIVE Portal  
**ID:** 2  
**Status:** Verbunden und synchronisiert

## Verbindungsdaten

```
Name: DRIVE Portal
Host: localhost
Port: 5432
Database: drive_portal
User: drive_user
```

## Nächste Schritte

### 1. Tabellen prüfen

In Metabase:
1. Öffne http://10.80.80.20:3001
2. Klicke auf **"Daten"** → **"Datenbanken"** → **"DRIVE Portal"**
3. Du solltest alle Tabellen sehen

### 2. Erste Query testen

1. Klicke auf **"Neu"** → **"Frage"** → **"Native query"**
2. Wähle Datenbank: **"DRIVE Portal"**
3. Test-Query:
```sql
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = 'public' AND table_name = t.table_name) as spalten
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name
LIMIT 10;
```

### 3. TEK-Query ausführen

Verwende Queries aus `docs/metabase_queries.sql`:

**TEK Gesamt - Monat kumuliert:**
```sql
SELECT 
    b.name as "Bereich",
    COALESCE(SUM(cd.erloes), 0) as "Erlös (€)",
    COALESCE(SUM(cd.einsatz), 0) as "Einsatz (€)",
    COALESCE(SUM(cd.db1), 0) as "DB1 (€)",
    CASE 
        WHEN SUM(cd.erloes) > 0 
        THEN ROUND(SUM(cd.db1) / SUM(cd.erloes) * 100, 2)
        ELSE 0 
    END as "DB1 (%)",
    COALESCE(SUM(cd.stueck), 0) as "Menge (Stück)"
FROM (
    SELECT 
        bereich_id,
        standort_id,
        jahr,
        monat,
        SUM(erloes) as erloes,
        SUM(einsatz) as einsatz,
        SUM(db1) as db1,
        SUM(stueck) as stueck
    FROM controlling_data
    WHERE jahr = EXTRACT(YEAR FROM CURRENT_DATE)
      AND monat <= EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY bereich_id, standort_id, jahr, monat
) cd
JOIN bereiche b ON cd.bereich_id = b.id
GROUP BY b.name, b.sort_order
ORDER BY b.sort_order;
```

## Verfügbare Tabellen

Wichtige Tabellen für TEK/BWA:
- `controlling_data` - TEK-Daten
- `bwa_monatswerte` - BWA-Monatswerte
- `loco_journal_accountings` - Buchhaltungsdaten
- `bereiche` - Bereiche (NW, GW, Teile, Werkstatt)
- `standorte` - Standorte (DEG, HYU, LAN)
- `loco_nominal_accounts` - Konten-Stammdaten

## Dashboard erstellen

Nach erfolgreichen Queries:
1. Erstelle **Questions** (Queries mit Visualisierungen)
2. Erstelle **Dashboard** → Füge Questions hinzu
3. Teile Dashboard oder integriere in DRIVE Portal
