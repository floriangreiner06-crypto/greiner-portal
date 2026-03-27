# SESSION WRAP-UP TAG 90 - Werkstatt-Leistungsübersicht
**Datum:** 2025-12-04  
**Fokus:** Werkstatt-Auswertung mit abgerechneten Aufträgen & Leistungsgrad

---

## 🎯 AUFGABE

**Anforderung vom User:**
- Tägliche Übersicht der abgerechneten Locosoft Werkstattaufträge
- Leistungsübersicht nach Mechaniker und Serviceberater
- Leistungsgrad = Auftragszeit (AW) / Stempelzeit × 100%

---

## ✅ ERSTELLT

### 1. Sync-Script: `scripts/sync/sync_werkstatt_zeiten.py`
- Synchronisiert Stempelzeiten aus Locosoft (falls vorhanden)
- Fallback: Berechnet aus `labours` und `invoices`
- Erstellt zwei neue Tabellen:
  - `werkstatt_leistung_daily` - Tägliche Mechaniker-Leistung
  - `werkstatt_auftraege_abgerechnet` - Abgerechnete Aufträge

**Verwendung:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python scripts/sync/sync_werkstatt_zeiten.py --days 30
# Oder komplett:
python scripts/sync/sync_werkstatt_zeiten.py --full
```

### 2. API: `api/werkstatt_api.py`
Endpoints:
- `GET /api/werkstatt/dashboard` - Tages-/Monats-KPIs
- `GET /api/werkstatt/leistung` - Mechaniker-Leistungsgrad
- `GET /api/werkstatt/serviceberater` - Übersicht nach Serviceberater
- `GET /api/werkstatt/auftraege` - Detaillierte Auftragsliste
- `GET /api/werkstatt/trend` - Zeitlicher Verlauf
- `GET /api/werkstatt/health` - Health Check

### 3. Template: `templates/werkstatt_uebersicht.html`
Features:
- KPI-Karten (Aufträge, Umsatz, Lohn, Teile, AW, Ø-Auftrag)
- Tabs: Serviceberater | Mechaniker-Leistung | Aufträge | Trend
- Datumswähler (Heute/Monat)
- Standort-Filter (Deggendorf/Landau)
- Trend-Chart mit Chart.js

### 4. App-Registrierung in `app.py`
- Blueprint registriert: `/api/werkstatt/`
- Route registriert: `/werkstatt` und `/werkstatt/uebersicht`

---

## 📋 DEPLOYMENT-SCHRITTE

### Auf dem Server ausführen:

```bash
# 1. Dateien synchronisieren
cd /opt/greiner-portal
rsync -av /mnt/greiner-sync/ .

# 2. Sync-Script ausführen (initialer Datenimport)
source venv/bin/activate
python scripts/sync/sync_werkstatt_zeiten.py --days 60

# 3. Flask neustarten
sudo systemctl restart greiner-portal

