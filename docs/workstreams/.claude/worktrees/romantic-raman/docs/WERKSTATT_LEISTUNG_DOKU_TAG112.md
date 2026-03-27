# Werkstatt Leistungsübersicht - Technische Dokumentation

**Erstellt:** 2025-12-10 (TAG 112)  
**Letzte Änderung:** 2025-12-10  
**Autor:** Claude AI / Florian  
**Status:** ✅ Produktiv  

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [KPI-Definitionen & Berechnungen](#kpi-definitionen--berechnungen)
3. [Datenquellen](#datenquellen)
4. [API-Endpoints](#api-endpoints)
5. [Frontend-Komponenten](#frontend-komponenten)
6. [Bekannte Probleme & Lösungen](#bekannte-probleme--lösungen)
7. [Deployment](#deployment)

---

## 🎯 Übersicht

Die **Werkstatt Leistungsübersicht** zeigt die Performance der Werkstatt-Mechaniker anhand verschiedener KPIs. Das Dashboard ermöglicht:

- Tagesaktuelle Leistungsüberwachung
- Historische Trend-Analyse
- Mechaniker-Vergleiche
- Problemfall-Erkennung (niedrige Leistungsgrade)
- Berechnung von entgangenem Umsatz

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    WERKSTATT DASHBOARD                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Jinja2/JS)         API (Flask)                   │
│  ┌─────────────────────┐      ┌─────────────────────┐       │
│  │ werkstatt_          │ ──→  │ werkstatt_api.py    │       │
│  │ uebersicht.html     │      │                     │       │
│  │ - Chart.js          │      │ /api/werkstatt/     │       │
│  │ - Bootstrap 5       │      │ - leistung          │       │
│  └─────────────────────┘      │ - trend             │       │
│                               │ - problemfaelle     │       │
│                               └─────────────────────┘       │
│                                        │                     │
│                                        ↓                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Datenquellen                       │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ SQLite (greiner_controlling.db)                      │   │
│  │ - werkstatt_leistung_daily (Tages-Aggregation)      │   │
│  │ - werkstatt_auftraege_abgerechnet (Einzelaufträge)  │   │
│  │ - loco_employees (Mitarbeiter)                       │   │
│  │ - loco_absence_calendar (Abwesenheiten)              │   │
│  │ - holidays (Bayern Feiertage)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 KPI-Definitionen & Berechnungen

### Haupt-KPIs (3 Tachos + Umsatz-Card)

#### 1. Leistungsgrad (%)
```
Leistungsgrad = (Vorgabe AW × 6) / Stempelzeit (min) × 100

Beispiel:
- Vorgabe: 100 AW
- Stempelzeit: 480 min (8h)
- Leistungsgrad = (100 × 6) / 480 × 100 = 125%
```

| Bereich | Bewertung | Farbe |
|---------|-----------|-------|
| ≥ 100%  | Excellent | 🟢 Grün |
| 80-99%  | Gut       | 🔵 Blau |
| 60-79%  | Warnung   | 🟡 Gelb |
| < 60%   | Kritisch  | 🔴 Rot |

**Ziel:** ≥ 100%

#### 2. Produktivität (%)
```
Produktivität = Stempelzeit / Anwesenheitszeit × 100

Beispiel:
- Stempelzeit: 400 min
- Anwesenheit: 480 min
- Produktivität = 400 / 480 × 100 = 83.3%
```

**Ziel:** ≥ 90%

**Bedeutung:** Wie viel der Anwesenheitszeit wird auf Aufträge gestempelt?

#### 3. Effizienz (%)
```
Effizienz = Leistungsgrad × Produktivität / 100

Beispiel:
- Leistungsgrad: 100%
- Produktivität: 90%
- Effizienz = 100 × 90 / 100 = 90%
```

**Ziel:** ≥ 85%

**Bedeutung:** Kombinierte Kennzahl aus Leistung UND Produktivität.

#### 4. Entgangener Umsatz (€)
```
Verlorene Stunden = Stempelzeit (Std) × (1 - Leistungsgrad/100)
Entgangener Umsatz = Verlorene Stunden × SVS

Beispiel:
- Stempelzeit: 400 Std
- Leistungsgrad: 80%
- SVS: 119 €/Std
- Verlorene Std = 400 × (1 - 0.8) = 80 Std
- Entgangener Umsatz = 80 × 119 = 9.520 €
```

**SVS (Standard-Verrechnungssatz):** Aus `charge_types_sync` Tabelle, default 119 €/Std

---

### Kontext-KPIs (2. Reihe)

| KPI | Berechnung | Beschreibung |
|-----|------------|--------------|
| Mechaniker | COUNT(DISTINCT mechaniker_nr) | Anzahl aktive Mechaniker (MON-Gruppe) |
| Aufträge | SUM(anzahl_auftraege) | Abgerechnete Aufträge im Zeitraum |
| Stempelzeit | SUM(stempelzeit_min) / 60 | Gesamte produktive Zeit in Stunden |
| Anwesenheit | SUM(anwesenheit_min) / 60 | Gesamte Anwesenheitszeit in Stunden |
| Arbeitswerte | SUM(vorgabezeit_aw) | Summe der Vorgabe-AW |
| Arbeitstage | COUNT(DISTINCT datum) | Anzahl Tage mit Buchungen |

---

### Soll-Kapazität Berechnung (TAG 111)

```
Soll-Kapazität (AW) = (Arbeitstage × Basis-Mechaniker × 80) - (Abwesenheitstage × 80)

Wobei:
- Arbeitstage = Werktage (Mo-Fr) ohne Feiertage im Zeitraum
- Basis-Mechaniker = Aktive MON-Mechaniker (ohne Azubis)
- 80 AW = 10 AW/Std × 8 Std/Tag
- Abwesenheitstage = Summe Abwesenheiten aus loco_absence_calendar
```

**Mechaniker-Filter:**
```sql
-- Nur echte Mechaniker (MON), keine Azubis
SELECT employee_number FROM loco_employees e
JOIN loco_employees_group_mapping g ON e.employee_number = g.employee_number
WHERE g.grp_code = 'MON'
  AND e.is_latest_record = 1
  AND e.employee_number NOT IN (
      SELECT employee_number FROM loco_employees_group_mapping 
      WHERE grp_code IN ('A-W', 'A-L', 'A-K')  -- Azubi-Gruppen
  )
```

---

### Trend-Chart Berechnung (TAG 112)

Der Trend zeigt die **letzten 10 Werktage** (ohne heute):

1. **API-Aufruf:** `/api/werkstatt/trend?tage=20`
2. **Filter:**
   - Wochenenden (Sa/So) ausgeschlossen
   - Bayern-Feiertage ausgeschlossen (aus `holidays` Tabelle)
   - Nur abgeschlossene Tage (< heute)
3. **Anzeige:** Letzte 10 Werktage

**Labels:** `Mo 01.12 [12/13]` = Wochentag, Datum, [Anwesend/Soll]

**Tooltip:** Details bei Hover
- Mechaniker anwesend/abwesend
- Aufträge
- Stempelzeit

---

## 🗄️ Datenquellen

### Tabellen

| Tabelle | Quelle | Beschreibung |
|---------|--------|--------------|
| `werkstatt_leistung_daily` | Sync-Script | Tägliche Aggregation pro Mechaniker |
| `werkstatt_auftraege_abgerechnet` | Locosoft | Einzelne abgerechnete Aufträge |
| `loco_employees` | Locosoft | Mitarbeiterstammdaten |
| `loco_employees_group_mapping` | Locosoft | Gruppenzuordnung (MON, A-W, etc.) |
| `loco_absence_calendar` | Locosoft | Abwesenheiten (Urlaub, Krank, etc.) |
| `holidays` | Manuell | Bayern Feiertage |
| `charge_types_sync` | Locosoft | Verrechnungssätze (SVS) |

### Relevante Spalten

**werkstatt_leistung_daily:**
```sql
- datum
- mechaniker_nr
- mechaniker_name
- betrieb_nr
- anzahl_auftraege
- stempelzeit_min
- anwesenheit_min
- vorgabezeit_aw
- leistungsgrad
- umsatz
- ist_aktiv
```

**werkstatt_auftraege_abgerechnet:**
```sql
- rechnungs_datum
- rechnungs_nr
- auftrags_nr
- kennzeichen
- betrieb
- summe_aw
- summe_stempelzeit_min
- leistungsgrad
- serviceberater_nr
- serviceberater_name
- storniert
```

---

## 🔌 API-Endpoints

### GET /api/werkstatt/leistung

**Parameter:**
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| zeitraum | monat | heute\|woche\|monat\|vormonat\|quartal\|jahr\|custom |
| von/bis | - | Bei custom |
| betrieb | alle | alle\|1\|3 |
| sort | leistungsgrad | leistungsgrad\|stempelzeit\|aw\|auftraege |
| inkl_ehemalige | 0 | 1 = Ehemalige einschließen |

**Response:**
```json
{
  "success": true,
  "mechaniker": [...],
  "gesamt": {
    "leistungsgrad": 85.2,
    "produktivitaet": 92.1,
    "effizienz": 78.5,
    "stempelzeit": 24000,
    "anwesenheit": 26000,
    "auftraege": 320,
    "aw": 4500,
    "svs": 119.0,
    "entgangener_umsatz": 6408.55,
    "verlorene_std": 53.9,
    "soll_kapazitaet_aw": 5840,
    "basis_mechaniker": 10,
    "arbeitstage": 8,
    "abwesenheitstage": 5
  }
}
```

### GET /api/werkstatt/trend

**Parameter:**
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| tage | 30 | Anzahl Tage zurück |
| betrieb | alle | alle\|1\|3 |

**Response:**
```json
{
  "success": true,
  "trend": [
    {
      "datum": "2025-12-09",
      "leistungsgrad": 89.9,
      "mechaniker_anwesend": 12,
      "mechaniker_soll": 13,
      "abwesend": 1,
      "auftraege": 45,
      "stempelzeit": 2800,
      "ist_werktag": true
    }
  ],
  "basis_mechaniker": 13
}
```

**Besonderheiten:**
- Filtert Wochenenden (Sa/So) aus
- Filtert Bayern-Feiertage aus (aus `holidays` Tabelle)
- Gibt nur Werktage zurück

### GET /api/werkstatt/problemfaelle

**Parameter:**
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| zeitraum | monat | Zeitraumfilter |
| betrieb | alle | Betriebsfilter |
| max_lg | 70 | Maximaler Leistungsgrad (%) |
| min_stempelzeit | 30 | Mindest-Stempelzeit (min) |

**Response:**
```json
{
  "success": true,
  "auftraege": [...],
  "anzahl": 15,
  "statistik": {
    "durchschnitt_lg": 52.3,
    "total_verlust_aw": 125.5
  }
}
```

---

## 🎨 Frontend-Komponenten

### Template
`templates/aftersales/werkstatt_uebersicht.html`

### Tabs
1. **Mechaniker-Ranking:** Karten mit Leistungsgrad, Rang-Badge
2. **Trend:** Line-Chart (Leistungsgrad + Ziel 100%)
3. **Detailtabelle:** Sortierbare Tabelle mit Summen
4. **Vergleich:** Horizontal-Bar + Pie-Chart
5. **Problemfälle:** Aufträge mit LG < 70%

### Charts (Chart.js)
- `trendChart`: Leistungsgrad-Verlauf
- `vergleichChart`: Mechaniker-Vergleich (Bar)
- `pieChart`: Stempelzeit-Verteilung

### Modals
- `detailModal`: Mechaniker-Detail
- `entgangenerUmsatzModal`: Verlust-Berechnung
- `auftragModal`: Auftrags-Detail

---

## ⚠️ Bekannte Probleme & Lösungen

### Problem 1: Falscher Mount-Pfad (TAG 111-112)
**Symptom:** Änderungen nicht auf Server sichtbar

**Ursache:** Falscher Pfad `/mnt/greiner-sync/` statt `/mnt/greiner-portal-sync/`

**Lösung:** 
```bash
# KORREKT:
sudo cp /mnt/greiner-portal-sync/api/werkstatt_api.py /opt/greiner-portal/api/

# FALSCH:
sudo cp /mnt/greiner-sync/api/werkstatt_api.py ...  # NICHT VERWENDEN!
```

**Merke:** Mount-Pfad ist in `/mnt/project/CLAUDE.md` dokumentiert!

---

### Problem 2: Template-Version verloren (TAG 111)
**Symptom:** Effizienz-Tacho und Entgangener Umsatz fehlten

**Ursache:** Template wurde nie korrekt gespeichert/deployed

**Lösung:** Template aus Chat-History rekonstruiert und neu deployed

**Prävention:** Nach Template-Änderungen immer prüfen:
```bash
ls -la /opt/greiner-portal/templates/aftersales/werkstatt_uebersicht.html
grep -c "Effizienz\|entgangener" /opt/greiner-portal/templates/aftersales/werkstatt_uebersicht.html
```

---

### Problem 3: Problemfälle API - Falsche Spaltennamen (TAG 112)
**Symptom:** `no such column: w.datum`

**Ursache:** Query verwendete falsche Spaltennamen

**Lösung:** Spalten-Mapping korrigiert:

| API erwartet | Tatsächlich |
|--------------|-------------|
| `datum` | `rechnungs_datum` |
| `betrieb_nr` | `betrieb` |
| `stempelzeit_min` | `summe_stempelzeit_min` |
| `vorgabe_aw` | `summe_aw` |
| `mechaniker_nr` | `serviceberater_nr` |

---

### Problem 4: Wochenenden im Trend (TAG 112)
**Symptom:** Samstage (LG=None, Anwesend=0) im Chart

**Ursache:** API-Änderung (Feiertags-Filter) nicht deployed

**Lösung:** 
1. API nach Deployment prüfen
2. Service neu starten: `systemctl restart greiner-portal`

---

### Problem 5: Trend-Chart zu viele Linien (TAG 112)
**Symptom:** 4 Linien, verwirrend, zwei Y-Achsen

**Ursache:** Ursprünglich Mechaniker-Anwesenheit als separate Linien

**Lösung:** Vereinfacht auf:
- 2 Linien: Leistungsgrad + Ziel
- Anwesenheit im X-Achsen-Label: `[12/13]`
- Details im Tooltip bei Hover

---

### Problem 6: Azubis in Mechaniker-Zählung (TAG 111)
**Symptom:** Basis-Mechaniker zu hoch

**Ursache:** Azubis haben oft MON-Gruppenzuordnung zusätzlich zu A-W/A-L/A-K

**Lösung:** Expliziter Ausschluss:
```sql
AND e.employee_number NOT IN (
    SELECT employee_number FROM loco_employees_group_mapping 
    WHERE grp_code IN ('A-W', 'A-L', 'A-K')
)
```

---

## 🚀 Deployment

### Dateien
```
/opt/greiner-portal/
├── api/werkstatt_api.py           # API-Endpoints
├── templates/aftersales/
│   └── werkstatt_uebersicht.html  # Frontend
└── data/greiner_controlling.db    # Datenbank
```

### Deployment-Befehle
```bash
# 1. API kopieren
sudo cp /mnt/greiner-portal-sync/api/werkstatt_api.py /opt/greiner-portal/api/

# 2. Template kopieren
sudo cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_uebersicht.html /opt/greiner-portal/templates/aftersales/

# 3. Service neu starten (nur bei Python-Änderungen!)
sudo systemctl restart greiner-portal

# 4. Logs prüfen
sudo journalctl -u greiner-portal -f
```

### Verifizierung
```bash
# API-Health
curl http://localhost:5000/api/werkstatt/health

# Trend-Check (keine Wochenenden!)
curl -s "http://localhost:5000/api/werkstatt/trend?tage=10" | python3 -c "
import sys,json
for t in json.load(sys.stdin).get('trend',[]):
    from datetime import datetime
    dt = datetime.strptime(t['datum'], '%Y-%m-%d')
    print(f\"{t['datum']} ({['Mo','Di','Mi','Do','Fr','Sa','So'][dt.weekday()]}): LG={t.get('leistungsgrad')}%\")"
```

---

## 📝 Änderungshistorie

| Datum | TAG | Änderung |
|-------|-----|----------|
| 2025-12-04 | 90 | Initial: Basis-Dashboard |
| 2025-12-05 | - | Betriebsfilter hinzugefügt |
| 2025-12-10 | 111 | Soll-Kapazität mit Abwesenheiten |
| 2025-12-10 | 111 | Azubi-Bug behoben |
| 2025-12-10 | 111 | Effizienz-Tacho + Entgangener Umsatz |
| 2025-12-10 | 112 | Problemfälle-Tab + API |
| 2025-12-10 | 112 | Trend-API: Feiertags-Filter Bayern |
| 2025-12-10 | 112 | Trend-Chart vereinfacht (2 Linien) |
| 2025-12-10 | 112 | Trend: Nur letzte 10 Werktage |

---

## 🔗 Verwandte Dokumente

- `CLAUDE.md` - Projekt-Konventionen & Mount-Pfade
- `DATABASE_SCHEMA.md` - Datenbank-Struktur
- `API_INTEGRATION.md` - API-Dokumentation
- `Locosoft_zeiterfassung_und_mitarbeiter.pdf` - Locosoft-Doku

---

**Kontakt:** Bei Fragen → Florian / IT
