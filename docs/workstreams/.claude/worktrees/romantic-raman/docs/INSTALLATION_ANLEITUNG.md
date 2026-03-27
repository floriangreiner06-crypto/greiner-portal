# 🚀 INSTALLATION ANLEITUNG - Bankenspiegel 3.0

**Server:** 10.80.80.20  
**Zielverzeichnis:** /opt/greiner-portal/  
**Stand:** 2025-11-06

---

## ✅ VORAUSSETZUNGEN (Bereits erfüllt!)

- ✅ Virtual Environment in `/opt/greiner-portal/venv/`
- ✅ Flask 3.0.0 installiert
- ✅ **pdfplumber 0.11.0 bereits installiert!**
- ✅ pypdfium2 5.0.0 installiert

---

## 📋 INSTALLATIONS-SCHRITTE

### Option A: Automatische Installation (EMPFOHLEN)

```bash
# 1. In PuTTY verbinden
ssh ag-admin@10.80.80.20

# 2. Zum Zielverzeichnis wechseln
cd /opt/greiner-portal

# 3. Virtual Environment aktivieren
source venv/bin/activate

# 4. Alle Dateien aus dem bankenspiegel_deployment Ordner hochladen
#    (via WinSCP, FileZilla oder scp)

# 5. Installations-Skript ausführen
chmod +x install.sh
./install.sh
```

Das war's! ✨

---

### Option B: Manuelle Installation

Falls du es Schritt für Schritt machen möchtest:

```bash
# 1. Verbinden und venv aktivieren
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal
source venv/bin/activate

# 2. Parser-Verzeichnis erstellen
mkdir -p parsers

# 3. Dateien kopieren
# Kopiere alle .py Dateien aus parsers/ nach /opt/greiner-portal/parsers/
# Kopiere transaction_manager.py, pdf_importer.py, import_bank_pdfs.py nach /opt/greiner-portal/

# 4. Berechtigungen setzen
chmod +x import_bank_pdfs.py
chmod -R 755 parsers/

# 5. Dependencies sind bereits installiert! (pdfplumber 0.11.0 ✅)

# 6. Testen
python import_bank_pdfs.py info
python import_bank_pdfs.py list-banks
```

---

## 🧪 ERSTE TESTS

Nach der Installation:

```bash
# Test 1: System-Info
python import_bank_pdfs.py info

# Erwartete Ausgabe:
# ╔════════════════════════════════════════════════════════════════╗
# ║         Bankenspiegel 3.0 - PDF Import System Info            ║
# ╚════════════════════════════════════════════════════════════════╝
# ...

# Test 2: Unterstützte Banken
python import_bank_pdfs.py list-banks

# Erwartete Ausgabe:
# Unterstützte Banken:
# - Sparkasse (Keywords: sparkasse)
# - VR-Bank/Genobank/Volksbank (Keywords: genobank, vrbank, volksbank)
# - HypoVereinsbank (Keywords: hypovereinsbank, hypo)

# Test 3: Test-Import (ohne DB)
python import_bank_pdfs.py test /pfad/zu/test.pdf --verbose

# Dies parst die PDF OHNE sie in die DB zu importieren
# Perfekt zum Testen!
```

---

## 📁 DATEI-UPLOAD-OPTIONEN

### Via WinSCP (Grafisch)

1. WinSCP öffnen
2. Verbinden zu: `10.80.80.20` (User: `ag-admin`)
3. Navigiere zu `/opt/greiner-portal/`
4. Drag & Drop alle Dateien aus `bankenspiegel_deployment/`

### Via SCP (Kommandozeile)

Von deinem lokalen Windows-PC (Git Bash oder PowerShell):

```bash
# Gesamtes Verzeichnis hochladen
scp -r bankenspiegel_deployment/* ag-admin@10.80.80.20:/opt/greiner-portal/

# Oder einzelne Dateien
scp install.sh ag-admin@10.80.80.20:/opt/greiner-portal/
scp -r parsers/ ag-admin@10.80.80.20:/opt/greiner-portal/parsers/
```

### Via FileZilla

1. FileZilla öffnen
2. Host: `10.80.80.20`
3. Benutzername: `ag-admin`
4. Passwort: [dein Passwort]
5. Port: 22 (SFTP)
6. Dateien hochladen

---

## 🎯 ERSTER PRODUKTIV-IMPORT

Nach erfolgreicher Installation und Tests:

