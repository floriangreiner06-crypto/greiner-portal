# BUG-FIX REPORT: Konto-Vermischung Tag 14

**Datum:** 07.11.2025  
**Schweregrad:** 🚨 KRITISCH  
**Status:** ✅ BEHOBEN  

---

## 🐛 Problem

### Symptom
150 November-Transaktionen wurden dem **falschen Konto** zugeordnet:

```
Falsch importiert zu:
  Konto ID 6: 22225 Immo KK
  IBAN: DE64741900000000022225
  Inhaber: Greiner Immobilienverwaltungs GmbH & Co. KG

Transaktionen gehören aber zu:
  Konto ID 5: 57908 KK  
  IBAN: DE27741900000000057908
  Inhaber: Autohaus Greiner GmbH & Co. KG
```

### Betroffene Transaktionen
```
Zeitraum:     03.11.2025 - 06.11.2025
Anzahl:       150 Transaktionen
Summe:        +66.973,80 EUR
Transaktionen:
  - Auto1 European Cars B.V. (Fahrzeugzahlungen)
  - UniCredit/aufinity Group (Finanzierung)
  - Autohaus Greiner GmbH & Co. KG (Transfers)
  → Alle gehören zum AUTOHAUS, nicht zur IMMOBILIENVERWALTUNG!
```

---

## 🔍 Root Cause Analyse

### Ursache
**Import-Script V1 nutzte Verzeichnis-basiertes Mapping:**

```python
# import_november_all_accounts.py (V1 - FEHLERHAFT)

KONTEN = {
    'Genobank Autohaus Greiner': ['22225'],  # ← PROBLEM!
    ...
}

# Logic:
# 1. PDF gefunden in: "Genobank Autohaus Greiner/"
# 2. Mapping sagt: Verzeichnis → Kontonummer "22225"
# 3. Script sucht in DB: kontonummer LIKE '%22225%'
# 4. Findet: Konto ID 6 (22225 Immo KK)  ← FALSCH!
# 5. Importiert 150 Transaktionen zu Konto 6  ← FEHLER!
```

### Warum passierte das?

**Zwei Konten mit ähnlichen Endziffern:**

```
Konto 5 (57908 KK):
  IBAN: DE27741900000000057908  ← Endet auf 57908
  Inhaber: Autohaus Greiner GmbH & Co. KG

Konto 6 (22225 Immo KK):
  IBAN: DE64741900000000022225  ← Endet auf 22225  
  Inhaber: Greiner Immobilienverwaltungs GmbH & Co. KG
```

**Verwirrende Verzeichnisnamen:**
```
/Genobank Autohaus Greiner/
  └── Genobank Auszug Autohaus Greiner 06.11.25.pdf
      └── IBAN im PDF: DE27...57908  ← Konto 5!
      └── Script nutzte aber: "22225" aus Mapping  ← Konto 6! (FALSCH)
```

### Timeline
```
20:00 - Import-Script V1 ausgeführt
20:03 - 150 Transaktionen importiert zu Konto 6 (22225 Immo)
20:29 - Validierung: User bemerkt Auto1-Transaktionen bei "Immo KK"
20:35 - Root Cause identifiziert: Verzeichnis-Mapping falsch
20:43 - Fix angewendet: 150 Transaktionen verschoben zu Konto 5
20:50 - Import-Script V2 entwickelt (IBAN-basiert)
```

---

## ✅ Fix Applied

### Schritt 1: Daten-Korrektur

**Backup erstellt:**
```
data/greiner_controlling.db.backup_fix_20251107_204343
```

**SQL-Update ausgeführt:**
```sql
UPDATE transaktionen
SET konto_id = 5  -- 57908 KK (Autohaus)
WHERE konto_id = 6  -- 22225 Immo KK
  AND buchungsdatum >= '2025-11-01'
  AND pdf_quelle LIKE '%Autohaus Greiner%'
```

**Ergebnis:**
```
✅ 150 Transaktionen verschoben
✅ Konto 5 (57908 KK): 150 November-Transaktionen
✅ Konto 6 (22225 Immo): 0 November-Transaktionen
```

### Schritt 2: Code-Fix

**Neues Script: `import_november_all_accounts_v2.py`**

**Hauptänderungen:**

```python
# ALT (V1 - FEHLERHAFT):
KONTEN = {
    'Genobank Autohaus Greiner': ['22225'],  # Hardcoded!
}
def get_konto_id(self, kontonummer: str):
    # Sucht in DB: kontonummer LIKE '%22225%'
    # → Findet falsches Konto!

# NEU (V2 - KORREKT):
def get_konto_id_by_iban(self, iban: str):
    """
    Ermittelt konto_id anhand vollständiger IBAN aus PDF
    
    1. Parser extrahiert IBAN aus PDF: "DE27741900000000057908"
    2. Match gegen konten.iban in DB
    3. → Findet korrektes Konto 5 (57908 KK)
    """
    iban = iban.replace(' ', '').strip().upper()
    
    # Direkt aus IBAN-Cache (geladen beim Start)
    if iban in self.iban_cache:
        return self.iban_cache[iban]
    
    return None
```

**Neue Features:**
- ✅ IBAN-Cache beim Start geladen (Performance)
- ✅ Keine hardcodierten Mappings mehr
- ✅ PDF bestimmt das Zielkonto (nicht das Verzeichnis)
- ✅ Log zeigt IBAN-Match: `DE27...57908 → Konto 5 (57908 KK)`

---

## ✅ Validierung

### Nach dem Fix:

