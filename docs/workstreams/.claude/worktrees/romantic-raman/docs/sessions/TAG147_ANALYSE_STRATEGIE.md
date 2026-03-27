# TAG 147 - TEK/BWA ANALYSE & REFACTORING-STRATEGIE
**Datum:** 2025-12-30
**Auftraggeber:** Florian Greiner
**Analyst:** Claude Sonnet 4.5

---

## 🔍 PROBLEMSTELLUNG

User-Feedback:
> "wir haben in beiden modulen berechnungsfehler. siehe dir die tek aus global cube an, die stimmt"
> "ich will das tek bwa und alle features in drive mit einer datengrundlage arbeiten"
> "wir sind glaub ich nicht konsisten und haben keine ausreichende qualität"
> "die postgresql migration leztze woche haben wir nicht sauber hinbekommen"

**Kernanliegen:**
- TEK-Berechnungen in Web-UI und PDF-Reports sind **inkonsistent**
- Global Cube F.04a ist die **korrekte Referenz** (Dezember 2025: DB1 Gesamt 335.437,63 €)
- Wunsch nach **einer** Berechnungsgrundlage für **alle** Features
- **Kein** piecemeal fixing, sondern **stabiles sauberes Backend**

---

## 📊 ANALYSE-ERGEBNISSE

### 1. Code-Duplikation (KRITISCH!)

Es existieren **3 parallele Implementierungen** der TEK-Berechnung:

| Datei | Zeilen | Zweck | Status | Problem |
|-------|--------|-------|--------|---------|
| **api/controlling_data.py** | 270 | Wiederverwendbares Modul (TAG146) | ✅ NEU, sauber | ❌ Wird NICHT genutzt! |
| **routes/controlling_routes.py** | 572-1537 (966 Zeilen!) | Web-UI Backend | ⚠️ AKTIV | ❌ Eigene SQL-Logik |
| **scripts/send_daily_tek.py** | 91-361 (270 Zeilen) | E-Mail PDF-Reports | ⚠️ AKTIV | ❌ Eigene SQL-Logik |

**Beweis für Nicht-Nutzung:**
```python
# routes/controlling_routes.py Zeile 13
from api.controlling_data import get_tek_data  # ❌ IMPORTED BUT NOT USED!
```

### 2. Inkonsistente Formeln

**Kalkulatorische Lohnkosten** (3 verschiedene Ansätze!):

| Implementation | Formel | Problem |
|----------------|--------|---------|
| controlling_data.py (TAG146) | ~~60% pauschal vom GESAMTEN Werkstatt-Umsatz~~ | ❌ FALSCH - jetzt entfernt |
| controlling_routes.py | Rolling 3-Monats-Durchschnitt (Zeile 994-1005) | ⚠️ Komplex, historienbasiert |
| send_daily_tek.py | ❌ KEINE kalkulatorischen Kosten | ❌ Fehlt komplett |

**Global Cube Wahrheit** (laut User):
- Kalkulatorische Kosten NUR für **spezifische Lohn-Konten** (Mechanik/Karosserie)
- Konten: 840001, 840002, 840601, 840602, 840701, 840702, 841001, 841002, 841801
- Formel: **60% DB1 berechtigt** (= 40% Einsatz vom Umsatz)
- NICHT pauschal für gesamten Bereich '4-Lohn'!

### 3. PostgreSQL Migration unvollständig

**Inkonsistente Patterns:**
- `db_session()` Context Manager (controlling_data.py) ✅
- `get_db()` direkte Connection (send_daily_auftragseingang.py) ✅
- `locosoft_session()` für Locosoft-DB (controlling_routes.py) ✅
- Gemischte Placeholder-Nutzung (`%s` vs `convert_placeholders()`)

---

## 🎯 ZIEL-ARCHITEKTUR (Single Source of Truth)

```
┌─────────────────────────────────────────────────┐
│     api/controlling_data.py                     │
│     = SINGLE SOURCE OF TRUTH                    │
│     - TEK Berechnung (Umsatz/Einsatz/DB1)      │
│     - Bereiche (NW/GW/Teile/Lohn/Sonst)         │
│     - Breakeven/Prognose                        │
│     - VM/VJ-Vergleich                           │
│     - Kalkulatorische Lohnkosten (KORREKT!)    │
└─────────────────────────────────────────────────┘
                     ▲         ▲
                     │         │
        ┌────────────┴─┐   ┌───┴────────────┐
        │ Web-UI       │   │ E-Mail Reports │
        │ (Routes)     │   │ (Scripts)      │
        └──────────────┘   └────────────────┘
```

