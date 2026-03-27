# 📋 SESSION WRAP-UP TAG 84

**Datum:** 27. November 2025  
**Dauer:** ~4 Stunden  
**Status:** ✅ ERFOLGREICH + Wichtige Erkenntnisse

---

## 🎯 ZIELE TAG 84

| Ziel | Status |
|------|--------|
| BWA Dashboard erstellen | ✅ |
| Rsync-Schäden reparieren | ✅ |
| BWA vs GlobalCube validieren | ✅ Analysiert |
| GlobalCube Mapping verstehen | ✅ Entschlüsselt! |

---

## 🔧 WAS WURDE GEMACHT

### 1. BWA Dashboard (NEU)

**URL:** `/controlling/bwa`  
**API:** `/controlling/api/bwa`

Vollständige BWA-Kaskade:
- Umsatzerlöse → Einsatz → **DB1**
- DB1 → Variable Kosten → **DB2**
- DB2 → Direkte Kosten → **DB3**
- DB3 → Indirekte Kosten → **Betriebsergebnis**
- Betriebsergebnis → Neutrales Ergebnis → **Unternehmensergebnis**

### 2. Rsync-Schäden repariert

| Problem | Lösung |
|---------|--------|
| `teile_api` nicht registriert | Blueprint in app.py hinzugefügt |
| Teilebestellung API-URL falsch | `/api/stellantis/` → `/api/parts/` |
| Verkauf Templates (Tag-Filter kaputt) | `git checkout d4b402e` |
| Preisradar 404 | teile_api registriert |

### 3. GlobalCube Mapping Analyse

**Wichtigste Erkenntnis:** Die **letzte Ziffer der Kontonummer** (Kostenstelle) entscheidet über die Zuordnung!

---

## 🔑 GLOBALCUBE KONTEN-MAPPING (ENTSCHLÜSSELT)

### Regel 1: Kostenstelle (letzte Ziffer)

| Letzte Ziffer | Bedeutung | BWA-Kategorie |
|---------------|-----------|---------------|
| **0** | Gesamtgeschäft / Verwaltung | **Indirekte Kosten** |
| **1** | Neuwagen | Direkt oder Variabel |
| **2** | Gebrauchtwagen | Direkt oder Variabel |
| **3** | Mechanik/Werkstatt | Direkte Kosten |
| **4** | Karosserie | Direkte Kosten |
| **5** | Teile & Zubehör | Direkte Kosten |
| **6** | Lackiererei | Direkte Kosten |
| **7** | Mietwagen | Direkte Kosten |
| **8** | Tankstelle/Versicherung | Direkte Kosten |
| **9** | Sonstige | Indirekte Kosten |

### Regel 2: Kontengruppen

| Kontenbereich | Beschreibung | BWA-Kategorie |
|---------------|--------------|---------------|
| **4151x** | Provisionen (Finanz/Vers/Vermittl.) | **Variable Kosten** |
| **491xx** | Fertigmachen | **Variable Kosten** |
| **492xx-494xx** | Fixum/Provision/Sozial | **Variable Kosten** |
| **497xx** | Kulanz | **Variable Kosten** |
| **435xx** | Training | **Variable Kosten** |
| **455xx-457xx** | Fahrzeugkosten | **Variable Kosten** |
| **487xx-488xx** | Werbekosten | **Variable Kosten** |
| **410xx-414xx** | Löhne | Direkt (wenn Stelle≠0) |
| **415xx** (ohne 4151x) | Gehälter | Direkt (wenn Stelle≠0) |
| **498xx** | **Umlage** | **Konsolidiert neutral!** |

### Regel 3: Kombination

**Variabel** = Kontengruppe ist variabel UND Kostenstelle ≠ 0  
**Direkt** = Personalkonten UND Kostenstelle ≠ 0  
**Indirekt** = Alles andere ODER Kostenstelle = 0

---

## 📊 VALIDIERUNG OKTOBER 2025

| Position | GlobalCube | DRIVE | Diff | Status |
|----------|------------|-------|------|--------|
| **Umsatz** | 2.796.329 € | 2.796.135 € | -194 € | ✅ |
| **Einsatz** | 2.319.691 € | 2.319.690 € | -1 € | ✅ |
| **DB1** | 476.638 € | 476.445 € | -193 € | ✅ |
| **Variable Kosten** | 84.861 € | 84.858 € | -3 € | ✅ |
| Fixum/Prov/Soz | 42.007 € | 42.007 € | 0 € | ✅ |
| Provisionen | 6.812 € | 6.811 € | -1 € | ✅ |
| Fertigmachen | 5.383 € | 5.382 € | -1 € | ✅ |
| Kulanz | 15.737 € | 15.736 € | -1 € | ✅ |
| Training | 4.325 € | 4.325 € | 0 € | ✅ |
| Fahrzeugkosten | 5.755 € | 5.755 € | 0 € | ✅ |
| Werbekosten | 4.843 € | 4.842 € | -1 € | ✅ |
| **Direkte Kosten** | 154.432 € | ~96.000 € | ❌ | ⚠️ TODO |
| **Indirekte Kosten** | 205.358 € | ~270.000 € | ❌ | ⚠️ TODO |

