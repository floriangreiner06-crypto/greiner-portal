# TODO FÜR CLAUDE - SESSION START TAG 148 (WERKSTATT-ZENTRIERT)
**Erstellt:** 2025-12-30
**Basis:** Session TAG 147 (Vollständige DRIVE Analyse - 43 Features)
**Strategie:** OPTION A - Werkstatt-zentrierter Ansatz

---

## 📋 WICHTIG: VOR BEGINN LESEN!

**Session TAG 147 Ergebnis:**
- ✅ ALLE 43 DRIVE Features analysiert (100%)
- ✅ KRITISCHSTES Problem identifiziert: **werkstatt_live_api.py (5.532 LOC!)**
- ✅ Synergien erkannt: TEK ↔ Werkstatt/Teile
- ✅ Vollständige Strategie: `TAG147_COMPLETE_DRIVE_ANALYSIS.md`

**User-Entscheidung:** OPTION A - Breiter Ansatz (Werkstatt-Modularisierung Priorität!)

---

## 🎯 ROADMAP (TAG 148-151)

### TAG 148: Fundament (2-3h) ← **DU BIST HIER**
✅ Kalkulatorische Lohnkosten korrekt implementieren
✅ Validierung gegen Global Cube
✅ Standard-Pattern definieren & dokumentieren

### TAG 149-150: Werkstatt/Teile Modularisierung (8-10h) ⭐ **HÖCHSTE PRIORITÄT**
- Erstelle `werkstatt_data.py` (800 LOC)
- Erstelle `teile_data.py` (600 LOC)
- Migriere `werkstatt_live_api.py` (5532 → 1500 LOC)
- Migriere Teile-APIs
- **Impact:** 9.400 → 3.500 LOC (63% kleiner!)

### TAG 151: TEK ↔ Aftersales Verbindung (2-3h)
- `controlling_data.py` nutzt `werkstatt_data.py` + `teile_data.py`
- TEK-Dashboard zeigt Produktivität + Lagerumschlag

### TAG 152: controlling_routes.py Refactoring (3h)
- Web-UI nutzt `controlling_data.py`

---

## 📋 AUFGABEN TAG 148

### 1. Kalkulatorische Lohnkosten KORREKT implementieren
**Status:** ⏳ Ausstehend
**Datei:** `api/controlling_data.py`
**Zeile:** Nach 128 einfügen

**User-Klarstellung:**
> "die kalkulatorischen Kosten beziehen sich auf Lohnkosten Mechanik! wir haben unter Moant kien Lohnbuchungen... aber bei den anderen service erlösarten kann es ja schon rechnungen geben"

**Global Cube Wahrheit:**
- Kalkulatorische Kosten NUR für **spezifische Lohn-Konten** (Mechanik/Karosserie)
- Spalte "DB 1 in % ber." zeigt **60** bei Lohn ME/KA
- Bedeutet: **60% DB1 berechtigt** = **40% Einsatz**

**Implementierung:**

```python
# api/controlling_data.py nach Zeile 128

# =================================================================
# KALKULATORISCHE LOHNKOSTEN (TAG148 FIX)
# =================================================================
# Global Cube: Nur für spezifische Lohn-Konten (Mechanik/Karosserie)
# Formel: 40% Einsatz = 60% DB1 berechtigt
# Konten: 840001, 840002 (ME), 840601, 840602 (KA), 840701, 840702 (Lack),
#         841001, 841002 (KD), 841801 (Sonstige)

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
        COALESCE(SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value
                          ELSE -posted_value END) / 100.0, 0) as lohn_umsatz
    FROM loco_journal_accountings
    WHERE accounting_date >= %s AND accounting_date < %s
      AND nominal_account_number = ANY(%s)
      {firma_filter_umsatz}
""", (von, bis, KALK_LOHN_KONTEN))

lohn_umsatz_row = cursor.fetchone()
lohn_umsatz = float(lohn_umsatz_row['lohn_umsatz'] or 0) if lohn_umsatz_row else 0

# 40% kalkulatorische Lohnkosten (= 60% DB1)
if lohn_umsatz > 0:
    kalk_lohn_einsatz = lohn_umsatz * 0.40
    einsatz_dict['4-Lohn'] = einsatz_dict.get('4-Lohn', 0) + kalk_lohn_einsatz
    print(f"DEBUG: Kalkulatorische Lohnkosten: Umsatz {lohn_umsatz:.2f} € → Einsatz +{kalk_lohn_einsatz:.2f} €")
```

**Validierung:**
- Test mit Dezember 2025 Daten
- Ziel: DB1 Gesamt = **335.437,63 €** (Global Cube Referenz)
- Service DB1 = **100.005,43 €**

