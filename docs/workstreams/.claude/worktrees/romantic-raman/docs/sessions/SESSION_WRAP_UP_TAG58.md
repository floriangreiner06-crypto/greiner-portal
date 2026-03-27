# 📋 SESSION WRAP-UP TAG 58
**Datum:** 2025-11-18  
**Dauer:** ~4 Stunden  
**Thema:** Speicherplatz-Problem, Parser-Analyse, Architektur-Planung

---

## ✅ ERREICHTE ERFOLGE

### 1. **Speicherplatz-Problem gelöst**
- **Problem:** `/` Partition 100% voll (15GB)
- **Ursache:** 7.4GB Backups in `/opt/greiner-portal/data/`
  - Stündlicher Backup-Cron (24 Backups/Tag × 7 Tage = 168 Backups)
- **Lösung:**
  - ✅ Datenbank verschoben: `/opt/greiner-portal/data` → `/data/greiner-portal/data`
  - ✅ Symlink erstellt (transparent für Anwendung)
  - ✅ Alte Backups gelöscht (nur 3 neueste behalten)
  - ✅ Cron geändert: Stündlich → Täglich (3 Uhr)
  - ✅ Auto-Cleanup: Nur 7 neueste Backups behalten
- **Resultat:** Von 100% auf 48% (7.4GB frei)

### 2. **Schema-Cleanup durchgeführt**
```sql
daily_balances → daily_balances_old_backup
bank_accounts → bank_accounts_old_backup (falls vorhanden)
```
- ✅ Konsistente Verwendung von `konto_id`
- ✅ Alte Tabellen als Backup gesichert

### 3. **Parser gefixt für 2 PDF-Formate**
- **Problem:** GenobankUniversalParser erkannte nur Tagesauszüge
- **Fix:** IBAN-Extraktion unterstützt jetzt:
  - ✅ Format 1 (Tagesauszüge): `IBAN DE27741900000000057908`
  - ✅ Format 2 (Kontoauszüge): `IBAN: DE58 7419 0000 4700 0579 08` (mit Leerzeichen)

### 4. **September-Import erfolgreich**
- ✅ 1700057908: +4 Transaktionen
- ✅ 4700057908: +7 Transaktionen
- ✅ Keine Duplikate
- ❌ 3700057908: Keine Kontoauszüge vorhanden (nur Mitteilungen)

### 5. **November-Import funktioniert weiterhin**
- ✅ Alle bestehenden Imports laufen
- ✅ Duplikat-Check funktioniert
- ✅ Täglicher Cron läuft stabil

---

## ❌ LESSONS LEARNED - WAS NICHT GETAN WERDEN SOLLTE

### 1. **KEIN PATCHING des Universal-Parsers!**
```
❌ FALSCH: GenobankUniversalParser immer komplexer patchen
           → IF-ELSE Hölle
           → Schwer wartbar
           → Fehleranfällig

✅ RICHTIG: Spezialisierte Parser pro Format
            → Einfach
            → Stabil
            → Wartbar
```

### 2. **KEINE Quick-Fixes ohne Test!**
- ❌ Parser ändern ohne ALLE Formate zu testen
- ❌ Code patchen ohne Rollback-Plan
- ❌ Regex ändern ohne zu verstehen warum

### 3. **KEINE manuellen IBAN-Zuordnungen im Code!**
```python
❌ FALSCH: if '1700057908' in filename:  # User kann falsch benennen
✅ RICHTIG: iban = extract_from_pdf_content()  # Aus PDF-Inhalt lesen
```

---

## 🎯 TODO FÜR NÄCHSTE SESSION (TAG 59)

### **PHASE 1: Parser-Architektur neu aufbauen**

#### 1.1 **Spezialisierte Parser erstellen**
```
parsers/genobank/
├── genobank_base.py                    # Gemeinsame Funktionen
├── genobank_tagesauszug_parser.py      # Für Tagesauszüge (November)
└── genobank_kontoauszug_parser.py      # Für Kontoauszüge (September)
```

**Verantwortlichkeiten:**
- `genobank_tagesauszug_parser.py`:
  - Format: `IBAN DE27741900000000057908`
  - Endsaldo: `(Endsaldo) +190.438,80 EUR`
  - Konten: 57908, 1501500, 303585
  
- `genobank_kontoauszug_parser.py`:
  - Format: `IBAN: DE58 7419 0000 4700 0579 08`
  - Endsaldo: `neuer Kontostand vom 30.09.2024  14.854,72 H`
  - Konten: 1700057908, 4700057908, 22225, 120057908, 20057908