**Problem:** Direkte/Indirekte Kosten noch nicht korrekt getrennt (Kostenstellen-Logik fehlt)

---

## 📁 GEÄNDERTE DATEIEN

```
app.py                                    - teile_api Blueprint
routes/controlling_routes.py              - BWA Route + API (mit Korrekturen)
templates/controlling/bwa_dashboard.html  - NEU
templates/controlling/tek_dashboard.html  - NEU (ohne DB2)
templates/aftersales/bestellung_detail.html - API-URL Fix
templates/verkauf_auftragseingang.html    - Restored
templates/verkauf_auslieferung_detail.html - Restored
```

---

## 📂 GLOBALCUBE DATEIEN (Referenz)

```
/mnt/globalcube/GCStruct/AutohausGreiner_20250825_102814.zip  (aktuelles Mapping)
/tmp/gcstruct_aktuell/Kontenrahmen/Kontenrahmen.csv          (entpackt)
/tmp/kontenrahmen_utf8.csv                                    (UTF-8 konvertiert)
```

---

## 🎯 TODO TAG 85

### Prio 1: BWA Direkte/Indirekte Kosten korrigieren

Die API muss die **Kostenstellen-Logik** implementieren:

```sql
-- DIREKTE KOSTEN = Personalkonten (41xxxx) mit Kostenstelle 1-8
SELECT SUM(...) FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 410000 AND 449999
  AND substr(nominal_account_number, 6, 1) IN ('1','2','3','4','5','6','7','8')
  AND nominal_account_number NOT BETWEEN 415100 AND 415199;  -- ohne Provisionen

-- INDIREKTE KOSTEN = Personalkonten mit Kostenstelle 0 oder 9
-- PLUS alle anderen Kosten (43-48 mit Kostenstelle 0)
```

### Prio 2: Variable Kosten verfeinern

Stelle5 (5. Stelle) ist NICHT die Kostenstelle - es ist die **6. Stelle** (letzte)!

```sql
-- Korrekt: letzte Stelle = Kostenstelle
substr(nominal_account_number, 6, 1) -- bei 6-stelligen Konten
-- ODER: letzte Stelle dynamisch
substr(nominal_account_number, length(nominal_account_number), 1)
```

### Prio 3: 498xxx Umlage eliminieren

Bei konsolidierter Betrachtung:
- 498001 (Firma 2, 50.000 € Aufwand) eliminieren
- Gegenbuchung (Firma 1, Ertrag) eliminieren

---

## 🚀 QUICK-START TAG 85

### Befehle für Claude zum Kontext herstellen:

```bash
cd /opt/greiner-portal
source venv/bin/activate

# 1. Session Wrap-Up lesen
cat docs/SESSION_WRAP_UP_TAG84.md

# 2. GlobalCube Mapping prüfen (bereits entpackt)
head -50 /tmp/kontenrahmen_utf8.csv
grep "^415" /tmp/kontenrahmen_utf8.csv | head -20

# 3. Aktuelle BWA API prüfen
grep -n "DIREKTE\|INDIREKTE\|substr" routes/controlling_routes.py | head -30

# 4. Test BWA Oktober
curl -s "http://localhost:5000/controlling/api/bwa?von=2025-10-01&bis=2025-10-31" 2>/dev/null | python3 -m json.tool | head -40

# 5. GlobalCube Zielwerte (Oktober 2025)
echo "
GlobalCube Oktober 2025:
  Umsatz:         2.796.329 €
  Einsatz:        2.319.691 €
  DB1:              476.638 €
  Variable Kosten:   84.861 € ✓
  DB2:              391.777 €
  Direkte Kosten:   154.432 € ← TODO
  DB3:              237.345 €
  Indirekte:        205.358 € ← TODO
  Betriebsergebnis:  31.988 €
"
```

### Kontext-Nachricht für neuen Chat:

```
Wir arbeiten am BWA Dashboard (GlobalCube F.03 Ersatz).

STATUS:
- Umsatz, Einsatz, DB1, Variable Kosten → STIMMEN ✓
- Direkte/Indirekte Kosten → STIMMEN NOCH NICHT

ERKENNTNIS TAG84:
Die LETZTE ZIFFER der Kontonummer = Kostenstelle
- 0 = Indirekt
- 1-8 = Direkt
- 9 = Indirekt (Sonstige)

Die API in routes/controlling_routes.py muss angepasst werden:
- Direkte Kosten: 41xxxx mit letzter Ziffer 1-8
- Indirekte Kosten: 41xxxx mit letzter Ziffer 0 oder 9, plus Rest 4xxxxx

Lies bitte docs/SESSION_WRAP_UP_TAG84.md für Details.
```

---

## 📝 GIT COMMITS TAG84

```
63a0308 - feat(TAG84): BWA Dashboard + Fixes nach rsync
b7df008 - fix(TAG84): Alle Fixes nach rsync - teile_api registriert
78b3c42 - feat(TAG84): BWA Dashboard + GlobalCube Mapping Analyse
```

---

**Branch:** `feature/tag82-onwards`  
**Server:** 10.80.80.20  
**Pfad:** /opt/greiner-portal

*Erstellt: 27.11.2025, 13:30 Uhr*