# 4. Testen
curl http://localhost:5000/api/werkstatt/health
```

---

## 🔍 WICHTIGE ERKENNTNISSE

### Datenquellen in Locosoft:
| Tabelle | Inhalt | Zeilen |
|---------|--------|--------|
| `loco_orders` | Werkstattaufträge | 40.704 |
| `loco_labours` | Arbeitspositionen (time_units = AW) | 278.593 |
| `loco_invoices` | Rechnungen | 53.675 |
| `loco_employees` | Mitarbeiter (mechanic_number!) | 114 |
| `loco_times` | Stempelzeiten | 0 (LEER!) |

### ⚠️ PROBLEM: Stempelzeiten fehlen!
Die Tabelle `loco_times` ist leer. Das bedeutet:
- Leistungsgrad kann NICHT berechnet werden (braucht Soll/Ist-Vergleich)
- Das Sync-Script zeigt aktuell nur **verkaufte AW** (Vorgabezeit)

### Lösung:
1. **Prüfen ob Stempelzeiten in Locosoft anders erfasst werden**
   - Möglicherweise in anderer Tabelle?
   - Oder werden sie manuell in Locosoft eingetragen?
   
2. **Wenn keine Stempelzeiten:**
   - Zeigt nur Vorgabezeit/verkaufte AW
   - Leistungsgrad bleibt leer (NULL)

---

## 📊 DATENMODELL

### Tabelle: werkstatt_auftraege_abgerechnet
```sql
CREATE TABLE werkstatt_auftraege_abgerechnet (
    id INTEGER PRIMARY KEY,
    rechnungs_datum DATE,
    rechnungs_nr INTEGER,
    auftrags_nr INTEGER,
    betrieb INTEGER,
    kunde_nr INTEGER,
    kennzeichen TEXT,
    serviceberater_nr INTEGER,
    serviceberater_name TEXT,
    lohn_netto REAL,
    lohn_brutto REAL,
    teile_netto REAL,
    teile_brutto REAL,
    gesamt_netto REAL,
    gesamt_brutto REAL,
    summe_aw REAL,           -- Verkaufte Arbeitseinheiten
    summe_vorgabezeit_min REAL,  -- = summe_aw * 6 Minuten
    storniert INTEGER
);
```

### Tabelle: werkstatt_leistung_daily
```sql
CREATE TABLE werkstatt_leistung_daily (
    id INTEGER PRIMARY KEY,
    datum DATE,
    mechaniker_nr INTEGER,
    mechaniker_name TEXT,
    auftrag_nr INTEGER,
    charge_type INTEGER,
    vorgabezeit_aw REAL,     -- Soll (aus labours.time_units)
    vorgabezeit_min REAL,    -- = aw * 6
    stempelzeit_min REAL,    -- Ist (aus times) - AKTUELL LEER
    leistungsgrad REAL,      -- = vorgabezeit / stempelzeit * 100
    umsatz REAL
);
```

---

## 🧮 LEISTUNGSGRAD-FORMEL

```
Leistungsgrad = (Vorgabezeit in Minuten) / (Stempelzeit in Minuten) × 100%

Wobei:
- Vorgabezeit = SUM(time_units) × 6 Minuten  (aus labours)
- Stempelzeit = SUM(duration_minutes)         (aus times)

Beispiel:
- Auftrag mit 10 AW = 60 min Vorgabezeit
- Mechaniker stempelt 50 min
- Leistungsgrad = 60/50 × 100 = 120%
```

---

## 🔄 CRON-JOB (empfohlen)

```bash
# In crontab hinzufügen:
# Täglich um 22:00 Uhr sync (nach Locosoft-Mirror)
0 22 * * * cd /opt/greiner-portal && venv/bin/python scripts/sync/sync_werkstatt_zeiten.py --days 7 >> logs/werkstatt_sync.log 2>&1
```

---

## 🚀 NÄCHSTE SCHRITTE

1. **SOFORT:** Sync-Script auf Server ausführen
2. **PRÜFEN:** Woher kommen Stempelzeiten in Locosoft?
3. **OPTIONAL:** Scheduler-Job für täglichen Sync anlegen
4. **SPÄTER:** Mechaniker-Leistungsgrad mit echten Stempelzeiten

---

## 📁 ERSTELLTE DATEIEN

```
scripts/sync/sync_werkstatt_zeiten.py    # NEU - Sync-Script
api/werkstatt_api.py                      # NEU - REST API
templates/werkstatt_uebersicht.html       # NEU - Frontend
app.py                                    # GEÄNDERT - Blueprint + Route
```

---

## ⚠️ BEKANNTE LIMITIERUNGEN

1. **Keine Stempelzeiten** - `loco_times` ist leer
   - Leistungsgrad kann nicht berechnet werden
   - Nur verkaufte AW werden angezeigt
   
2. **Keine Mechaniker-Zuordnung bei fehlendem mechanic_no**
   - Manche Positionen haben keinen Mechaniker
   - Werden unter "Nicht zugeordnet" geführt

---

**Status:** ✅ Grundsystem erstellt, wartet auf Deployment & Stempelzeiten-Klärung
