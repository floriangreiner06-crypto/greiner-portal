# Session Wrap-Up - Tag 31: Bankenspiegel Startsaldo-Problem Analyse

**Datum:** 2025-11-12  
**Dauer:** ~3 Stunden  
**Status:** ⚠️ Parser funktioniert, aber Kontenstruktur muss geklärt werden

---

## 🎯 Ausgangslage

**User-Test steht bevor** - Bankenspiegel muss funktionieren!

**Problem:** Frontend zeigt für 11.11.2025:
- Filter "Alle Konten" → 41 Transaktionen ✅
- Filter "Konto 57908" → 0 Transaktionen ❌

---

## 🔍 Durchgeführte Analysen

### 1. API-Statistik Bug gefunden und gefixt

**Problem:** API berechnete Statistik nur über limitierte/gepagte Transaktionen

**Fix:** Separate Aggregat-Query für Statistik über ALLE gefilterten Transaktionen
```python
# Vorher (FALSCH):
if transaktionen:
    summe_einnahmen = sum(t['betrag'] for t in transaktionen if t['betrag'] > 0)

# Nachher (KORREKT):
stats_query = """
    SELECT 
        SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as summe_einnahmen,
        SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as summe_ausgaben,
        SUM(betrag) as saldo
    FROM v_transaktionen_uebersicht
    WHERE 1=1
"""
```

**Datei:** `api/bankenspiegel_api.py` (Zeile ~401)

---

### 2. Startsaldo-Problem identifiziert

**Symptom:** Alle Salden sind falsch

**Root Cause:** Parser findet Startsaldo nicht im PDF

**PDF-Struktur Problem:**
```
Seite 1: (Endsaldo) +140.122,61 EUR
...
Seite 4: (Startsaldo)
         +173.262,27EUR
```

**Herausforderungen:**
1. Startsaldo steht auf **letzter Seite** (nicht erster)
2. Startsaldo und Betrag sind auf **verschiedenen Zeilen** (Zeilenumbruch!)
3. Format: `(Startsaldo)\n+173.262,27EUR` (OHNE Leerzeichen!)

---

### 3. Parser-Fix implementiert

**Datei:** `scripts/imports/genobank_universal_parser.py`

**Änderung:** Multiline-Regex statt Zeile-für-Zeile Suche
```python
# ALT (funktioniert nicht):
for line in lines:
    if '(Startsaldo)' in line:
        saldo_match = re.search(r'\+?([-\d.,]+)\s+EUR', line)

# NEU (funktioniert):
full_text_search = '\n'.join(lines)
if '(Startsaldo)' in full_text_search:
    saldo_match = re.search(r'\(Startsaldo\)\s*\+?([-\d.,]+)\s*EUR', full_text_search)
```

**Status:** ✅ Parser findet jetzt Startsaldo korrekt

---

### 4. Kontenstruktur-Problem entdeckt

**KRITISCH:** Dateinamen sind irreführend!
```
PDF-Name: "Genobank Auszug AUTOHAUS Greiner 11.11.25.pdf"
IBAN im PDF: DE27741900000000057908
Kontoinhaber: Autohaus Greiner GmbH & Co. KG
Endsaldo: 68.275,46 EUR ✅

PDF-Name: "Genobank Auszug AUTO Greiner 11.11.25.pdf"  
IBAN im PDF: DE68741900000001501500
Kontoinhaber: Auto Greiner GmbH & Co. KG
Endsaldo: 140.122,61 EUR ✅
```

**BEIDE Parser-Ergebnisse sind KORREKT!**

**ABER:** In der DB gibt es Verwirrung mit Konto-IDs:
- Konto 5, 15, 16 haben ähnliche Kontonummern
- Mehrere Konten enden mit "057908" (Darlehenskonten!)
- Mögliche Duplikate in der DB

---