---

### 2. Validierungs-Script erstellen
**Status:** ⏳ Ausstehend
**Datei:** `scripts/validate_tek_vs_global_cube.py` (NEU)

```python
"""
TAG148: TEK Validierung gegen Global Cube F.04a
Vergleicht controlling_data.py Output mit Excel-Referenz
"""
from api.controlling_data import get_tek_data

# Dezember 2025 Daten
print("Teste TEK-Berechnung gegen Global Cube F.04a...")
data = get_tek_data(monat=12, jahr=2025, firma='0', standort='0')

# SOLL-Werte aus Global Cube F.04a
EXPECTED_DB1_GESAMT = 335_437.63
EXPECTED_DB1_SERVICE = 100_005.43  # Zeile 68 in Excel

# DB1 Gesamt
db1_gesamt = data['gesamt']['db1']
abweichung_gesamt = abs(db1_gesamt - EXPECTED_DB1_GESAMT)
abweichung_prozent_gesamt = (abweichung_gesamt / EXPECTED_DB1_GESAMT) * 100

print(f"\n📊 DB1 GESAMT:")
print(f"  IST:       {db1_gesamt:>15,.2f} €")
print(f"  SOLL:      {EXPECTED_DB1_GESAMT:>15,.2f} €")
print(f"  Abweichung: {abweichung_gesamt:>14,.2f} € ({abweichung_prozent_gesamt:.2f}%)")

# DB1 Service (Bereich 4-Lohn)
service_bereich = next((b for b in data['bereiche'] if b['id'] == '4-Lohn'), None)
if service_bereich:
    db1_service = service_bereich['db1']
    abweichung_service = abs(db1_service - EXPECTED_DB1_SERVICE)
    abweichung_prozent_service = (abweichung_service / EXPECTED_DB1_SERVICE) * 100

    print(f"\n📊 DB1 SERVICE (4-Lohn):")
    print(f"  IST:       {db1_service:>15,.2f} €")
    print(f"  SOLL:      {EXPECTED_DB1_SERVICE:>15,.2f} €")
    print(f"  Abweichung: {abweichung_service:>14,.2f} € ({abweichung_prozent_service:.2f}%)")

# Assertions (< 1% Toleranz)
assert abweichung_prozent_gesamt < 1.0, \
    f"❌ DB1 Gesamt Abweichung zu hoch: {abweichung_prozent_gesamt:.2f}%"

assert abweichung_prozent_service < 1.0, \
    f"❌ DB1 Service Abweichung zu hoch: {abweichung_prozent_service:.2f}%"

print("\n✅ Validierung gegen Global Cube erfolgreich!")
print("   Alle Werte innerhalb 1% Toleranz.")
```

**Test:**
```bash
# Lokal (Windows)
python scripts/validate_tek_vs_global_cube.py

# Server
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && /opt/greiner-portal/venv/bin/python3 scripts/validate_tek_vs_global_cube.py"
```

---

### 3. Standard-Pattern dokumentieren
**Status:** ⏳ Ausstehend
**Datei:** `docs/DATENMODUL_PATTERN.md` (NEU)

**Inhalt:**
- Einheitliches Pattern für ALLE zukünftigen Datenmodule
- Klassen-basiert, statische Methoden
- Code-Beispiele
- Best Practices
- Testing-Guidelines

**Basis:** Siehe `TAG147_COMPLETE_DRIVE_ANALYSIS.md` Sektion "Pattern definieren"

---

### 4. Git Commit (lokal + Server)
**Status:** ⏳ Ausstehend

```bash
# 1. Lokal (Windows)
git add .
git commit -m "feat(TAG147+148): DRIVE Architektur-Analyse + TEK Kalkulatorische Lohnkosten Fix

TAG 147 - Vollständige Analyse:
- 43 DRIVE Features auf Single Source of Truth geprüft
- Kritischstes Problem: werkstatt_live_api.py (5.532 LOC)
- 67% der Features sind MONOLITH (SQL in API)
- 5 GOLD Features (TEK, Budget, Preisradar, Organigramm, Urlaub)
- Synergien erkannt: TEK ↔ Werkstatt/Teile
- Strategie: 4-Phasen-Plan (Werkstatt-zentriert)

TAG 148 - TEK Fix:
- Kalkulatorische Lohnkosten KORREKT implementiert
- Nur für spezifische Lohn-Konten (Mechanik/Karosserie)
- 40% Einsatz = 60% DB1 (wie Global Cube F.04a)
- Validierungs-Script gegen Excel-Referenz
- Target: DB1 Gesamt 335.437,63 € (Abweichung < 1%)

Dokumente:
- docs/sessions/TAG147_COMPLETE_DRIVE_ANALYSIS.md (680 Zeilen)
- docs/sessions/TAG147_ANALYSE_STRATEGIE.md (247 Zeilen)
- docs/sessions/SESSION_WRAP_UP_TAG147.md
- docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG148_UPDATED.md
- docs/DATENMODUL_PATTERN.md (NEU)
- scripts/validate_tek_vs_global_cube.py (NEU)

Impact:
- controlling_data.py: Korrekte Berechnung
- Vorbereitung für TAG149-150: Werkstatt-Modularisierung

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 2. Server
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG147+148 - DRIVE Analyse + TEK Fix'"
```

