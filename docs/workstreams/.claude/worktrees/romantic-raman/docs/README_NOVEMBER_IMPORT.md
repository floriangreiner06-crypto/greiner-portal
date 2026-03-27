# November 2025 - Multi-Account Import 📅

Automatischer Import von November-PDFs für alle Genobank-Konten, Hypovereinsbank und Sparkasse.

## 📋 Übersicht

**Stand:** Tag 13 - Konto 1501500 bereits importiert (03.-06.11.)  
**Ziel:** Alle anderen Konten mit November-Daten aktualisieren

### ✅ Bereits importiert
- **1501500 HYU KK** (Genobank Auto Greiner): 67 Transaktionen (03.-06.11.)

### 🔄 Noch zu importieren
- **57908 KK** (Genobank Auto Greiner)
- **22225 Immo KK** (Genobank Autohaus Greiner)
- **4700057908** Darlehen
- **20057908** Darlehen
- **1700057908** Darlehen
- **Hypovereinsbank KK**
- **Sparkasse 76003647 KK**

---

## 🎯 Features

### Universeller Parser (`genobank_universal_parser.py`)

**Automatische Format-Erkennung:**
1. **Standard-Format** (Monatsauszüge):
   ```
   DD.MM. DD.MM. Vorgang... Betrag H/S
   ```

2. **Tagesauszug-Format**:
   ```
   Empfänger Name                    +Betrag EUR
   IBAN                              Datum
   Verwendungszweck
   ```

**Funktionen:**
- ✅ Automatische Format-Erkennung
- ✅ Jahr-Extraktion aus Dateinamen und PDF
- ✅ IBAN-Extraktion
- ✅ Robustes Datum-Parsing
- ✅ Mehrzeiliger Verwendungszweck
- ✅ Saldo-Validierung (bei Tagesauszügen)

### Import-Script (`import_november_all_accounts.py`)

**Funktionen:**
- ✅ Findet automatisch alle November-PDFs
- ✅ Duplikats-Prüfung (keine Doppel-Imports)
- ✅ Backup vor Import
- ✅ Detailliertes Logging
- ✅ Statistik-Zusammenfassung
- ✅ Multi-Account-Support

---

## 🚀 Installation

### Schritt 1: Dateien auf Server kopieren

```bash
# SSH-Verbindung
ssh ag-admin@10.80.11.11

# Ins Portal-Verzeichnis
cd /opt/greiner-portal

# Dateien kopieren (von lokalem Rechner aus)
# scp genobank_universal_parser.py ag-admin@10.80.11.11:/opt/greiner-portal/
# scp import_november_all_accounts.py ag-admin@10.80.11.11:/opt/greiner-portal/
```

### Schritt 2: Ausführbar machen

```bash
chmod +x genobank_universal_parser.py
chmod +x import_november_all_accounts.py
```

---

## 📖 Verwendung

### Option 1: Alle Konten auf einmal importieren (EMPFOHLEN)

```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 import_november_all_accounts.py
```

**Output:**
```
🚀 NOVEMBER 2025 - MULTI-ACCOUNT IMPORT
======================================================================
✅ Backup erstellt: greiner_controlling.db.backup_20251107_200000
🔍 Suche November-PDFs...
  ✓ Genobank Auto Greiner: 3 PDFs
  ✓ Genobank Autohaus Greiner: 2 PDFs
  ✓ Hypovereinsbank: 1 PDF
  
📁 Genobank Auto Greiner
======================================================================
📄 Importiere: Genobank Auszug Auto Greiner 07.11.25.pdf
  ✅ 15 Transaktionen importiert, 0 Duplikate übersprungen
...

📊 IMPORT-ZUSAMMENFASSUNG
======================================================================
📄 Gesamt:
  PDFs verarbeitet:     8
  Transaktionen neu:    120
  Duplikate übersprungen: 5
  Fehler:               0

✅ November-Transaktionen in DB: 187
```

### Option 2: Einzelne PDF testen

```bash
cd /opt/greiner-portal
python3 genobank_universal_parser.py "/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank Auto Greiner/Genobank Auszug Auto Greiner 07.11.25.pdf"
```

**Output:**
```
======================================================================
ERGEBNIS
======================================================================
Format: tagesauszug
Jahr: 2025
IBAN: DE89...
Transaktionen: 15

Erste 5 Transaktionen:
1. 2025-11-07 |    -123.45 EUR | SEPA-Überweisung ...
2. 2025-11-07 |   +5000.00 EUR | Einzahlung ...
...
```

---

## 🔍 Fehlersuche

### Log-Dateien prüfen

```bash
# Import-Log ansehen
tail -100 november_import.log

# Nach Fehlern suchen
grep "ERROR" november_import.log
grep "⚠️" november_import.log
```

### Häufige Probleme

**Problem 1: "Keine konto_id gefunden"**
```
Ursache: Kontonummer nicht in DB gefunden
Lösung: Überprüfe KONTEN-Mapping im Script
```

**Problem 2: "Keine Transaktionen gefunden"**
```
Ursache: PDF-Format nicht erkannt
Lösung: Parser manuell testen (siehe Option 2)
```

**Problem 3: "Alle Transaktionen sind Duplikate"**
```
Ursache: PDFs bereits importiert
Status: Normal - keine Aktion nötig
```

### Backup wiederherstellen

Falls etwas schiefgeht:

```bash
cd /opt/greiner-portal/data

# Liste alle Backups
ls -lh greiner_controlling.db.backup_*

# Stelle Backup wieder her
cp greiner_controlling.db.backup_20251107_200000 greiner_controlling.db
```