**Vorteile:**
✅ **100% Konsistenz** zwischen Web-UI und Reports
✅ **1x testen** statt 3x
✅ **1x bugfixen** statt 3x
✅ **Wartbarkeit** drastisch verbessert
✅ **Performance** durch weniger Code

---

## 🔧 REFACTORING-STRATEGIE

### Phase 1: Fundament korrigieren (JETZT)

**1.1 Kalkulatorische Lohnkosten in controlling_data.py FIX**

**Status:** ✅ Fehlerhafte Zeilen 130-138 entfernt

**NÄCHSTER SCHRITT:** Korrekte Implementierung laut Global Cube:

```python
# In api/controlling_data.py nach Zeile 128

# Kalkulatorische Lohnkosten NUR für spezifische Lohn-Konten
# Global Cube: 60% DB1 berechtigt (= 40% Einsatz) für Mechanik/Karosserie
KALK_LOHN_KONTEN = [
    840001, 840002,  # Lohn ME (Mechanik)
    840601, 840602,  # Lohn KA (Karosserie)
    840701, 840702,  # Lackierung
    841001, 841002,  # Kundendienst
    841801           # Sonstige Lohnarten
]

# Umsatz dieser Konten separat berechnen
cursor.execute(f"""
    SELECT
        SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value
                 ELSE -posted_value END) / 100.0 as lohn_umsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number = ANY(%s)
      {firma_filter_umsatz}
""", (von, bis, KALK_LOHN_KONTEN))

lohn_umsatz = float(cursor.fetchone()['lohn_umsatz'] or 0)

# 40% kalkulatorische Kosten (= 60% DB1)
if lohn_umsatz > 0:
    kalk_lohn_einsatz = lohn_umsatz * 0.40
    einsatz_dict['4-Lohn'] = einsatz_dict.get('4-Lohn', 0) + kalk_lohn_einsatz
```

**Validierung gegen Global Cube:**
- Test mit Dezember 2025 Daten
- Erwartetes Ergebnis: DB1 Gesamt = 335.437,63 €
- Service DB1 = 100.005,43 €

---

### Phase 2: controlling_routes.py Migration

**Status:** ❌ Noch nicht implementiert

**Aufwand:** ~2-3 Stunden
**Komplexität:** HOCH (966 Zeilen, viele Spezial-Features)

**Plan:**
1. `api_tek()` Funktion (Zeile 572-1537) **teilweise** ersetzen
2. **Kerndaten** von `controlling_data.py` holen:
   - Bereiche (Umsatz/Einsatz/DB1/Marge)
   - Gesamt-KPIs
   - Breakeven/Prognose
   - VM/VJ-Vergleich

3. **Spezial-Features** lokal behalten (noch nicht in controlling_data.py):
   - Stückzahlen (NW/GW aus dealer_vehicles)
   - Heute-Daten (aktueller Tagesumsatz)
   - Firmen-Vergleich (Stellantis vs Hyundai)
   - Standort-Breakevens (DEG vs LAN)
   - Vollkosten-Modus (wenn modus='voll')

**Code-Reduktion:** 966 Zeilen → ~300 Zeilen (60% weniger!)

**Risiko:**
- Web-UI erwartet sehr spezifisches Response-Format
- Umfangreiche Tests erforderlich
- Gunicorn-Restart nötig

**Prototyp erstellt:** `_controlling_routes_tek_refactored.py` (170 Zeilen Basis-Version)

---

### Phase 3: send_daily_tek.py Migration

**Status:** ❌ Noch nicht implementiert

**Aufwand:** ~1 Stunde
**Komplexität:** MITTEL (270 Zeilen, simpler)

**Plan:**
1. Eigene `get_tek_data()` Funktion (Zeile 91-361) **komplett löschen**
2. Ersetzen durch Import:
   ```python
   from scripts.tek_api_helper import get_tek_data_from_api
   ```
