# Bankenspiegel 3.0 - PDF Import System

**Status:** ✅ PRODUCTION READY  
**Version:** 3.0  
**Datum:** 2025-11-06

---

## 📋 ÜBERSICHT

Automatisches Import-System für Bank-Kontoauszüge (PDF → SQLite Datenbank)

### Unterstützte Banken
- ✅ **Sparkasse**
- ✅ **VR-Bank / Genobank / Volksbank**
- ✅ **HypoVereinsbank**

### Features
- 🔄 Automatische Bank-Erkennung
- 🛡️ Duplikats-Check
- 📝 Mehrzeiliger Verwendungszweck
- 🏦 IBAN-Extraktion
- 📊 CLI + Programmatische API
- 🎯 Type Hints & moderne Python 3.10+ Features

---

## 🚀 SCHNELLSTART (Auf Server 10.80.80.20)

### 1. Dateien kopieren

Alle Dateien aus diesem Verzeichnis nach `/opt/greiner-portal/` kopieren:

```bash
# Via SCP von lokalem Rechner:
scp -r bankenspiegel_deployment/* ag-admin@10.80.80.20:/opt/greiner-portal/

# Oder direkt auf dem Server:
cd /opt/greiner-portal/
# Dateien hier einfügen
```

### 2. Dependencies installieren

```bash
cd /opt/greiner-portal
source venv/bin/activate
pip install pdfplumber==0.11.0
```

**Hinweis:** Flask und pdfplumber sind bereits installiert!

### 3. Testen

```bash
# System-Info anzeigen
python import_bank_pdfs.py info

# Unterstützte Banken auflisten
python import_bank_pdfs.py list-banks

# Test mit einer PDF (ohne DB-Import)
python import_bank_pdfs.py test /pfad/zu/test.pdf
```

### 4. Produktiv-Import

```bash
# Alle PDFs aus Verzeichnis importieren
python import_bank_pdfs.py import /pfad/zu/pdfs

# Nur Dateien ab 2025
python import_bank_pdfs.py import /pfad/zu/pdfs --min-year 2025

# Nur eine bestimmte Bank
python import_bank_pdfs.py import /pfad/zu/pdfs --bank sparkasse

# Kombiniert
python import_bank_pdfs.py import /pfad/zu/pdfs --bank sparkasse --min-year 2025 --verbose
```

---

## 📁 VERZEICHNIS-STRUKTUR

```
/opt/greiner-portal/
├── parsers/                          # ✅ Parser Package
│   ├── __init__.py                   # Package Definition
│   ├── base_parser.py                # Abstract Base Class + Helpers
│   ├── sparkasse_parser.py           # Sparkasse Parser
│   ├── vrbank_parser.py              # VR-Bank Parser
│   ├── hypovereinsbank_parser.py     # HypoVereinsbank Parser
│   └── parser_factory.py             # Automatische Bank-Erkennung
├── transaction_manager.py            # ✅ DB Operations + Duplikats-Check
├── pdf_importer.py                   # ✅ Main Orchestrator (Batch-Import)
├── import_bank_pdfs.py               # ✅ CLI Tool (argparse)
├── requirements.txt                  # ✅ Dependencies
├── README.md                         # ✅ Diese Datei
└── data/
    └── greiner_controlling.db        # SQLite DB (bereits vorhanden)
```

---

## 🎯 CLI-BEFEHLE

### Basis-Kommandos

```bash
# Hilfe anzeigen
python import_bank_pdfs.py --help
python import_bank_pdfs.py import --help

# System-Info
python import_bank_pdfs.py info

# Unterstützte Banken
python import_bank_pdfs.py list-banks
```

### Import-Kommandos

```bash
# Standard-Import (alle PDFs)
python import_bank_pdfs.py import /pfad/zu/pdfs

# Mit Jahr-Filter
python import_bank_pdfs.py import /pfad/zu/pdfs --min-year 2025

# Mit Bank-Filter
python import_bank_pdfs.py import /pfad/zu/pdfs --bank sparkasse

# Verbose Modus (detaillierte Logs)
python import_bank_pdfs.py import /pfad/zu/pdfs --verbose

# Kombiniert
python import_bank_pdfs.py import /pfad/zu/pdfs \
    --bank sparkasse \
    --min-year 2025 \
    --verbose
```

### Test-Kommandos

```bash
# Einzelne PDF testen (OHNE DB-Import)
python import_bank_pdfs.py test sparkasse_2025.pdf

# Mit Verbose
python import_bank_pdfs.py test sparkasse_2025.pdf --verbose
```

---

## 💻 PROGRAMMATISCHE NUTZUNG

### Beispiel 1: Basis-Import

```python
from pdf_importer import PDFImporter

# Importer erstellen
importer = PDFImporter(
    pdf_directory='/pfad/zu/pdfs',
    min_year=2025
)

# Import durchführen
results = importer.import_all()

# Ergebnisse anzeigen
print(f"Dateien verarbeitet: {results['files_processed']}")
print(f"Transaktionen importiert: {results['total_transactions']}")
```

### Beispiel 2: Mit Filter

```python
from pdf_importer import PDFImporter

# Nur Sparkasse-Dateien
importer = PDFImporter(
    pdf_directory='/pfad/zu/pdfs',
    bank_filter='sparkasse',
    min_year=2025
)

results = importer.import_all()
```

### Beispiel 3: Einzelne PDF

```python
from parsers import ParserFactory

# Automatische Bank-Erkennung
parser_class = ParserFactory.get_parser('sparkasse_2025.pdf')

if parser_class:
    parser = parser_class('sparkasse_2025.pdf')
    transactions = parser.parse()
    
    # Statistiken
    stats = parser.get_statistics()
    print(f"Transaktionen: {stats['count']}")
    print(f"Zeitraum: {stats['date_range']}")
```

