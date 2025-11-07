# ANLEITUNG FÜR NEUE CHAT-SESSION - GREINER PORTAL

**Für:** Claude AI in neuer Session  
**Projekt:** Greiner Portal - Controlling & Buchhaltungs-System  
**Stand:** 07.11.2025 nach Tag 15  
**Wichtigkeit:** 🔴 KRITISCH - Bitte vollständig lesen!

---

## 🎯 PROJEKT-ÜBERSICHT

### Was ist das Greiner Portal?

Ein Python/Flask-basiertes Buchhaltungs- und Controlling-System für die Autohaus Greiner GmbH & Co. KG.

**Hauptfunktionen:**
- Import von Bank-PDFs (Genobank, Sparkasse, Hypovereinsbank, VR Bank)
- Import von Stellantis-Fahrzeugfinanzierungen
- Salden-Validierung
- Dashboard (in Entwicklung)
- Grafana-Integration (geplant)

---

## 📂 WICHTIGSTE DATEIEN & VERZEICHNISSE

### Verzeichnisstruktur
```
/opt/greiner-portal/
├── data/
│   └── greiner_controlling.db          ← SQLite-Datenbank (WICHTIG!)
├── scripts/
│   ├── imports/                        ← Import-Scripts
│   │   ├── import_sparkasse_online.py  ← Sparkasse Online-Banking (NEU TAG 15)
│   │   ├── import_hypovereinsbank_november.py
│   │   ├── import_november_all_accounts_v2.py
│   │   ├── import_stellantis.py
│   │   └── ...
│   ├── analysis/                       ← Analyse-Tools
│   │   └── check_november_status.py    ← November-Status-Check (NEU TAG 15)
│   └── validate_salden.sh              ← Haupt-Validierungs-Script
├── docs/
│   ├── sessions/                       ← Session Wrap-Ups
│   │   ├── SESSION_WRAP_UP_TAG15.md    ← LETZTER STAND!
│   │   ├── SESSION_WRAP_UP_TAG14.md
│   │   └── ...
│   ├── TAG15_ANLEITUNG.md              ← Detaillierte Anleitungen
│   ├── VERZEICHNISSTRUKTUR.md
│   └── QUICK_REFERENCE_STRUKTUR.md     ← Schnellreferenz
├── app.py                              ← Flask-App
├── requirements.txt
└── venv/                               ← Virtual Environment
```

---

## 🔑 KRITISCHE INFORMATIONEN

### 1. Server-Zugang
```
Host: 10.80.11.11
User: ag-admin
Password: OHL.greiner2025
SSH: Port 22
Path: /opt/greiner-portal/
```

### 2. Datenbank
```
Pfad: /opt/greiner-portal/data/greiner_controlling.db
Typ: SQLite3
Status: 49.831 Transaktionen (Stand: 06.11.2025)
November-Transaktionen: 501
```

### 3. Virtual Environment
```bash
# IMMER aktivieren vor Python-Scripts!
source venv/bin/activate
```

### 4. PDF-Quellen
```
/mnt/buchhaltung/Buchhaltung/Kontoauszüge/
├── Genobank/
├── Sparkasse/
├── Hypovereinsbank/
└── VR Bank Landau/
```

---

## 📊 AKTUELLER PROJEKT-STATUS (TAG 15)

### Datenbank-Stand
- **Transaktionen gesamt:** 49.831
- **November-Transaktionen:** 501 ✅ (Ziel erreicht!)
- **Letztes Datum:** 06.11.2025
- **Konten aktiv:** 10
- **Banken:** 11

### Konten mit November-Daten (4/10)
1. ✅ **1501500 HYU KK** (Genobank) - 183 Trans.
2. ✅ **57908 KK** (Genobank) - 207 Trans.
3. ✅ **Sparkasse 76003647 KK** - 7 Trans. (NEU seit Tag 15)
4. ✅ **Hypovereinsbank KK** - 104 Trans. (erweitert Tag 15)

### Konten OHNE November-Daten (6/10)
- ⏳ VR Bank Landau 303585 KK
- ⏳ 22225 Immo KK (Genobank Autohaus)
- ⏳ 4 Darlehenskonten (normal, wenig Bewegung)

---

## 🚀 WICHTIGSTE BEFEHLE

