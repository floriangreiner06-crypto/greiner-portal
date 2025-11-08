# TAG 15 - ANLEITUNG: NOVEMBER-IMPORT FÜR ALLE KONTEN

**Datum:** 07.11.2025  
**Ziel:** November-Daten für alle fehlenden Konten importieren

---

## 📋 ÜBERSICHT

Aktuell fehlen November-Daten für:
- ⏳ Sparkasse 76003647 KK (Stand 31.10.)
- ⏳ Hypovereinsbank KK (weitere Daten ab 04.11.)
- ⏳ Weitere Genobank-Konten (22225 Immo, Darlehen)

**Neue Scripts:**
- ✅ `import_sparkasse_november.py` - Sparkasse-Import
- ✅ `import_hypovereinsbank_november.py` - Hypo-Import
- ✅ `check_november_status.py` - Status-Check

---

## 🚀 SCHRITT 1: SCRIPTS HOCHLADEN

### 1.1 Auf Ihrem lokalen Rechner

Die neuen Scripts liegen bereit. Kopieren Sie diese zum Server:

```bash
# Von Ihrem lokalen Rechner aus
scp import_sparkasse_november.py ag-admin@10.80.11.11:/opt/greiner-portal/
scp import_hypovereinsbank_november.py ag-admin@10.80.11.11:/opt/greiner-portal/
scp check_november_status.py ag-admin@10.80.11.11:/opt/greiner-portal/
```

### 1.2 Auf dem Server

```bash
# Auf Server einloggen
ssh ag-admin@10.80.11.11
cd /opt/greiner-portal

# Rechte setzen
chmod +x import_sparkasse_november.py
chmod +x import_hypovereinsbank_november.py
chmod +x check_november_status.py

# Virtual Environment aktivieren
source venv/bin/activate
```

---

## 🔍 SCHRITT 2: STATUS-CHECK

Prüfen Sie zuerst den aktuellen Stand:

```bash
python3 check_november_status.py
```

**Erwartete Ausgabe:**
```
================================================================================
📊 NOVEMBER-STATUS - ALLE KONTEN
================================================================================

🏦 Genobank
-------------------------------------------------------------------
✅ 1501500 HYU KK                | 112.798,29 EUR | 183 Trans. | 03.11. bis 06.11.
✅ 57908 KK                      | XXX.XXX,XX EUR | 207 Trans. | 03.11. bis 06.11.
⏳ 22225 Immo KK                 | XXX.XXX,XX EUR | Noch keine November-Daten (Stand: 31.10.)
⏳ Darlehen 4700057908           | XXX.XXX,XX EUR | Noch keine November-Daten (Stand: 31.10.)

🏦 Hypovereinsbank
-------------------------------------------------------------------
✅ Hypovereinsbank KK            | -193.284,00 EUR | 61 Trans. | 03.11. bis 03.11.

🏦 Sparkasse
-------------------------------------------------------------------
⏳ Sparkasse 76003647 KK         | 138,00 EUR | Noch keine November-Daten (Stand: 31.10.)

📈 GESAMT-STATISTIK
================================================================================
Aktive Konten:            10
Transaktionen gesamt:     49.781
November-Transaktionen:   451
Gesamt-Saldo:             2.604.378,52 EUR

⏳ KONTEN OHNE NOVEMBER-DATEN: 3
```

---

## 📄 SCHRITT 3: SPARKASSE IMPORTIEREN

### 3.1 Test-Modus (Dry-Run)

Erst mal testen, ohne Daten zu ändern:

```bash
python3 import_sparkasse_november.py --dry-run
```

**Was passiert:**
- ✅ Sucht nach November-PDFs
- ✅ Parst die PDFs
- ✅ Zeigt was importiert würde
- ❌ Speichert NICHT in Datenbank

### 3.2 Produktiver Import

Wenn der Dry-Run erfolgreich war:

```bash
python3 import_sparkasse_november.py
```