---

## 🏦 BANK-FORMATE

### Sparkasse

**Format:**
```
DD.MM.YYYY Verwendungszweck... Betrag
```

**Erkennung:**
- Dateiname enthält: `sparkasse`
- PDF-Inhalt enthält: `Sparkasse`

**Beispiel:**
```
01.01.2025 SEPA-Überweisung Max Mustermann 1.234,56
Verwendungszweck Zeile 2
```

### VR-Bank / Genobank

**Format:**
```
DD.MM. DD.MM. Verwendungszweck Betrag H/S
```

**Erkennung:**
- Dateiname enthält: `genobank`, `vrbank`, `volksbank`
- PDF-Inhalt enthält: `Volksbank`, `Genobank`

**Besonderheit:**
- Jahr wird aus Dateiname extrahiert (z.B. `kontoauszug_2025.pdf`)

### HypoVereinsbank

**Format:**
```
DD.MM.YYYY DD.MM.YYYY Verwendungszweck Betrag EUR
```

**Erkennung:**
- Dateiname enthält: `hypovereinsbank`, `hypo`
- PDF-Inhalt enthält: `HypoVereinsbank`

---

## 🛡️ DUPLIKATS-CHECK

Das System verhindert automatisch Duplikate durch Prüfung von:
- `konto_id` (abgeleitet aus IBAN)
- `datum` (Buchungsdatum)
- `betrag`
- `verwendungszweck` (erste 100 Zeichen)

**Hinweis:** Bei mehrfachem Import derselben PDF werden keine Duplikate erstellt!

---

## 📊 LOGGING

### Standard-Logs

```bash
# Logs im data/ Verzeichnis
/opt/greiner-portal/logs/
├── bankenspiegel.log        # Haupt-Log
└── errors.log               # Nur Fehler
```

### Verbose-Modus

```bash
# Aktiviert mit --verbose Flag
python import_bank_pdfs.py import /pfad/zu/pdfs --verbose
```

Zeigt:
- Jede geparste Transaktion
- IBAN-Extraktion
- Parser-Auswahl
- DB-Operationen

---

## 🔧 KONFIGURATION

### Datenbank

Standardpfad: `/opt/greiner-portal/data/greiner_controlling.db`

Ändern in `transaction_manager.py`:
```python
DB_PATH = '/anderer/pfad/zur/datenbank.db'
```

### Logging-Level

Ändern in `import_bank_pdfs.py`:
```python
logging.basicConfig(
    level=logging.INFO,  # oder DEBUG für mehr Details
    ...
)
```

---

## ❗ TROUBLESHOOTING

### Problem: "Keine IBAN gefunden"

**Lösung:**
1. PDF manuell öffnen und IBAN suchen
2. Parser ggf. anpassen (Regex in `base_parser.py`)

### Problem: "Keine Transaktionen gefunden"

**Lösung:**
1. PDF im Test-Modus prüfen: `python import_bank_pdfs.py test datei.pdf --verbose`
2. Parser-Regex ggf. anpassen
3. PDF-Format ggf. geändert → Parser updaten

### Problem: "Permission Denied"

**Lösung:**
```bash
# Berechtigungen setzen
chmod +x import_bank_pdfs.py
chmod -R 755 parsers/
```

### Problem: "Module nicht gefunden"

**Lösung:**
```bash
# Virtual Environment aktivieren
source /opt/greiner-portal/venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

---

## 🔄 INTEGRATION MIT FLASK

### Beispiel: Flask-Route für Upload

```python
from flask import Blueprint, request, jsonify
from pdf_importer import PDFImporter
import os

bp = Blueprint('bankenspiegel', __name__)

@bp.route('/api/bankenspiegel/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'Keine Datei'}), 400
    
    file = request.files['file']
    
    # Temporär speichern
    temp_path = f'/tmp/{file.filename}'
    file.save(temp_path)
    
    try:
        # Importieren
        importer = PDFImporter(pdf_directory='/tmp')
        results = importer.import_all()
        
        # Aufräumen
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'transactions': results['total_transactions']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 📈 ERWEITERUNGEN

### Neue Bank hinzufügen

1. Neuen Parser erstellen (z.B. `postbank_parser.py`)
2. Von `BaseParser` erben
3. `bank_name` Property implementieren
4. `parse()` Methode implementieren
5. In `parser_factory.py` registrieren
6. In `parsers/__init__.py` exportieren

### Beispiel:

```python
from .base_parser import BaseParser, Transaction

class PostbankParser(BaseParser):
    @property
    def bank_name(self) -> str:
        return "Postbank"
    
    def parse(self) -> List[Transaction]:
        # Implementation hier
        pass
```

---

## ✅ NÄCHSTE SCHRITTE

### 1. Deployment
- [ ] Dateien auf Server kopieren
- [ ] Dependencies prüfen
- [ ] Test-Import durchführen

### 2. Produktiv-Nutzung
- [ ] PDFs in Verzeichnis ablegen
- [ ] Import durchführen
- [ ] Ergebnisse in DB prüfen

### 3. Optional
- [ ] Cron-Job für automatischen Import
- [ ] Flask-Route für Web-Upload
- [ ] Email-Benachrichtigung bei Fehlern
- [ ] Grafana-Dashboard für Import-Statistiken

---

## 📞 SUPPORT

Bei Fragen oder Problemen:
1. Logs prüfen: `/opt/greiner-portal/logs/`
2. Verbose-Modus aktivieren
3. Test-Modus nutzen für Debugging

---

## 📄 LIZENZ

Internal Tool für Auto Greiner GmbH  
© 2025 Auto Greiner

---

**Stand:** 2025-11-06  
**Version:** 3.0  
**Status:** ✅ Production Ready
# Test
