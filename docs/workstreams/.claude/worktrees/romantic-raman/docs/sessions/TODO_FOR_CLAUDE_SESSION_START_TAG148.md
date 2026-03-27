# TODO FÜR CLAUDE - SESSION START TAG 148
**Erstellt:** 2025-12-30
**Basis:** Session TAG 147 (Umfassende Analyse & Strategie)

---

## 📋 WICHTIG: VOR BEGINN LESEN!

**Session TAG 147 Ergebnis:**
- ✅ Umfassende Code-Analyse abgeschlossen
- ✅ Strategie-Dokument erstellt: `TAG147_ANALYSE_STRATEGIE.md`
- ⚠️ **KEINE Produktions-Änderungen deployed!**
- ⚠️ Nur lokale Änderungen (controlling_data.py - Zeilen 130-138 entfernt)

**User-Anforderung:**
> "ich will das tek bwa und alle features in drive mit einer datengrundlage arbeiten"
> "Analyse und Strategie bitte. ich jetzt nicht einzelne Kleinigkeiten fixen. wir brauchen einstabiles sauberes backend"

**Status:** Analyse abgeschlossen → Jetzt Implementierung!

---

## 🎯 OFFENE AUFGABEN (PRIORITÄT)

### KRITISCH (Priorität 1) - TAG 148

#### 1. User-Freigabe einholen
**Status:** ⏳ Ausstehend
**Was:** Strategie-Dokument mit User besprechen

**Zu klären:**
1. **Kalkulatorische Lohnkosten - Konten-Liste:**
   - Sind diese Konten korrekt?
     - 840001, 840002 (Lohn ME - Mechanik)
     - 840601, 840602 (Lohn KA - Karosserie)
     - 840701, 840702 (Lackierung)
     - 841001, 841002 (Kundendienst)
     - 841801 (Sonstige)
   - Oder: Alle 840xxx AUSSER 847051 (Umlage)?

2. **Formel-Bestätigung:**
   - Global Cube "DB 1 in % ber." = 60
   - Bedeutet: 60% DB1 = 40% Einsatz vom Umsatz?

3. **Deployment-Strategie:**
   - Staging-Umgebung vorhanden?
   - Wartungsfenster erforderlich?
   - User-Abnahme vor Produktions-Rollout?

**Dokument:** `docs/sessions/TAG147_ANALYSE_STRATEGIE.md`

---

#### 2. Kalkulatorische Lohnkosten KORREKT implementieren
**Status:** ⏳ Ausstehend (nach User-Freigabe)
**Datei:** `api/controlling_data.py`
**Zeilen:** Nach 128 einfügen

**Code-Vorlage:**
```python
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

**Validation Target:**
- DB1 Gesamt: **335.437,63 €** (Global Cube Dezember 2025)
- DB1 Service: **100.005,43 €**

---

#### 3. Validierungs-Script erstellen
**Status:** ⏳ Ausstehend
**Datei:** `scripts/validate_tek_vs_global_cube.py` (NEU)

**Zweck:**
- Automatischer Abgleich gegen Global Cube Excel
- Toleranz: < 1% Abweichung akzeptabel

**Code-Vorlage:**
```python
"""
TAG148: TEK Validierung gegen Global Cube
Vergleicht controlling_data.py Output mit Excel-Referenz
"""
from api.controlling_data import get_tek_data

# Dezember 2025 Daten
data = get_tek_data(monat=12, jahr=2025, firma='0', standort='0')

# SOLL-Werte aus Global Cube F.04a
EXPECTED_DB1_GESAMT = 335_437.63
EXPECTED_DB1_SERVICE = 100_005.43

# Assertions
db1_gesamt = data['gesamt']['db1']
abweichung_gesamt = abs(db1_gesamt - EXPECTED_DB1_GESAMT)

print(f"DB1 Gesamt (IST):  {db1_gesamt:,.2f} €")
print(f"DB1 Gesamt (SOLL): {EXPECTED_DB1_GESAMT:,.2f} €")
print(f"Abweichung:        {abweichung_gesamt:,.2f} € ({abweichung_gesamt/EXPECTED_DB1_GESAMT*100:.2f}%)")

assert abweichung_gesamt < 1000, \
    f"❌ DB1 Gesamt Abweichung zu hoch: {abweichung_gesamt:,.2f} €"