#### 1.2 **IBAN-basierte Factory erstellen**
```python
parsers/iban_parser_factory.py

IBAN_PARSER_MAP = {
    # Tagesauszüge
    'DE27741900000000057908': GenobankTagesauszugParser,
    'DE68741900000001501500': GenobankTagesauszugParser,
    'DE76741910000000303585': VRBankParser,
    
    # Kontoauszüge
    'DE96741900001700057908': GenobankKontoauszugParser,
    'DE58741900004700057908': GenobankKontoauszugParser,
    'DE64741900000000022225': GenobankKontoauszugParser,
    
    # Andere Banken
    'DE22741200710006407420': HypoVereinsbankParser,
    'DE63741500000760036467': SparkasseParser,
}
```

**Wichtig:**
- ✅ IBAN aus PDF-Inhalt extrahieren (nicht aus Dateiname!)
- ✅ Factory wählt Parser basierend auf IBAN
- ✅ User-fehler-resistent

#### 1.3 **Import-Script aktualisieren**
```python
# ALT (deprecated):
from parsers.genobank_universal_parser import GenobankUniversalParser
parser = GenobankUniversalParser(pdf_path)

# NEU:
from parsers.iban_parser_factory import IBANParserFactory
parser = IBANParserFactory.get_parser(pdf_path)
if parser:
    transactions = parser.parse()
```

---

### **PHASE 2: Systematische Tests**

#### 2.1 **Test-Suite erstellen**
```bash
scripts/tests/test_parsers.py
```

**Test für JEDE IBAN:**
```python
test_cases = [
    {
        'iban': 'DE27741900000000057908',
        'pdf': 'Genobank Auszug Auto Greiner 17.11.25.pdf',
        'expected_tx': 17,
        'expected_endsaldo': 190438.80,
        'parser': 'GenobankTagesauszugParser'
    },
    {
        'iban': 'DE64741900000000022225',
        'pdf': '22225_2024_Nr.077_Kontoauszug_vom_2024.09.30_20241001064954.pdf',
        'expected_tx': 18,
        'expected_endsaldo': 14854.72,
        'parser': 'GenobankKontoauszugParser'
    },
    # ... alle 11 Konten
]
```

#### 2.2 **Import-Test für alle Konten**
```bash
scripts/tests/test_import_all_konten.py
```

**Für jedes Konto:**
1. ✅ PDF vorhanden?
2. ✅ IBAN erkennbar?
3. ✅ Parser funktioniert?
4. ✅ Transaktionen importierbar?
5. ✅ Endsaldo erkennbar?
6. ✅ Kein Duplikat-Import?

---

## 📋 TECHNISCHE VORAUSSETZUNGEN & GEGEBENHEITEN

### **1. Datenbank-Schema**
```
data/greiner_controlling.db (190 MB)
Standort: /data/greiner-portal/data/ (Symlink von /opt/greiner-portal/data)
```

**Relevante Tabellen:**
```sql
konten
├── id (PRIMARY KEY)
├── iban (UNIQUE, NOT NULL)
├── kontoname
├── kontonummer
└── bank_id (FOREIGN KEY → banken.id ODER NULL)

transaktionen
├── id (PRIMARY KEY)
├── konto_id (FOREIGN KEY → konten.id)
├── buchungsdatum
├── betrag
├── verwendungszweck
└── pdf_quelle

kontostand_historie
├── id (PRIMARY KEY)
├── konto_id (FOREIGN KEY → konten.id)
├── datum
├── saldo
├── quelle
└── erfasst_am
```

**WICHTIG:** Keine `banken`-Tabelle verwenden! `bank_id` kann NULL sein!

### **2. Alle Konten mit Status**