**Erwartete Ausgabe:**
```
🚀 SPARKASSE NOVEMBER-IMPORT
======================================================================
📊 STATUS VORHER:
   Transaktionen gesamt: 7.690
   November-Transaktionen: 0
   Aktueller Saldo: 138,00 EUR
   Letztes Datum: 2025-10-31

🔍 Suche nach Sparkasse November-PDFs...
✅ 2 PDF-Dateien gefunden
   📄 Konto_0760036467-Auszug_2025_0011.pdf
   📄 Sparkasse_Nov_01-07_2025.pdf

📄 VERARBEITE 2 PDF-DATEIEN:
----------------------------------------------------------------------
📄 Konto_0760036467-Auszug_2025_0011.pdf
✅ 35 Transaktionen gefunden
   ✅ Importiert: 35
   ⊘ Duplikate: 0

📊 STATUS NACHHER:
   Transaktionen gesamt: 7.725
   November-Transaktionen: 35
   Aktueller Saldo: XXX,XX EUR
   Letztes Datum: 2025-11-07

======================================================================
✅ IMPORT ABGESCHLOSSEN
======================================================================
Importiert:  35
Duplikate:   0
```

### 3.3 Validierung

```bash
# Prüfe Sparkasse-Transaktionen
python3 -c "
import sqlite3
conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()
c.execute('''
    SELECT COUNT(*), SUM(betrag), MIN(buchungsdatum), MAX(buchungsdatum)
    FROM transaktionen t
    JOIN konten k ON t.konto_id = k.id
    WHERE k.kontoname LIKE '%Sparkasse%' AND t.buchungsdatum >= '2025-11-01'
''')
count, summe, min_date, max_date = c.fetchone()
print(f'Sparkasse November:')
print(f'  Transaktionen: {count}')
print(f'  Summe: {summe:.2f} EUR')
print(f'  Zeitraum: {min_date} bis {max_date}')
conn.close()
"
```

---

## 🏦 SCHRITT 4: HYPOVEREINSBANK WEITERE DATEN

Hypovereinsbank hat bereits Daten bis 03.11., wir suchen nach weiteren:

### 4.1 Test-Modus

```bash
python3 import_hypovereinsbank_november.py --dry-run
```

### 4.2 Produktiver Import

```bash
python3 import_hypovereinsbank_november.py
```

**Erwartete Ausgabe:**
```
🚀 HYPOVEREINSBANK NOVEMBER-IMPORT
======================================================================
📊 STATUS VORHER:
   Transaktionen gesamt: 17.796
   November-Transaktionen: 61
   Aktueller Saldo: -193.284,00 EUR
   Letztes Datum: 2025-11-03

🔍 Suche nach Hypovereinsbank November-PDFs...
✅ 3 PDF-Dateien gefunden (ab 04.11.)
   📄 Hypovereinsbank_04.11.25.pdf
   📄 Hypovereinsbank_05.11.25.pdf
   📄 Hypovereinsbank_06.11.25.pdf

[... Import-Details ...]

✅ IMPORT ABGESCHLOSSEN
Importiert:  XX
Duplikate:   0
```

---

## 🏗️ SCHRITT 5: WEITERE GENOBANK-KONTEN

Für die anderen Genobank-Konten (22225 Immo, Darlehen) können Sie das bestehende Script verwenden:

### 5.1 Prüfe verfügbare PDFs

```bash
# Immo-Konto
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank/ \
  -name "*22225*11*.pdf" -o -name "*Immo*11.25*.pdf" 2>/dev/null

# Darlehen-Konten
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank/ \
  -name "*Darlehen*11.25*.pdf" -o -name "*4700057908*.pdf" 2>/dev/null
```

### 5.2 Import mit bestehendem V2-Script

Falls PDFs vorhanden sind:

```bash
# Test-Modus
python3 import_november_all_accounts_v2.py --dry-run

# Produktiv
python3 import_november_all_accounts_v2.py
```