print("✅ Validierung gegen Global Cube erfolgreich!")
```

**Test:**
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && /opt/greiner-portal/venv/bin/python3 scripts/validate_tek_vs_global_cube.py"
```

---

### HOCH (Priorität 2) - TAG 148 oder TAG 149

#### 4. send_daily_tek.py refactoren
**Status:** ⏳ Geplant
**Aufwand:** ~1 Stunde
**Risiko:** NIEDRIG

**Änderungen:**
1. **Löschen:** Eigene `get_tek_data()` Funktion (Zeile 91-361)
2. **Ersetzen durch:**
   ```python
   from scripts.tek_api_helper import get_tek_data_from_api

   # Statt 270 Zeilen SQL - nur noch 5 Zeilen API-Call:
   tek_data = get_tek_data_from_api(
       monat=monat,
       jahr=jahr,
       standort=standort_param  # None/'ALL'/'DEG'/'LAN'
   )
   ```

**Code-Reduktion:** 361 Zeilen → ~100 Zeilen (72% weniger!)

**Test:**
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && /opt/greiner-portal/venv/bin/python3 scripts/send_daily_tek.py --force"
```

**Validierung:**
- PDF öffnen
- Vergleich mit Web-UI (MUSS identisch sein!)
- Werkstatt-Werte prüfen (Einsatz ~104k €, nicht ~32k €)

---

### MITTEL (Priorität 3) - TAG 149+

#### 5. controlling_routes.py refactoren
**Status:** 🔄 Prototyp vorhanden
**Aufwand:** ~3 Stunden
**Risiko:** MITTEL-HOCH

**Datei:** `routes/controlling_routes.py`
**Funktion:** `api_tek()` (Zeile 572-1537)
**Prototyp:** `routes/_controlling_routes_tek_refactored.py`

**Strategie:**
1. **Kerndaten** von controlling_data.py holen:
   - Bereiche (Umsatz/Einsatz/DB1/Marge)
   - Gesamt-KPIs
   - Breakeven/Prognose
   - VM/VJ-Vergleich

2. **Spezial-Features** lokal ergänzen:
   - Stückzahlen (NW/GW aus dealer_vehicles)
   - Heute-Daten (aktueller Tagesumsatz)
   - Firmen-Vergleich (Stellantis vs Hyundai)
   - Standort-Breakevens (DEG vs LAN)
   - Vollkosten-Modus (wenn modus='voll')

**Code-Reduktion:** 966 Zeilen → ~300 Zeilen (68% weniger!)

**Risiko-Mitigation:**
- ⚠️ Staging-Tests erforderlich!
- ⚠️ Web-UI Response-Format EXAKT einhalten!
- ⚠️ Gunicorn-Restart nötig → Wartungsfenster
- ⚠️ User-Abnahme VOR Produktions-Rollout

**Test-Checklist:**
- [ ] TEK Dashboard lädt korrekt
- [ ] Bereiche zeigen Daten (NW/GW/Teile/Lohn/Sonst)
- [ ] Stückzahlen werden angezeigt
- [ ] Heute-Daten sichtbar (wenn aktueller Monat)
- [ ] Vormonat/Vorjahr-Vergleich korrekt
- [ ] Firma-Filter funktioniert (Stellantis/Hyundai)
- [ ] Standort-Filter funktioniert (DEG/LAN)
- [ ] Umlage-Option funktioniert (mit/ohne)
- [ ] Vollkosten-Modus funktioniert (wenn genutzt)

---

## 📂 DATEIEN-ÜBERSICHT

### Geändert (lokal, NICHT deployed):
- `api/controlling_data.py` (Zeilen 130-138 entfernt)

### Neu erstellt (lokal):
- `docs/sessions/TAG147_ANALYSE_STRATEGIE.md` ⭐ WICHTIG - Strategie lesen!
- `docs/sessions/SESSION_WRAP_UP_TAG147.md`
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG148.md` (diese Datei)
- `routes/_controlling_routes_tek_refactored.py` (Prototyp)

### Zu ändern (TAG 148):
1. `api/controlling_data.py` (Kalkulatorische Lohnkosten implementieren)
2. `scripts/validate_tek_vs_global_cube.py` (NEU erstellen)
3. `scripts/send_daily_tek.py` (Refactoring)

### Zu ändern (TAG 149):
4. `routes/controlling_routes.py` (Refactoring)

---

## 🧪 VALIDIERUNGS-CHECKLIST