## 📊 Kontenstruktur laut Mail (30.10.2025)
```
ID  5: DE27741900000000057908    - Genobank Auto Greiner - Hauptkonto
ID  6: DE64741900000000022225    - Genobank Autohaus Greiner - Hauptkonto
ID  7: DE94741900000020057908    - Genobank Darlehenskonten (20057908)
ID  8: DE96741900001700057908    - Genobank Greiner Immob.Verw (1700057908)
ID 15: DE68741900000001501500    - 1501500 HYU
ID 17: DE58741900004700057908    - 4700057908
ID 20: DE41741900000120057908    - KfW Darlehen 120057908
```

**Problem:** Viele Konten enden mit "057908" → Verwechslungsgefahr!

---

## 📁 Geänderte Dateien
```
api/bankenspiegel_api.py                              # Statistik-Fix
scripts/imports/genobank_universal_parser.py          # Startsaldo-Fix
scripts/imports/genobank_universal_parser.py.backup_* # Mehrere Backups
```

---

## ⚠️ OFFENE PUNKTE (KRITISCH für User-Test!)

### 1. Kontenstruktur klären

**User hat Kontoaufstellung.xlsx hochgeladen** - MUSS analysiert werden!

**Fragen:**
- Sind alle Konten in der DB korrekt angelegt?
- Gibt es Duplikate?
- Stimmen die IBANs?
- Welche Konten sollen im Frontend sichtbar sein?

### 2. Datenbank-Status prüfen
```bash
# Prüfe alle 057908-Konten
sqlite3 data/greiner_controlling.db "
SELECT id, kontoname, iban, 
  (SELECT COUNT(*) FROM transaktionen WHERE konto_id = konten.id) as trans
FROM konten 
WHERE iban LIKE '%057908%';
"

# Prüfe Duplikate
sqlite3 data/greiner_controlling.db "
SELECT iban, COUNT(*) 
FROM konten 
GROUP BY iban 
HAVING COUNT(*) > 1;
"
```

### 3. November-Transaktionen Status
```bash
sqlite3 data/greiner_controlling.db "
SELECT 
    buchungsdatum,
    COUNT(*) as transaktionen,
    COUNT(DISTINCT konto_id) as konten
FROM transaktionen
WHERE buchungsdatum >= '2025-11-01'
GROUP BY buchungsdatum
ORDER BY buchungsdatum;
"
```

---

## 🔄 Nächste Schritte für neuen Chat

### PRIORITÄT 1: Kontoaufstellung analysieren
```bash
python3 << 'EOF'
import pandas as pd
xlsx = pd.ExcelFile('/mnt/user-data/uploads/Kontoaufstellung.xlsx')
for sheet in xlsx.sheet_names:
    df = pd.read_excel(xlsx, sheet)
    print(df.to_string())
EOF
```

### PRIORITÄT 2: DB mit SOLL-Zustand abgleichen
- Kontoaufstellung.xlsx ist die Wahrheit
- DB-Konten bereinigen/korrigieren
- Duplikate entfernen

### PRIORITÄT 3: Re-Import November
- Nach Konten-Bereinigung
- Mit korrigiertem Parser
- Alle Konten neu importieren

---

## 💡 Erkenntnisse

1. ✅ **API-Statistik-Bug** ist gefixt
2. ✅ **Parser findet Startsaldo** jetzt korrekt (Multiline-Regex)
3. ⚠️ **Kontenstruktur** ist das Hauptproblem
4. ⚠️ **Dateinamen** sind irreführend (Autohaus vs Auto)
5. 📄 **Kontoaufstellung.xlsx** ist der Schlüssel zur Lösung

---

## 🚫 KEIN User-Test bis:

- [ ] Kontoaufstellung.xlsx analysiert
- [ ] DB-Konten bereinigt
- [ ] November-Daten neu importiert
- [ ] Frontend zeigt korrekte Salden für ALLE Konten

---

**Session Ende:** 2025-11-12 ~10:40 Uhr  
**Nächste Session:** Kontostruktur-Bereinigung mit Kontoaufstellung.xlsx als Master