3. Funktion `get_tek_data_from_api()` nutzt bereits `controlling_data.py`!

**Code-Reduktion:** 361 Zeilen → ~100 Zeilen (72% weniger!)

**Risiko:** NIEDRIG
- tek_api_helper.py existiert bereits (TAG146)
- Wurde nur noch nicht integriert
- Kein Gunicorn-Restart nötig (nur Script)

**Status:** Es existiert bereits ein Plan in send_daily_tek.py Zeile 100-138 (kommentiert):
```python
# TAG147: API-basierte TEK-Daten-Abfrage
# VORHER: 230 Zeilen SQL-Queries in dieser Datei
# JETZT: 5 Zeilen API-Call über tek_api_helper.py
```

Dieser Plan wurde NIE IMPLEMENTIERT!

---

## 📋 UMSETZUNGS-ROADMAP

### ✅ Erledigt (TAG 147 - Heute)
1. ✅ Umfassende Code-Analyse (alle TEK-relevanten Dateien)
2. ✅ Problem-Identifikation (3 parallele Implementierungen)
3. ✅ Kalkulatorische Lohnkosten Bug entfernt (controlling_data.py)
4. ✅ Strategie-Dokument erstellt (diese Datei)

### 🔄 Empfohlen für NÄCHSTE Session (TAG 148)

**Priorität 1 (KRITISCH):**
1. **Kalkulatorische Lohnkosten KORREKT implementieren**
   - In `api/controlling_data.py`
   - Nur für spezifische Lohn-Konten
   - 40% Einsatz (= 60% DB1) wie Global Cube
   - **Validierung:** Test gegen Global Cube Dezember 2025

**Priorität 2 (HOCH):**
2. **send_daily_tek.py refactoren**
   - Einfacher als controlling_routes.py
   - Geringeres Risiko
   - Schneller Erfolg = Motivation!
   - Code-Reduktion: 361 → 100 Zeilen

**Priorität 3 (MITTEL):**
3. **controlling_routes.py refactoren**
   - Aufwändiger, aber wichtigster Impact
   - Umfangreiche Tests erforderlich
   - Staging-Umgebung nutzen!

**Priorität 4 (NIEDRIG):**
4. **PostgreSQL Connection standardisieren**
   - Einheitlich `db_session()` überall
   - `convert_placeholders()` entfernen (nur noch `%s`)

---

## ⚠️ RISIKEN & ABHÄNGIGKEITEN

### Hohe Risiken
1. **Web-UI Breakage**
   - controlling_routes.py ist live in Produktion
   - Änderungen können Dashboard zerstören
   - **Mitigation:** Staging-Tests, User-Abnahme

2. **Global Cube Formel unklar**
   - Welche Konten genau bekommen kalkulatorische Kosten?
   - Ist es wirklich 40% Einsatz?
   - **Mitigation:** Excel-Datei detailliert analysieren, mit User klären

### Mittlere Risiken
3. **Vollkosten-Modus**
   - controlling_data.py unterstützt `modus='voll'` theoretisch
   - Aber Implementierung fehlt/ungetestet
   - **Mitigation:** Scope auf modus='teil' begrenzen

4. **Gunicorn Neustart**
   - controlling_routes.py Änderungen = Neustart
   - Kurze Downtime
   - **Mitigation:** Wartungsfenster, User informieren

---

## 🧪 VALIDIERUNGS-STRATEGIE

### Test 1: Global Cube Abgleich (MUSS!)
```python
# Test-Skript: scripts/validate_tek_vs_global_cube.py
from api.controlling_data import get_tek_data

# Dezember 2025 Daten
data = get_tek_data(monat=12, jahr=2025, firma='0', standort='0')

# SOLL-Werte aus Global Cube F.04a
EXPECTED_DB1_GESAMT = 335_437.63
EXPECTED_DB1_SERVICE = 100_005.43

# Assertions
assert abs(data['gesamt']['db1'] - EXPECTED_DB1_GESAMT) < 100, \
    f"DB1 Gesamt Abweichung: {data['gesamt']['db1']} vs {EXPECTED_DB1_GESAMT}"

print("✅ Validierung gegen Global Cube erfolgreich!")
```