### Phase 1 (MUSS):
- [ ] User-Freigabe für Strategie
- [ ] Kalkulatorische Lohnkosten korrekt implementiert
- [ ] Validierungs-Script erstellt
- [ ] Test gegen Global Cube erfolgreich (< 1% Abweichung)
- [ ] Git Commit lokal erstellt

### Phase 2 (SOLLTE):
- [ ] send_daily_tek.py refactored
- [ ] E-Mail Report getestet
- [ ] Vergleich mit Web-UI (MUSS identisch sein!)
- [ ] Git Commit lokal + Server

### Phase 3 (KANN):
- [ ] controlling_routes.py refactored (Staging)
- [ ] Umfangreiche Web-UI Tests
- [ ] User-Abnahme
- [ ] Produktions-Rollout
- [ ] Git Commit lokal + Server

---

## ⚠️ WICHTIGE HINWEISE

### NICHT VERGESSEN:
1. **TAG147_ANALYSE_STRATEGIE.md** lesen vor Session-Start!
2. **User-Freigabe** einholen bevor Code geschrieben wird!
3. **Validierung gegen Global Cube** ist PFLICHT!
4. **Server-Sync nach jedem Commit:**
   ```bash
   ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG148 - [Beschreibung]'"
   ```

### Git Workflow:
```bash
# 1. Lokal (Windows)
git add .
git commit -m "feat(TAG148): Kalkulatorische Lohnkosten korrekt implementiert

- Nur für spezifische Lohn-Konten (Mechanik/Karosserie)
- 40% Einsatz = 60% DB1 wie Global Cube
- Validierungs-Script gegen Excel-Referenz

Validierung:
- DB1 Gesamt: 335.437,63 € (Ziel erreicht!)
- Abweichung < 0,1%

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 2. Server
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG148 - Kalkulatorische Lohnkosten Fix'"
```

---

## 📚 REFERENZEN

**Strategie-Dokument (PFLICHTLEKTÜRE!):**
- `docs/sessions/TAG147_ANALYSE_STRATEGIE.md`

**Session Wrap-Ups:**
- `docs/sessions/SESSION_WRAP_UP_TAG147.md`
- `docs/sessions/SESSION_WRAP_UP_TAG146.md`

**Global Cube Referenz:**
- `F.04.a Tägliche Erfolgskontrolle aktueller Monat (1).xlsx` (im Sync-Verzeichnis)

**Code-Referenzen:**
- `api/controlling_data.py` (Single Source of Truth - TO BE)
- `scripts/tek_api_helper.py` (Best Practice Beispiel)
- `routes/_controlling_routes_tek_refactored.py` (Prototyp)

---

## 🎯 ERFOLGS-KRITERIEN

### Definition of Done (DoD) - Phase 1:
✅ User-Freigabe erhalten
✅ Kalkulatorische Lohnkosten korrekt implementiert
✅ Validierungs-Script funktioniert
✅ Global Cube Abgleich erfolgreich (< 1% Abweichung)
✅ Git Commit erstellt (lokal + Server)

### Definition of Done (DoD) - Phase 2:
✅ send_daily_tek.py nutzt controlling_data.py
✅ E-Mail PDF identisch mit Web-UI
✅ Code-Reduktion nachgewiesen (361 → 100 Zeilen)

### Definition of Done (DoD) - Phase 3:
✅ controlling_routes.py nutzt controlling_data.py
✅ Web-UI Tests erfolgreich
✅ Keine Regression
✅ User-Abnahme positiv
✅ Produktions-Rollout erfolgreich

---

## 💡 STRATEGISCHE ZIELE

**Kurzfristig (TAG 148):**
- Korrekte Berechnung implementieren
- Validierung gegen Referenz
- Quick Win mit send_daily_tek.py

**Mittelfristig (TAG 149):**
- controlling_routes.py Migration
- 100% Konsistenz Web-UI ↔ Reports
- Code-Duplikation eliminiert

**Langfristig (TAG 150+):**
- Automatische Tests für TEK
- CI/CD Pipeline
- Dokumentation für Formeln
- Performance-Optimierung

---

**Erstellt von:** Claude Sonnet 4.5
**Basis:** TAG 147 Analyse & Strategie
**Nächste Session:** TAG 148 - Phase 1 Implementierung
**Geschätzter Aufwand:** 2-3 Stunden (Phase 1)