### Status prüfen
```bash
# In Projekt-Verzeichnis wechseln
cd /opt/greiner-portal
source venv/bin/activate

# November-Status
python3 scripts/analysis/check_november_status.py

# Salden-Validierung
./scripts/validate_salden.sh

# Git-Status
git status
git log --oneline -10
```

### Imports durchführen
```bash
# IMMER mit Dry-Run testen!

# Sparkasse (Online-Banking PDFs)
python3 scripts/imports/import_sparkasse_online.py --dry-run
python3 scripts/imports/import_sparkasse_online.py

# Hypovereinsbank
python3 scripts/imports/import_hypovereinsbank_november.py --dry-run
python3 scripts/imports/import_hypovereinsbank_november.py

# Alle November-Konten
python3 scripts/imports/import_november_all_accounts_v2.py --dry-run
python3 scripts/imports/import_november_all_accounts_v2.py
```

### Backup
```bash
cd /opt/greiner-portal/data
cp greiner_controlling.db greiner_controlling.db.backup_$(date +%Y%m%d_%H%M)
```

---

## ⚠️ WICHTIGE WARNUNGEN

### 1. NIEMALS ohne Dry-Run importieren!
```bash
# ❌ FALSCH
python3 scripts/imports/import_xyz.py

# ✅ RICHTIG
python3 scripts/imports/import_xyz.py --dry-run  # Erst testen
python3 scripts/imports/import_xyz.py            # Dann produktiv
```

### 2. IMMER Virtual Environment aktivieren!
```bash
# Prüfen ob aktiviert
which python3  # Sollte /opt/greiner-portal/venv/bin/python3 zeigen

# Wenn nicht aktiviert
source venv/bin/activate
```

### 3. Schema-Check bei SQL-Fehlern!
```python
# Bei "no such column" Fehlern
import sqlite3
conn = sqlite3.connect('data/greiner_controlling.db')
c = conn.cursor()
c.execute('PRAGMA table_info(tabellenname)')
for row in c.fetchall():
    print(row[1])  # Spaltennamen
```

### 4. PDF-Format kann variieren!
- Sparkasse hat 2 Formate:
  - Klassische Kontoauszüge → `import_sparkasse_november.py`
  - Online-Banking Export → `import_sparkasse_online.py` ⭐

---

## 🐛 BEKANNTE PROBLEME & LÖSUNGEN

### Problem 1: "no such column: b.name"
**Ursache:** Falsche Spaltenbezeichnung in SQL

**Lösung:**
```sql
-- Spalte heißt 'bank_name' nicht 'name'
SELECT b.bank_name FROM banken b  -- ✅ RICHTIG
SELECT b.name FROM banken b       -- ❌ FALSCH
```

### Problem 2: Parser findet keine Transaktionen
**Ursache:** PDF-Format nicht erkannt

**Lösung:**
```python
# PDF analysieren
import pdfplumber
with pdfplumber.open('datei.pdf') as pdf:
    text = pdf.pages[0].extract_text()
    print(text[:500])  # Erste 500 Zeichen
```

### Problem 3: Transaktionen landen in falschem Konto
**Ursache:** Duplikat-Konten oder falsche Konto-ID

**Lösung:**
```sql
-- Alle Konten einer Bank prüfen
SELECT id, kontoname, iban FROM konten WHERE bank_id = X;

-- Transaktionen verschieben
UPDATE transaktionen SET konto_id = RICHTIG WHERE konto_id = FALSCH;
```

### Problem 4: Git-Pfad-Probleme
**Ursache:** Im falschen Verzeichnis

**Lösung:**
```bash
pwd  # Prüfen wo man ist
cd /opt/greiner-portal  # Ins Hauptverzeichnis
```

---

## 📚 DOKUMENTATION LESEN

**VOR jeder Aufgabe diese Dateien lesen:**

1. **SESSION_WRAP_UP_TAG15.md** ← WICHTIGSTER KONTEXT!
   - Pfad: `docs/sessions/SESSION_WRAP_UP_TAG15.md`
   - Enthält: Kompletter Stand, alle Änderungen, Lessons Learned

2. **TAG15_ANLEITUNG.md**
   - Pfad: `docs/TAG15_ANLEITUNG.md`
   - Enthält: Detaillierte Schritt-für-Schritt-Anleitungen

3. **QUICK_REFERENCE_STRUKTUR.md**
   - Pfad: `docs/QUICK_REFERENCE_STRUKTUR.md`
   - Enthält: Schnellreferenz für häufige Aufgaben