```bash
# 1. PDFs vorbereiten
# Lege alle PDF-Dateien in ein Verzeichnis, z.B.:
# /opt/greiner-portal/data/bank_pdfs/

# 2. Import starten
cd /opt/greiner-portal
source venv/bin/activate

python import_bank_pdfs.py import /opt/greiner-portal/data/bank_pdfs/ \
    --min-year 2025 \
    --verbose

# 3. Ergebnis prüfen
# Logs in: /opt/greiner-portal/logs/bankenspiegel.log
# Datenbank: /opt/greiner-portal/data/greiner_controlling.db
```

---

## 📊 VERZEICHNIS-STRUKTUR (Nach Installation)

```
/opt/greiner-portal/
├── parsers/                          # ✅ NEU
│   ├── __init__.py
│   ├── base_parser.py
│   ├── sparkasse_parser.py
│   ├── vrbank_parser.py
│   ├── hypovereinsbank_parser.py
│   └── parser_factory.py
├── transaction_manager.py            # ✅ NEU
├── pdf_importer.py                   # ✅ NEU
├── import_bank_pdfs.py               # ✅ NEU
├── install.sh                        # ✅ NEU (optional)
├── README.md                         # ✅ NEU
├── venv/                             # ✅ Bereits vorhanden
├── data/
│   └── greiner_controlling.db        # ✅ Bereits vorhanden
└── logs/                             # ✅ Bereits vorhanden
```

---

## ❗ TROUBLESHOOTING

### Problem: "Permission Denied"

```bash
# Lösung: Berechtigungen setzen
chmod +x /opt/greiner-portal/import_bank_pdfs.py
chmod +x /opt/greiner-portal/install.sh
chmod -R 755 /opt/greiner-portal/parsers/
```

### Problem: "ModuleNotFoundError: No module named 'parsers'"

```bash
# Prüfe ob parsers/ Verzeichnis existiert
ls -la /opt/greiner-portal/parsers/

# Prüfe ob __init__.py vorhanden ist
ls /opt/greiner-portal/parsers/__init__.py

# Aktiviere venv
cd /opt/greiner-portal
source venv/bin/activate
```

### Problem: "pdfplumber not found"

```bash
# Das sollte NICHT passieren, da pdfplumber bereits installiert ist
# Falls doch:
source /opt/greiner-portal/venv/bin/activate
pip install pdfplumber==0.11.0
```

### Problem: "Keine Transaktionen gefunden"

```bash
# 1. Im Test-Modus prüfen
python import_bank_pdfs.py test deine_datei.pdf --verbose

# 2. Schaue ob Bank erkannt wird
# Ausgabe sollte zeigen: "Erkannte Bank: Sparkasse" (oder andere)

# 3. Falls Bank nicht erkannt wird:
#    - Prüfe Dateiname (sollte "sparkasse", "vrbank" etc. enthalten)
#    - Öffne PDF manuell und prüfe Inhalt
```

---

## 📖 NÄCHSTE SCHRITTE

Nach erfolgreicher Installation:

1. ✅ **Teste mit einer PDF-Datei**
   ```bash
   python import_bank_pdfs.py test /pfad/zur/test.pdf --verbose
   ```

2. ✅ **Führe ersten Import durch**
   ```bash
   python import_bank_pdfs.py import /pfad/zu/pdfs --min-year 2025
   ```

3. ✅ **Prüfe Datenbank**
   ```bash
   sqlite3 /opt/greiner-portal/data/greiner_controlling.db
   SELECT COUNT(*) FROM bank_transactions;
   .quit
   ```

4. ✅ **Optional: Cron-Job einrichten** (für automatischen Import)

5. ✅ **Optional: Flask-Route erstellen** (für Web-Upload)

---

## 📞 SUPPORT

Bei Fragen:
1. Logs prüfen: `/opt/greiner-portal/logs/`
2. README.md lesen
3. Test-Modus nutzen: `python import_bank_pdfs.py test datei.pdf --verbose`

---

## ✅ CHECKLISTE

Installation erfolgreich wenn:

- [ ] `python import_bank_pdfs.py info` funktioniert
- [ ] `python import_bank_pdfs.py list-banks` zeigt 3 Banken
- [ ] Test-Import funktioniert ohne Fehler
- [ ] Logs werden erstellt in `/opt/greiner-portal/logs/`
- [ ] Produktiv-Import läuft durch
- [ ] Transaktionen sind in der DB sichtbar

---

**Viel Erfolg! 🚀**

Bei Problemen einfach melden!