### Test 2: Web-UI Konsistenz
- TEK Dashboard aufrufen (beide Monate: aktuell + Vormonat)
- Vergleich: alte vs neue Werte
- Differenzen < 1% akzeptabel (Rundungsfehler)

### Test 3: PDF-Report Konsistenz
- E-Mail Report manuell triggern
- PDF öffnen
- Vergleich mit Web-UI (MUSS identisch sein!)

---

## 💡 DESIGN-ENTSCHEIDUNGEN

### Warum NICHT alles in controlling_data.py?

**Spezial-Features** (Stückzahlen, Heute, Vollkosten) vorerst in Routes belassen:
1. **Komplexität:** Jedes Feature braucht eigene DB-Queries
2. **Scope Creep:** Perfektionismus verhindert Fortschritt
3. **80/20-Regel:** 80% des Nutzens mit 20% des Aufwands

**Kerndaten** (Umsatz/Einsatz/DB1/Breakeven) sind das Wichtigste!

### Warum send_daily_tek.py ZUERST?

1. **Quick Win:** Einfacher als controlling_routes.py
2. **Risikoarm:** Kein Gunicorn-Restart
3. **Motivation:** Schneller Erfolg zeigt Fortschritt
4. **Validierung:** Zeigt ob controlling_data.py funktioniert

---

## 📝 OFFENE FRAGEN (für User)

1. **Kalkulatorische Lohnkosten:**
   - Welche Konten GENAU bekommen 40% Einsatz?
   - Ist die Liste vollständig: 840001, 840002, 840601, 840602, 840701, 840702, 841001, 841002, 841801?
   - Oder alle 840xxx AUSSER 847051 (Umlage)?

2. **Global Cube Formel:**
   - Spalte "DB 1 in % ber." zeigt "60" - bedeutet das 60% DB1 oder 40% Einsatz?
   - Gibt es eine Formel-Dokumentation?

3. **Deployment-Strategie:**
   - Staging-Umgebung vorhanden?
   - Wartungsfenster möglich?
   - User-Abnahme vor Produktions-Rollout?

4. **Vollkosten-Modus:**
   - Wird `modus='voll'` aktiv genutzt?
   - Oder kann Fokus auf `modus='teil'` bleiben?

---

## 🎯 ERFOLGS-KRITERIEN

### Definition of Done (DoD)
✅ Kalkulatorische Lohnkosten korrekt implementiert
✅ Global Cube Validierung erfolgreich (< 1% Abweichung)
✅ send_daily_tek.py nutzt controlling_data.py
✅ controlling_routes.py nutzt controlling_data.py
✅ Web-UI zeigt identische Werte wie PDF-Report
✅ Keine 3 parallelen Implementierungen mehr
✅ Code-Reduktion: mind. 600 Zeilen weniger

### Akzeptanzkriterien
- User bestätigt: "Zahlen sind korrekt"
- Global Cube und DRIVE zeigen gleiche Werte
- Keine Regression (alte Features funktionieren noch)

---

## 📚 REFERENZEN

**Dateien:**
- `api/controlling_data.py` (TAG146, NEU, ungenutztes Potenzial)
- `routes/controlling_routes.py` (ALT, 966 Zeilen Duplicate)
- `scripts/send_daily_tek.py` (ALT, 270 Zeilen Duplicate)
- `scripts/tek_api_helper.py` (TAG146, KORREKT, aber selten genutzt)
- `F.04.a Tägliche Erfolgskontrolle aktueller Monat (1).xlsx` (Global Cube Referenz)

**Dokumentation:**
- `docs/sessions/SESSION_WRAP_UP_TAG146.md` (Vorherige Session)
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG147.md` (Aufgabenliste)
- `docs/TAG144_POSTGRESQL_BUGFIX_HISTORY.md` (PostgreSQL Migration)

**User-Feedback:**
- "wir sind glaub ich nicht konsisten und haben keine ausreichende qualität"
- "ich jetzt nicht einzelne Kleinigkeiten fixen. wir brauchen einstabiles sauberes backend"

---

**Erstellt von:** Claude Sonnet 4.5
**Analyse-Dauer:** TAG 147 Session (2025-12-30)
**Nächste Schritte:** User-Freigabe → Phase 2 Umsetzung