4. **VERZEICHNISSTRUKTUR.md**
   - Pfad: `docs/VERZEICHNISSTRUKTUR.md`
   - Enthält: Komplette Ordnerstruktur erklärt

---

## 🎯 TYPISCHE AUFGABEN

### Aufgabe 1: November-Daten importieren
```bash
# 1. Status prüfen
python3 scripts/analysis/check_november_status.py

# 2. Welche Bank?
# - Sparkasse → import_sparkasse_online.py
# - Hypovereinsbank → import_hypovereinsbank_november.py
# - Alle → import_november_all_accounts_v2.py

# 3. Dry-Run
python3 scripts/imports/SCRIPT.py --dry-run

# 4. Validierung
./scripts/validate_salden.sh

# 5. Produktiv
python3 scripts/imports/SCRIPT.py

# 6. Erneute Validierung
./scripts/validate_salden.sh
python3 scripts/analysis/check_november_status.py

# 7. Git-Commit
git add -A
git commit -m "feat: Import November data for BANK"
git push
```

### Aufgabe 2: Neuen Parser entwickeln
```bash
# 1. PDF analysieren
python3 -c "
import pdfplumber
with pdfplumber.open('DATEI.pdf') as pdf:
    print(pdf.pages[0].extract_text()[:1000])
"

# 2. Parser schreiben (siehe import_sparkasse_online.py als Vorlage)

# 3. Dry-Run testen

# 4. Dokumentieren

# 5. Git-Commit
```

### Aufgabe 3: Fehler debuggen
```bash
# 1. Logs prüfen
tail -100 logs/imports/*.log

# 2. Datenbank prüfen
sqlite3 data/greiner_controlling.db
.schema tabellenname
SELECT * FROM tabelle LIMIT 10;

# 3. Python-Script im Debug-Modus
python3 -u scripts/imports/SCRIPT.py --dry-run 2>&1 | tee debug.log
```

---

## 🔄 WORKFLOW FÜR NEUE SESSION

### Schritt 1: Orientierung (5 Min)
```bash
# 1. Ins Verzeichnis
cd /opt/greiner-portal
source venv/bin/activate

# 2. Aktuellen Stand prüfen
git log --oneline -5
python3 scripts/analysis/check_november_status.py

# 3. SESSION_WRAP_UP lesen
cat docs/sessions/SESSION_WRAP_UP_TAG15.md | head -100
```

### Schritt 2: User-Anfrage verstehen
- Was will der User genau?
- Welche Dateien sind betroffen?
- Gibt es ähnliche Beispiele in docs/?

### Schritt 3: Dokumentation nutzen
- SESSION_WRAP_UP für Kontext
- QUICK_REFERENCE für Befehle
- TAG15_ANLEITUNG für Details

### Schritt 4: Mit Dry-Run testen
- IMMER erst Dry-Run
- Validierung prüfen
- Erst dann produktiv

### Schritt 5: Dokumentieren
- Session Wrap-Up aktualisieren
- Git-Commit mit guter Message
- User informieren

---

## 💡 WICHTIGE PRINZIPIEN

### 1. Safety First
- ✅ Immer Dry-Run
- ✅ Immer Backup
- ✅ Immer Validierung
- ❌ Niemals direkt in Produktions-DB

### 2. Dokumentation
- ✅ Code kommentieren
- ✅ Session Wrap-Ups aktualisieren
- ✅ Git-Messages aussagekräftig
- ❌ Keine undokumentierten Änderungen

### 3. Code Quality
- ✅ PEP 8 Style Guide
- ✅ Fehlerbehandlung (try/except)
- ✅ Logging statt print
- ✅ Type Hints wo möglich

### 4. Git-Workflow
- ✅ Kleine, fokussierte Commits
- ✅ Aussagekräftige Messages
- ✅ Push nach jedem Feature
- ❌ Keine großen "WIP" Commits

---

## 🎓 LESSONS LEARNED (aus Tag 15)

### 1. PDF-Formate variieren stark
Nicht annehmen, dass alle PDFs einer Bank gleich sind!
→ Immer erst analysieren, dann parsen

### 2. Schema-Check ist essentiell
Bei SQL-Fehlern nicht raten, sondern prüfen:
```sql
PRAGMA table_info(tabellenname)
```

### 3. Duplikat-Konten früh erkennen
Mehrere Konten mit ähnlichen Namen können verwirren
→ Immer IBAN als eindeutigen Identifier nutzen