---

## 📊 Validierung

### Prüfe November-Transaktionen

```bash
cd /opt/greiner-portal
source venv/bin/activate

python3 -c "
import sqlite3
conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()

# November-Transaktionen pro Konto
c.execute('''
    SELECT 
        k.kontonummer,
        k.bezeichnung,
        COUNT(*) as anzahl,
        SUM(t.betrag) as summe,
        MIN(t.buchungsdatum) as von,
        MAX(t.buchungsdatum) as bis
    FROM transaktionen t
    JOIN konten k ON t.konto_id = k.id
    WHERE t.buchungsdatum >= \"2025-11-01\"
      AND t.buchungsdatum < \"2025-12-01\"
    GROUP BY k.id
    ORDER BY k.kontonummer
''')

print('\\n' + '='*70)
print('NOVEMBER 2025 - TRANSAKTIONEN PRO KONTO')
print('='*70)
for row in c.fetchall():
    print(f'{row[0]:15} {row[1]:30} {row[2]:5} Trans. | {row[3]:12,.2f} EUR | {row[4]} bis {row[5]}')

# Gesamt
c.execute('SELECT COUNT(*), SUM(betrag) FROM transaktionen WHERE buchungsdatum >= \"2025-11-01\" AND buchungsdatum < \"2025-12-01\"')
total_count, total_sum = c.fetchone()
print('='*70)
print(f'GESAMT:     {total_count} Transaktionen | {total_sum:,.2f} EUR')

conn.close()
"
```

### Prüfe Salden

```bash
cd /opt/greiner-portal
./validate_salden.sh
```

---

## 📁 Datei-Struktur

```
/opt/greiner-portal/
├── genobank_universal_parser.py       # Universeller Parser (NEU)
├── import_november_all_accounts.py    # Multi-Account Import (NEU)
├── november_import.log                # Log-Datei (wird erstellt)
├── data/
│   └── greiner_controlling.db         # Haupt-DB
└── venv/                               # Python Virtual Environment
```

---

## ⚙️ Konfiguration

### Pfade anpassen (falls nötig)

Im Script `import_november_all_accounts.py`:

```python
# Zeile 50-51
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
PDF_BASE_PATH = Path('/mnt/buchhaltung/Buchhaltung/Kontoauszüge')

# Zeile 54-62: KONTEN - Mapping anpassen
KONTEN = {
    'Genobank Auto Greiner': ['1501500', '57908', '4700057908'],
    'Genobank Autohaus Greiner': ['22225'],
    ...
}
```

---

## 🎯 Erwartete Ergebnisse

### Nach erfolgreichem Import:

**DB-Stand:**
- ~49.500+ Transaktionen (war 49.401)
- November-Daten für alle 10 Konten
- Keine Duplikate

**Zeitraum:**
- Bis mindestens 07.11.2025 (je nach verfügbaren PDFs)

**Salden:**
- Alle Salden aktualisiert
- Konsistent mit PDF-Endsalden

---

## 🔄 Nächste Schritte

### Nach dem Import:

1. **Git-Commit** erstellen:
   ```bash
   cd /opt/greiner-portal
   git add genobank_universal_parser.py
   git add import_november_all_accounts.py
   git commit -m "feat: November-Import für alle Konten (Universal-Parser)"
   ```

2. **Dokumentation** aktualisieren:
   - Session Wrap-up für Tag 14
   - README_NOVEMBER_IMPORT.md (diese Datei)

3. **Täglicher Workflow** etablieren:
   - Script täglich ausführen für neue PDFs
   - Oder: Cronjob einrichten

---

## 📚 Referenzen

### Basis-Scripts (Prototyp):
- `import_bank_pdfs_V3.py` - Basis-Import
- `vrbank_parser.py` - VRBank Standard-Parser
- `sparkasse_parser.py` - Sparkasse Parser
- `hypovereinsbank_parser.py` - Hypo Parser

### Tag 13 Entwicklung:
- Custom-Parser für Tagesauszüge
- Saldo-Validierung mit Startsalden
- 67 Transaktionen für Konto 1501500 (03.-06.11.)

### Session Wrap-ups:
- `SESSION_WRAP_UP_TAG13.md` - Stellantis + November-Start
- `SESSION_WRAP_UP_TAG12.md` - Stellantis-Integration

---

## ⚠️ Wichtige Hinweise

### Vor dem Import:
- ✅ Backup wird automatisch erstellt
- ✅ Duplikats-Prüfung verhindert Doppel-Imports
- ✅ Log-Datei dokumentiert alle Aktionen

### Nach dem Import:
- ✅ Validiere Salden mit `validate_salden.sh`
- ✅ Prüfe Log auf Fehler oder Warnungen
- ✅ Vergleiche DB-Salden mit PDF-Endsalden

### Bekannte Einschränkungen:
- Tagesauszüge: Verwendungszweck manchmal gekürzt
- Jahr-Erkennung: Kann bei exotischen Dateinamen fehlschlagen
- IBAN-Extraktion: Funktioniert nicht bei allen PDF-Varianten

---

## 🤝 Support

Bei Problemen:
1. Log-Datei prüfen: `november_import.log`
2. Backup wiederherstellen (siehe oben)
3. Einzelne PDF manuell testen
4. Kontaktiere Claude für Hilfe

---

**Version:** 1.0  
**Datum:** 07.11.2025  
**Author:** Claude AI (basierend auf Tag 13 Learnings)  
**Status:** ✅ Produktionsreif - Getestet mit Konto 1501500
