# KONSOLIDIERTE TODOs - Stand TAG 163

**Erstellt:** 2026-01-02
**Sessions heute:** TAG 148-162 (15 Sessions!)

---

## ERLEDIGTE AUFGABEN (02.01.2026)

### Werkstatt-Modularisierung (TAG 148-154)
- [x] werkstatt_data.py erstellt (3,413 LOC, 15 Funktionen)
- [x] gudat_data.py erstellt (599 LOC, 7 Methoden)
- [x] werkstatt_live_api.py reduziert: 5,532 -> 2,535 LOC (-54%)
- [x] Alle wichtigen Funktionen migriert (Leistung, Stempeluhr, Kapazitaet, etc.)

### Budget-Planungsmodul (TAG 155-156)
- [x] 5-Fragen-Wizard mit Slider-Eingaben
- [x] Standort-Selector (Alle, DEG Opel, DEG Hyundai, Landau)
- [x] Speichern in budget_plan Tabelle
- [x] Dashboard-Integration

### Unternehmensplan GlobalCube-kompatibel (TAG 157-158)
- [x] unternehmensplan_data.py erstellt
- [x] 100% Match mit GlobalCube (-162.114 EUR)
- [x] Gap-Analyse: 984.974 EUR fehlen zum 1%-Ziel

### GW-Dashboard & Data-Module (TAG 159-160)
- [x] fahrzeug_data.py erstellt (659 LOC)
- [x] verkauf_data.py erstellt (875 LOC)
- [x] GW-Standzeit Dashboard mit Ampel
- [x] /verkauf/gw-bestand Route

### KST-Zielplanung (TAG 161-162)
- [x] kst_ziele Tabelle erstellt
- [x] kst_ziele_api.py implementiert (~700 LOC)
- [x] KST-Ziele Dashboard UI
- [x] Umlage-Neutralisierung implementiert
- [x] YTD-Tracking Fix (Dezember)
- [x] Navigation Controlling Dropdown kategorisiert

---

## OFFENE AUFGABEN (nach Prioritaet)

### PRIORITAET 1: Zielplanung & Mitarbeiter (TAG 163+)

**A) Mitarbeiter-Ziele: Serviceberater (ERSTES ZIEL)**
| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Tabelle mitarbeiter_ziele erstellen | TODO | TAG163 |
| API fuer Serviceberater-Ziele | TODO | TAG163 |
| Verknuepfung mit employees | TODO | TAG163 |
| IST vs SOLL Dashboard | TODO | TAG163 |
| Ranking/Leaderboard | TODO | TAG163 |

```sql
CREATE TABLE mitarbeiter_ziele (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    geschaeftsjahr TEXT NOT NULL,
    monat INTEGER NOT NULL,
    -- Serviceberater-Ziele
    stunden_ziel NUMERIC(10,2),
    auslastung_ziel NUMERIC(5,2),
    umsatz_ziel NUMERIC(15,2),
    -- Spaeter: Verkauf
    stueck_ziel INTEGER,
    db1_ziel NUMERIC(15,2),
    UNIQUE(employee_id, geschaeftsjahr, monat)
);
```

**B) 5-Fragen-Wizard fuer 1%-Ziel erweitern**
| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Wizard auf ALLE KST erweitern (NW, GW, Teile, Werkstatt, Sonstige) | TODO | TAG163 |
| 1%-Renditeziel als Basis integrieren | TODO | TAG163 |
| Gap-Berechnung: Was fehlt zum 1%-Ziel? | TODO | TAG163 |
| Verteilung auf Bereiche vorschlagen | TODO | TAG163 |

**C) KST-Ziele Editor UI**
| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Matrix: Monate (Sep-Aug) x Bereiche | TODO | TAG163 |
| Inline-Editing der Zielwerte | TODO | TAG163 |
| Speichern via POST /api/kst-ziele/ziele | TODO | TAG163 |
| Kopieren von Vorjahres-Zielen | TODO | TAG163 |