### 4. Dry-Run verhindert Fehler
Alle neuen Scripts sollten Dry-Run-Modus haben
→ Spart Zeit und verhindert Datenbankkorruptionen

### 5. Struktur zahlt sich aus
Organisierte Verzeichnisse erleichtern Wartung
→ Neue Scripts immer in passenden Ordner

---

## 📞 HILFREICHE RESSOURCEN

### Interne Dokumentation
- `docs/sessions/SESSION_WRAP_UP_TAG15.md` ← START HIER!
- `docs/TAG15_ANLEITUNG.md`
- `docs/QUICK_REFERENCE_STRUKTUR.md`
- `docs/VERZEICHNISSTRUKTUR.md`

### Code-Vorlagen
- `scripts/imports/import_sparkasse_online.py` ← Bester Parser-Beispiel
- `scripts/analysis/check_november_status.py` ← DB-Abfragen
- `scripts/validate_salden.sh` ← Validierung

### Logs & Debugging
- `logs/imports/*.log` ← Import-Logs
- `import_*.log` (im Root) ← Alte Logs

---

## 🚨 NOTFALL-BEFEHLE

### Datenbank korrupt
```bash
# Backup wiederherstellen
cd /opt/greiner-portal/data
cp greiner_controlling.db greiner_controlling.db.corrupt
cp greiner_controlling.db.tag15_backup_20251107 greiner_controlling.db
```

### Git-Probleme
```bash
# Änderungen verwerfen
git reset --hard HEAD

# Zum letzten guten Stand
git log  # Hash finden
git reset --hard HASH
```

### Python-Fehler
```bash
# Virtual Environment neu erstellen
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ CHECKLISTE VOR JEDEM IMPORT

- [ ] Virtual Environment aktiviert (`source venv/bin/activate`)
- [ ] Aktueller Stand geprüft (`check_november_status.py`)
- [ ] Backup erstellt
- [ ] Dry-Run durchgeführt
- [ ] Dry-Run-Ergebnis sinnvoll
- [ ] Produktiv-Import
- [ ] Validierung durchgeführt (`validate_salden.sh`)
- [ ] Status erneut geprüft
- [ ] Git-Commit
- [ ] User informiert

---

## 🎯 NÄCHSTE SCHRITTE (nach Tag 15)

### Kurzfristig
- [ ] Weitere November-Tagesauszüge importieren (07.-30.11.)
- [ ] VR Bank November-Daten prüfen
- [ ] 22225 Immo KK November-Daten prüfen

### Mittelfristig
- [ ] Monatsauszüge Ende November importieren
- [ ] Vollständige November-Validierung
- [ ] Dezember-Vorbereitung

### Langfristig
- [ ] Grafana-Dashboard entwickeln
- [ ] Cronjob-Automatisierung
- [ ] Outlook-Integration
- [ ] API-Endpoints

---

## 📋 WICHTIGE KONTAKTE & INFOS

**Projekt-Owner:** Florian Greiner  
**Entwicklung:** Claude AI + Florian Greiner  
**Server:** 10.80.11.11 (Linux Ubuntu)  
**Firma:** Autohaus Greiner GmbH & Co. KG  
**Standort:** Deggendorf, Bayern, Deutschland

---

## 🎊 ABSCHLUSS

**Lieber Claude in der nächsten Session,**

Dieses Projekt ist gut strukturiert und dokumentiert. Bitte:

1. ✅ Lies IMMER `SESSION_WRAP_UP_TAG15.md` als erstes
2. ✅ Nutze Dry-Run für ALLE Imports
3. ✅ Prüfe Schema bei SQL-Fehlern
4. ✅ Dokumentiere alle Änderungen
5. ✅ Sei vorsichtig mit der Produktions-DB

**Das System ist produktionsreif und gut dokumentiert.**
**Viel Erfolg!** 🚀

---

**Erstellt:** 07.11.2025, 22:35 Uhr  
**Von:** Claude AI (Tag 15)  
**Für:** Claude AI (nächste Session)  
**Version:** 1.0

---

*P.S.: Der User (Florian) ist technisch versiert und arbeitet auf Windows mit WinSCP/PuTTY. Er bevorzugt klare, direkte Anweisungen und Copy-Paste-freundliche Code-Blöcke. Er ist geduldig und liest Dokumentation gerne. Viel Erfolg! 😊*