| IBAN | Kontoname | TX | Endsaldo | Status | Parser benötigt |
|------|-----------|----|----|--------|-----------------|
| DE27741900000000057908 | 57908 KK | 1038 | ✅ 190,438.80 € | ✅ | Tagesauszug |
| DE68741900000001501500 | 1501500 HYU KK | 497 | ✅ 391,114.23 € | ✅ | Tagesauszug |
| DE96741900001700057908 | 1700057908 Festgeld | 8 | ❌ | ⚠️ | Kontoauszug |
| DE58741900004700057908 | 4700057908 Darlehen | 21 | ❌ | ⚠️ | Kontoauszug |
| DE64741900000000022225 | 22225 Immo KK | 0 | ❌ | ❌ | Kontoauszug |
| DE06741900003700057908 | 3700057908 Darlehen | 0 | ❌ | ❌ | (Nur Mitteilungen) |
| DE41741900000120057908 | KfW 120057908 | 0 | ❌ | ❌ | Kontoauszug |
| DE94741900000020057908 | 20057908 Darlehen | 2 | ❌ | ⚠️ | Kontoauszug |
| DE22741200710006407420 | Hypovereinsbank KK | 409 | ✅ 96,860.86 € | ✅ | HypoVereinsbank |
| DE63741500000760036467 | Sparkasse KK | 23 | ✅ 7.46 € | ✅ | Sparkasse |
| DE76741910000000303585 | 303585 VR Landau KK | 50 | ✅ 3,091.97 € | ✅ | VRBank |

**Legende:**
- ✅ = Funktioniert vollständig
- ⚠️ = TX vorhanden, aber kein Endsaldo
- ❌ = Keine Daten

### **3. PDF-Formate**

**Format 1: Tagesauszüge (November)**
```
Dateiname: "Genobank Auszug Auto Greiner 17.11.25.pdf"
IBAN-Format: IBAN DE27741900000000057908
             Kontoinhaber Autohaus Greiner GmbH & Co. KG
Endsaldo: (Endsaldo) +190.438,80 EUR
Konten: 57908, 1501500
```

**Format 2: Kontoauszüge (September/Monatlich)**
```
Dateiname: "1700057908_2025_Nr.009_Kontoauszug_vom_2025.09.30_20251001065458.pdf"
IBAN-Format: IBAN: DE96 7419 0000 1700 0579 08 BIC: GENODEF1DGV
             (mit Leerzeichen und BIC)
Endsaldo: neuer Kontostand vom 30.09.2024  14.854,72 H
          (H = Haben/positiv, S = Soll/negativ)
Konten: 1700057908, 4700057908, 22225, 120057908, 20057908
```

**Format 3: Mitteilungen (NICHT importierbar)**
```
Dateiname: "3700057908_2025_Mitteilung_vom_2025.11.10_20251111103756.pdf"
Inhalt: Nur Benachrichtigungen, keine Transaktionen
→ SKIP!
```

### **4. Existierende Parser**
```
parsers/
├── base_parser.py                      # Basis-Klasse
├── genobank_universal_parser.py        # Universal (zu komplex!)
├── sparkasse_parser.py                 # ✅ Funktioniert
├── vrbank_parser.py                    # ✅ Funktioniert
├── hypovereinsbank_parser.py           # ✅ Funktioniert
└── parser_factory.py                   # Alt (nicht IBAN-basiert)
```

### **5. Import-Script**
```bash
scripts/imports/import_november_fix.py
```

**Aktueller Stand:**
- ✅ Durchsucht `/mnt/buchhaltung/Buchhaltung/Kontoauszüge/` rekursiv
- ✅ Verwendet `GenobankUniversalParser` für Genobank-PDFs
- ✅ Duplikat-Check funktioniert
- ❌ Keine IBAN-basierte Factory
- ❌ Nur für November optimiert

**Muss angepasst werden:**
```python
# ALT:
if 'Genobank' in folder_name:
    parser = GenobankUniversalParser(pdf_path)

# NEU:
parser = IBANParserFactory.get_parser(pdf_path)
if parser:
    transactions = parser.parse()
```

### **6. Cron-Jobs**
```bash
# DB Backup - täglich 3 Uhr (NEU)
0 3 * * * cd /opt/greiner-portal && cp data/greiner_controlling.db data/greiner_controlling.db.backup_$(date +\%Y\%m\%d_\%H\%M\%S)

# Alte Backups löschen - behalte nur 7 (NEU)
30 3 * * * cd /opt/greiner-portal/data && ls -t greiner_controlling.db.backup_* 2>/dev/null | tail -n +8 | xargs rm -f

# Bank-PDFs Import - täglich 8:30 Uhr
30 8 * * * cd /opt/greiner-portal && venv/bin/python3 scripts/imports/import_november_fix.py >> logs/bank_import.log 2>&1
```

---

## 🔍 IM CHAT GEKLÄRT

### **1. Speicherplatz-Problem**
- **Ursache:** Stündliche Backups × 7 Tage = 32 GB
- **Lösung:** DB nach `/data` verschieben + Backup auf täglich
- **Ergebnis:** 7.4 GB frei