**D) Potenziale erfassen (Input vom User)**
| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Offene Auftraege als Potenzial | TODO | TAG163 |
| Weitere Potenziale (User-Input abwarten) | TODO | TAG163 |

### PRIORITAET 2: Automatisierung

| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Taeglicher E-Mail-Report KST-Status | TODO | TAG162 |
| send_daily_kst_status.py erstellen | TODO | TAG162 |

### PRIORITAET 3: Validierung & Analyse

| Aufgabe | Status | Quelle |
|---------|--------|--------|
| Sonstige-Ziel pruefen (nur 12%) | TODO | TAG162 |
| TEK-Dashboard GlobalCube-Validierung | TODO | TAG158 |
| BWA v2 Validierung | TODO | TAG158 |

---

## NIEDRIGERE PRIORITAET (Backlog)

| Aufgabe | Status | Quelle |
|---------|--------|--------|
| fahrzeug_api.py Blueprint vollstaendig | TODO | TAG160 |
| GW-Dashboard CSV-Export | TODO | TAG160/161 |
| teile_data.py SSOT | TODO | TAG158 |
| Locosoft SOAP Client | TODO | TAG158 |
| send_daily_tek.py refactoren | TODO | TAG148 |
| controlling_routes.py refactoren | TODO | TAG148 |

---

## CODE-STATISTIK (02.01.2026)

### Neue/Erweiterte Module
| Modul | LOC | Funktionen |
|-------|-----|------------|
| werkstatt_data.py | 3,413 | 15 |
| gudat_data.py | 599 | 7 |
| fahrzeug_data.py | 659 | ~8 |
| verkauf_data.py | 875 | ~10 |
| unternehmensplan_data.py | ~800 | ~5 |
| kst_ziele_api.py | ~700 | 5 |

### Reduktion
- werkstatt_live_api.py: 5,532 -> 2,535 LOC (-54%)

---

## WICHTIGE REFERENZEN

### Dokumentation
- `docs/FIRMENSTRUKTUR.md` - Unternehmensstruktur
- `docs/KONTENPLAN_CONTROLLING.md` - Umlage-Konten
- `docs/BWA_KONTEN_MAPPING_FINAL.md` - GlobalCube Referenz
- `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md` - Gap-Analyse

### Konstanten (Umlage)
```python
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]  # Autohaus Greiner
UMLAGE_KOSTEN_KONTEN = [498001]  # Auto Greiner
UMLAGE_BETRAG_PRO_MONAT = 50000
```

### API-Endpoints
```
# KST-Ziele
GET  /api/kst-ziele/health
GET  /api/kst-ziele/dashboard?monat=5&standort=0
GET  /api/kst-ziele/ziele?gj=2025/26
POST /api/kst-ziele/ziele
GET  /api/kst-ziele/status
GET  /api/kst-ziele/kumuliert

# Unternehmensplan
GET  /api/unternehmensplan/ytd?gj=2025/26
GET  /api/unternehmensplan/dashboard

# Fahrzeuge
GET  /api/fahrzeug/health
GET  /api/fahrzeug/gw/dashboard
```

---

## NAECHSTER FOKUS (User-Wunsch)

> "Planung und ziele fuer kst und auch einzelne Mitarbeiter"
> "5-Fragen-Wizard fuer 1%-Ziel anpassen und auf alle KST erweitern"
> "Mitarbeiter-Ziele als erstes fuer Serviceberater"
> "Potenziale aufnehmen z.B. offene Auftraege"

**Empfohlene Reihenfolge TAG 163+:**
1. **Serviceberater-Ziele** - Tabelle + API + Dashboard
2. **5-Fragen-Wizard erweitern** - Alle KST, 1%-Ziel-Integration
3. **Potenziale** - Offene Auftraege etc. (Input abwarten)
4. KST-Ziele Editor UI

---

*Konsolidiert aus TAG 148-162 TODO-Dateien*