```bash
./validate_salden.sh
```

**Ergebnis:**
```
✅ Konto 5 (57908 KK - Autohaus):
   - 150 November-Transaktionen
   - Summe: +66.973,80 EUR
   - Zeitraum: 2025-11-03 bis 2025-11-06

✅ Konto 6 (22225 Immo KK):
   - 0 November-Transaktionen
   - (Korrekt - keine Immobilien-PDFs vorhanden)

✅ Neueste Transaktionen:
   Alle zeigen jetzt: "Genobank Auto Greiner 57908 KK" ✓
```

**SQL-Check:**
```sql
-- Alle November-Transaktionen mit "Auto1" oder "Autohaus"
SELECT konto_id, COUNT(*)
FROM transaktionen
WHERE buchungsdatum >= '2025-11-01'
  AND (verwendungszweck LIKE '%Auto1%' 
       OR verwendungszweck LIKE '%Autohaus Greiner%')
GROUP BY konto_id;

Ergebnis:
  konto_id 5: 48 Transaktionen  ✅ (57908 KK - Autohaus)
  konto_id 6: 0 Transaktionen   ✅ (22225 Immo - korrekt leer)
```

---

## 🎯 Prevention

### Verhindere zukünftige Fehler:

**1. Nutze immer IBAN-basiertes Matching**
```python
# ✅ RICHTIG:
iban = parser.iban  # Aus PDF
konto_id = get_konto_id_by_iban(iban)

# ❌ FALSCH:
directory_name = "Genobank Autohaus Greiner"
konto_id = MAPPING[directory_name]  # Hardcoded!
```

**2. Validiere IBAN-Extraktion**
```python
if not iban:
    logger.error("❌ Keine IBAN im PDF!")
    return 0

logger.info(f"✓ IBAN-Match: {iban} → Konto {konto_id}")
```

**3. Log zeigt Konto-Zuordnung**
```
✓ IBAN-Match: DE27741900000000057908 → Konto 5 (57908 KK - Autohaus)
```

**4. Regelmäßige Validierung**
```bash
# Nach jedem Import:
./validate_salden.sh

# Prüfe ob Transaktionen sinnvoll sind:
# - Auto1 bei Autohaus? ✅
# - Auto1 bei Immobilien? ❌ Fehler!
```

---

## 📚 Lessons Learned

### Was haben wir gelernt?

1. **❌ Verzeichnisnamen sind unzuverlässig**
   - Namen sind inkonsistent
   - Mapping muss manuell gepflegt werden
   - Fehleranfällig bei ähnlichen Kontonummern

2. **✅ IBAN ist die Single Source of Truth**
   - Eindeutig
   - Steht im PDF
   - Direkt in DB matchbar

3. **✅ Parser müssen IBAN extrahieren**
   - Erste Priorität im Parsing
   - Validierung vor Import

4. **✅ Logs müssen Zuordnung zeigen**
   - User kann Fehler sofort erkennen
   - "Auto1 bei Immobilien" ist offensichtlich falsch

5. **✅ Validierung ist essentiell**
   - Salden prüfen
   - Neueste Transaktionen prüfen
   - Verwendungszweck auf Plausibilität prüfen

---

## 📋 Checklist für künftige Imports

- [ ] Parser extrahiert IBAN ✅
- [ ] Konto-Matching anhand IBAN (nicht Verzeichnis) ✅
- [ ] Log zeigt IBAN → Konto-Zuordnung ✅
- [ ] Nach Import: validate_salden.sh ✅
- [ ] Neueste Transaktionen prüfen ✅
- [ ] Verwendungszweck auf Plausibilität prüfen ✅
- [ ] Bei Unsicherheit: Backup vorhanden ✅

---

## 📊 Impact Assessment

### Betroffene Daten:
```
Zeitraum:     07.11.2025 20:00-20:50 (50 Min)
Transaktionen: 150 (von 49.622 gesamt = 0,3%)
Konten:       2 (Konto 5 und 6)
Nutzer-Impact: Mittel (Salden waren falsch, aber erkennbar)
```

### Severity:
```
🚨 KRITISCH weil:
  - Falsche Salden in zwei Konten
  - Falsche Zuordnung Autohaus ↔ Immobilien
  - Könnte zu falschen Geschäftsentscheidungen führen

✅ BEHOBEN innerhalb 50 Min:
  - Daten korrigiert
  - Code gefixt
  - Validiert
  - Dokumentiert
```

---

## 🔗 Referenzen

### Dateien:
- `import_november_all_accounts.py` (V1 - deprecated)
- `import_november_all_accounts_v2.py` (V2 - IBAN-basiert)
- `genobank_universal_parser.py` (IBAN-Extraktion)

### Backups:
- `data/greiner_controlling.db.backup_fix_20251107_204343` (vor Korrektur)

### Session Wrap-ups:
- `SESSION_WRAP_UP_TAG14.md` (wird aktualisiert mit Bug-Fix)

### Logs:
- `november_import.log` (V1 - zeigt fehlerhaften Import)
- `november_import_v2.log` (V2 - IBAN-basiert)

---

**Status:** ✅ RESOLVED  
**Behoben von:** Claude AI  
**Behoben am:** 07.11.2025 20:50  
**Verifiziert:** Ja (validate_salden.sh)  
**Deployed:** Ja (import_november_all_accounts_v2.py produktiv)

---

_Dieser Bug-Fix-Report dokumentiert einen kritischen Fehler und dessen Behebung, damit ähnliche Fehler in Zukunft vermieden werden können._