---

## 📚 REFERENZEN

**PFLICHTLEKTÜRE:**
- `docs/sessions/TAG147_COMPLETE_DRIVE_ANALYSIS.md` ⭐ Vollständige 43-Feature-Analyse
- `docs/sessions/TAG147_ANALYSE_STRATEGIE.md` - TEK-fokussiert
- `F.04.a Tägliche Erfolgskontrolle aktueller Monat (1).xlsx` - Global Cube Referenz

**Code:**
- `api/controlling_data.py` - GOLD-Standard Datenmodul
- `api/preisvergleich_service.py` - Bestes Service-Modul-Beispiel
- `api/budget_api.py` - CRUD-Pattern

---

## ⚠️ WICHTIGE HINWEISE

### PostgreSQL Array-Syntax
**WICHTIG:** `= ANY(%s)` für Array-Parameter!

```python
# RICHTIG:
cursor.execute("""
    WHERE nominal_account_number = ANY(%s)
""", (von, bis, [840001, 840002, 840601]))

# FALSCH:
cursor.execute("""
    WHERE nominal_account_number IN (%s)
""", (von, bis, [840001, 840002]))  # Funktioniert NICHT!
```

### Dezember 2025 Test-Daten
- Global Cube Zeile 115: DB1 Gesamt **335.437,63 €**
- Global Cube Zeile 68: Service **100.005,43 €**
- Toleranz: < 1% Abweichung akzeptabel

### Server-Deployment
Nach `controlling_data.py` Änderungen:
```bash
# 1. Sync
scp "api/controlling_data.py" ag-admin@10.80.80.20:/opt/greiner-portal/api/

# 2. Gunicorn Restart (WICHTIG!)
ssh ag-admin@10.80.80.20 "sudo systemctl restart greiner-portal"

# 3. Test
ssh ag-admin@10.80.80.20 "/opt/greiner-portal/venv/bin/python3 scripts/validate_tek_vs_global_cube.py"
```

---

## 🎯 ERFOLGS-KRITERIEN TAG 148

### Definition of Done:
✅ Kalkulatorische Lohnkosten korrekt implementiert
✅ Validierungs-Script funktioniert
✅ Global Cube Abgleich erfolgreich (< 1% Abweichung)
✅ Standard-Pattern dokumentiert
✅ Git Commit erstellt (lokal + Server)
✅ Gunicorn neugestartet
✅ Web-UI zeigt korrekte Werte

### Validierungs-Checklist:
- [ ] DB1 Gesamt: 335.437,63 € (±3.354 €)
- [ ] DB1 Service: 100.005,43 € (±1.000 €)
- [ ] Werkstatt Einsatz: ~104.000 € (NICHT ~32.000 €!)
- [ ] Werkstatt Marge: ~42% (NICHT ~82%!)

---

## 💡 NÄCHSTE SESSION (TAG 149-150)

**Vorbereitung:**
- Pattern aus `DATENMODUL_PATTERN.md` verstehen
- `werkstatt_live_api.py` struktur analysieren (5.532 LOC!)
- Welche Funktionen → `werkstatt_data.py`?
- Welche Funktionen → `teile_data.py`?

**Aufgaben:**
1. `werkstatt_data.py` erstellen (800 LOC)
   - `get_mechaniker_leistung()`
   - `get_auftrag_status()`
   - `get_kapazitaet_forecast()`

2. `teile_data.py` erstellen (600 LOC)
   - `get_renner_penner()`
   - `get_fehlende_teile()`
   - `get_serviceberater_stats()`

3. Migration: werkstatt_live_api.py (5532 → 1500 LOC)

**Impact:** 9.400 → 3.500 LOC (63% Reduktion!)

---

**Erstellt von:** Claude Sonnet 4.5
**Strategie:** OPTION A - Werkstatt-zentrierter Ansatz
**Nächste Session:** TAG 148 - TEK Fix + Pattern
**Geschätzter Aufwand:** 2-3 Stunden