### **2. PDF-Formate**
- **2 verschiedene Formate:** Tagesauszüge vs. Kontoauszüge
- **IBAN-Format unterschiedlich:** Mit/ohne Leerzeichen, mit/ohne BIC
- **Endsaldo unterschiedlich:** `(Endsaldo)` vs. `neuer Kontostand`

### **3. Parser-Strategie**
- ❌ Universal-Parser patchen = falsch
- ✅ Spezialisierte Parser = richtig
- ✅ IBAN-basierte Factory = Lösung

### **4. Alle Infos parsbar**
- ✅ IBAN extrahierbar (beide Formate)
- ✅ Transaktionen erkennbar
- ✅ Endsalden vorhanden (nur Parsing-Problem)
- ✅ DB-Schema passt

### **5. Import-Script**
- ✅ Grundlogik funktioniert
- ✅ Duplikat-Check funktioniert
- ❌ Muss auf IBAN-Factory umgestellt werden

---

## 🎯 PRIORITÄTEN FÜR TAG 59

### **1. HÖCHSTE PRIORITÄT: Parser-Architektur**
```
1.1 GenobankTagesauszugParser erstellen
1.2 GenobankKontoauszugParser erstellen
1.3 IBAN-Factory erstellen
1.4 Test-Suite für alle 11 Konten
```

### **2. MITTLERE PRIORITÄT: Import-Script**
```
2.1 import_november_fix.py → IBANParserFactory
2.2 Test: Alle Konten importieren
2.3 Verify: Endsalden korrekt
```

### **3. NIEDRIGE PRIORITÄT: Dokumentation**
```
3.1 Parser-Dokumentation aktualisieren
3.2 README für Parser-Architektur
```

---

## 📝 WICHTIGE ERKENNTNISSE

### **1. IBAN ist Schlüssel**
- ✅ IBAN aus PDF-Inhalt = zuverlässig
- ❌ Dateiname = unzuverlässig (User-Fehler)
- ✅ Factory-Mapping über IBAN = robust

### **2. Spezialisierung > Generalisierung**
```
❌ Ein Parser für alles = komplex, fehleranfällig
✅ Mehrere spezialisierte Parser = einfach, stabil
```

### **3. Tests sind essentiell**
- Vor jeder Änderung: Test-Suite laufen lassen
- Nach jeder Änderung: Alle Formate testen
- Rollback-Plan bereithalten

### **4. DB-Schema beachten**
- `konto_id` ist der Schlüssel (nicht `bank_account_id`)
- Keine `banken`-Tabelle zwingend erforderlich
- IBAN ist UNIQUE und NOT NULL

---

## ⚠️ KRITISCHE PUNKTE FÜR NÄCHSTE SESSION

1. **KEIN Code ohne Test!**
   - Erst Test-Suite erstellen
   - Dann Parser bauen
   - Dann testen

2. **KEIN Patching!**
   - Alte Parser in Ruhe lassen
   - Neue Parser von Grund auf bauen
   - Factory verbindet alles

3. **IBAN-Mapping vollständig!**
   - Alle 11 Konten erfassen
   - Jedes Konto einem Parser zuordnen
   - Kein Konto vergessen

4. **Import-Script letzte Änderung!**
   - Erst Parser fertig
   - Dann Factory fertig
   - Dann Import-Script anpassen

---

## 📦 DELIVERABLES FÜR TAG 59

**Am Ende von Tag 59 sollten wir haben:**
```
✅ parsers/genobank/genobank_tagesauszug_parser.py
✅ parsers/genobank/genobank_kontoauszug_parser.py
✅ parsers/genobank/genobank_base.py
✅ parsers/iban_parser_factory.py (mit allen 11 IBANs)
✅ scripts/tests/test_all_parsers.py (Test-Suite)
✅ scripts/imports/import_universal.py (mit Factory)
✅ SESSION_WRAP_UP_TAG59.md
```

**Erfolgskriterien:**
- ✅ Alle 11 Konten haben korrekten Parser
- ✅ Alle Parser-Tests grün
- ✅ Import-Test für alle Konten erfolgreich
- ✅ Endsalden für alle verfügbaren PDFs korrekt
- ✅ Keine Duplikate
- ✅ November-Import läuft weiterhin

---

**STATUS:** ✅ Rollback durchgeführt, System stabil, bereit für saubere Neuimplementierung

**NÄCHSTER SCHRITT:** Parser-Architektur von Grund auf neu bauen (TAG 59)

