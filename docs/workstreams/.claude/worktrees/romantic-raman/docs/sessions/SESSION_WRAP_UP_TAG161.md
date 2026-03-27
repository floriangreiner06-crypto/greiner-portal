# SESSION WRAP-UP TAG 161

**Datum:** 2026-01-02
**Fokus:** KST-Zielplanung mit IST/SOLL-Vergleich und Hochrechnung

---

## ERLEDIGTE AUFGABEN

### 1. KST-Zielplanung Datenmodell & Tabelle

**Neue Tabelle `kst_ziele`:**
```sql
CREATE TABLE kst_ziele (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr TEXT NOT NULL,           -- '2025/26'
    monat INTEGER NOT NULL,                 -- 1-12 (GJ: Sep=1, Aug=12)
    bereich TEXT NOT NULL,                  -- NW, GW, Teile, Werkstatt, Sonstige
    standort INTEGER DEFAULT 0,             -- 0=Alle, 1=DEG, 2=HYU, 3=LAN

    -- Universelle KPIs
    umsatz_ziel NUMERIC(15,2),
    db1_ziel NUMERIC(15,2),
    marge_ziel NUMERIC(5,2),

    -- Verkauf (NW, GW)
    stueck_ziel INTEGER,

    -- GW-spezifisch
    avg_standzeit_ziel INTEGER,             -- Max. Durchschnittliche Standzeit

    -- Werkstatt
    stunden_ziel NUMERIC(10,2),             -- Produktive Stunden
    auslastung_ziel NUMERIC(5,2),           -- Auslastung %

    UNIQUE(geschaeftsjahr, monat, bereich, standort)
);
```

**Beispiel-Ziele eingefuegt:**
- GJ 2025/26, Monate 1-5 (Sep-Jan)
- Basierend auf GAP-Analyse (TAG 158)
- Ziel-Margen: NW=8%, GW=6%, Teile=28%, Werkstatt=55%

### 2. KST-Ziele API

**Neue API:** `/api/kst-ziele/`

| Endpoint | Beschreibung |
|----------|--------------|
| `/health` | Health-Check mit GJ/Monat |
| `/dashboard` | IST vs SOLL mit Hochrechnung pro Bereich |
| `/ziele` | CRUD fuer Ziele (GET/POST/PUT) |
| `/status` | Taeglicher Status (Daumen hoch/runter) |
| `/kumuliert` | YTD-Uebersicht |

**Dashboard-Response Beispiel:**
```json
{
  "bereiche": [
    {
      "bereich": "NW",
      "ist": {"db1": 79656, "marge": 7.4, "stueck": 0},
      "ziel": {"db1": 60000, "marge": 8.0, "stueck": 17},
      "prognose": {"db1": 67401, "erreichung_pct": 112.3},
      "status": "positiv"
    },
    ...
  ],
  "gesamt": {
    "db1_ist": 250000,
    "db1_ziel": 280000,
    "db1_prognose": 270000,
    "status": "warnung"
  }
}
```

**Status-Icons:**
- 👍 positiv: Prognose >= Ziel
- ⚠️ warnung: 85-100% vom Ziel
- 👎 negativ: <85% vom Ziel

### 3. Handlungsempfehlungen

Automatische Empfehlungen bei Status "down":
- **NW:** "Auslieferungen beschleunigen, Pipeline pruefen"
- **GW:** "Standzeit-Leichen abbauen, Rabattaktion starten"
- **Teile:** "Werkstatt-Umsatz steigern, Lagerreichweite pruefen"
- **Werkstatt:** "Offene Auftraege abschliessen, Leerlauf reduzieren"

---

## NEUE DATEIEN

| Datei | LOC | Beschreibung |
|-------|-----|--------------|
| `api/kst_ziele_api.py` | ~550 | KST-Zielplanung API |

---

## DATENBANK-AENDERUNGEN

```sql
-- Neue Tabelle
CREATE TABLE kst_ziele (...);

-- Beispiel-Ziele fuer GJ 2025/26
INSERT INTO kst_ziele (geschaeftsjahr, monat, bereich, ...) VALUES
('2025/26', 1, 'NW', 0, 875000, 70000, 8.0, 20, ...),
...
```

---

## ARCHITEKTUR-HINWEISE

### Dual-DB-Zugriff

Die API nutzt **beide Datenbanken**:
1. **DRIVE Portal** (db_session): Ziele, loco_journal_accountings
2. **Locosoft** (get_locosoft_connection): dealer_vehicles, times, labours

```python
# DRIVE Portal fuer Ziele und FIBU
with db_session() as conn:
    cursor.execute("SELECT ... FROM kst_ziele ...")
    cursor.execute("SELECT ... FROM loco_journal_accountings ...")

# Locosoft fuer Werkstatt/Fahrzeuge
conn_loco = get_locosoft_connection()
cursor_loco.execute("SELECT ... FROM dealer_vehicles ...")
```

### Geschaeftsjahr-Mapping

- GJ-Monat 1 = September, ..., GJ-Monat 12 = August
- `get_gj_monat()` und `get_kalendar_monat()` fuer Konvertierung

---

## NAECHSTE SCHRITTE (TAG 162+)

1. **E-Mail-Report Script:** Taeglicher Versand des Status-Reports
2. **Dashboard-UI:** Web-Oberflaeche fuer Zielplanung
3. **Ziel-Editor:** UI zum Bearbeiten der Ziele
4. **Erweiterte Empfehlungen:** Mehr bereichsspezifische Handlungsvorschlaege

---

## API-TESTS

```bash
# Health-Check
curl -s http://localhost:5000/api/kst-ziele/health

# Dashboard (Dezember)
curl -s 'http://localhost:5000/api/kst-ziele/dashboard?monat=4' | python3 -m json.tool

# Tagesstatus
curl -s http://localhost:5000/api/kst-ziele/status | python3 -m json.tool

# Ziele laden
curl -s 'http://localhost:5000/api/kst-ziele/ziele?gj=2025/26' | python3 -m json.tool
```

---

*Erstellt: TAG 161 | Autor: Claude AI*