**Hinweis:** Das V2-Script erkennt automatisch die richtigen Konten anhand der IBAN.

---

## ✅ SCHRITT 6: FINALER STATUS-CHECK

Nach allen Importen:

```bash
python3 check_november_status.py
```

**Erwartetes Ergebnis:**
```
📈 GESAMT-STATISTIK
================================================================================
November-Transaktionen:   500+  (vorher: 451)

✅ ALLE KONTEN HABEN NOVEMBER-DATEN!
```

---

## 📊 SCHRITT 7: VALIDIERUNG

### 7.1 Salden prüfen

```bash
./validate_salden.sh
```

### 7.2 Datenbank-Statistik

```bash
python3 -c "
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()

# Gesamt
c.execute('SELECT COUNT(*) FROM transaktionen')
total = c.fetchone()[0]

# November
c.execute('SELECT COUNT(*) FROM transaktionen WHERE buchungsdatum >= \"2025-11-01\"')
nov = c.fetchone()[0]

# Gesamt-Saldo
c.execute('SELECT SUM(betrag) FROM transaktionen')
saldo = c.fetchone()[0]

print(f'📊 DATENBANK-STATISTIK')
print(f'{'='*50}')
print(f'Transaktionen gesamt:     {total:,}')
print(f'November-Transaktionen:   {nov:,}')
print(f'Gesamt-Saldo:             {saldo:,.2f} EUR')
print(f'Stand:                    {datetime.now().strftime(\"%d.%m.%Y %H:%M:%S\")}')

conn.close()
"
```

---

## 🔧 TROUBLESHOOTING

### Problem: "PDF nicht gefunden"

```bash
# Prüfe Verzeichnisse
ls -la /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Sparkasse/
ls -la /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Hypovereinsbank/

# Suche nach November-PDFs
find /mnt/buchhaltung/Buchhaltung/Kontoauszüge/ -name "*11.25*.pdf" 2>/dev/null
```

### Problem: "Konto nicht gefunden"

```bash
# Prüfe Konten in DB
python3 -c "
import sqlite3
conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()
c.execute('SELECT id, kontoname, iban FROM konten WHERE aktiv=1')
for row in c.fetchall():
    print(f'{row[0]}: {row[1]} ({row[2]})')
conn.close()
"
```

### Problem: "Parser-Fehler"

```bash
# Teste einzelnes PDF manuell
python3 -c "
import pdfplumber
pdf = pdfplumber.open('/pfad/zur/datei.pdf')
print(pdf.pages[0].extract_text()[:500])
"
```

---

## 📝 LOGS

Alle Scripts schreiben Logs:
```bash
# Anzeigen
tail -f import_sparkasse_november.log
tail -f import_hypovereinsbank_november.log

# Fehler suchen
grep ERROR import_sparkasse_november.log
```

---

## 🎯 ZUSAMMENFASSUNG

**Nach Abschluss sollten Sie haben:**
- ✅ Sparkasse: November-Daten importiert
- ✅ Hypovereinsbank: Weitere November-Daten
- ✅ Genobank: Alle Konten auf aktuellstem Stand
- ✅ 500+ November-Transaktionen
- ✅ Alle Salden validiert

**Nächste Schritte:**
1. ⏳ Warten auf vollständige Monatsauszüge (Ende November)
2. ⏳ Parser-Integration für Sparkasse/Hypo in Hauptsystem
3. ⏳ Täglicher Import-Cronjob (optional)

---

## 🔗 DOKUMENTATION

- **SESSION_WRAP_UP_TAG14.md** - Status nach Tag 14
- **SESSION_WRAP_UP_TAG15.md** - (Wird nach diesem Tag erstellt)
- **README.md** - Allgemeine Projekt-Dokumentation

---

**Bei Fragen oder Problemen: Logfiles prüfen und Status-Check ausführen!** ✨
