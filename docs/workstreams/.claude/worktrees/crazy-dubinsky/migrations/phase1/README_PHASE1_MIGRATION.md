# 🚀 PHASE 1 MIGRATION - BANKENSPIEGEL 3.0

## 📋 Übersicht

Diese Migration fügt die wichtigsten fehlenden Tabellen und Views zum bestehenden Bankenspiegel-System hinzu.

## 🎯 Was wird migriert?

### NEUE TABELLEN:
1. **kontostand_historie** 🔴 KRITISCH
   - Historische Kontostände für Zeitreihen
   - Automatische Initialisierung aus bestehenden Transaktionen
   
2. **kreditlinien** 🔴 KRITISCH
   - Kreditlinien und Limits pro Konto
   - Zinssätze und Gültigkeitszeiträume
   
3. **kategorien** 🟡 WICHTIG
   - 16 Standard-Kategorien für Transaktions-Klassifizierung
   - Steuerrelevanz-Markierung
   
4. **pdf_imports** 🟡 WICHTIG
   - Import-Tracking-Protokoll
   - Automatische Initialisierung aus bestehenden PDF-Quellen

### NEUE VIEWS:
1. **v_aktuelle_kontostaende** 🔴 KRITISCH
   - Aktuellster Saldo pro Konto
   
2. **v_monatliche_umsaetze** 🔴 KRITISCH
   - Einnahmen/Ausgaben pro Monat und Konto
   
3. **v_transaktionen_uebersicht** 🟡 WICHTIG
   - Erweiterte Transaktionsansicht mit Bank- und Kontoinfos
   
4. **v_kategorie_auswertung** 🟢 OPTIONAL
   - Statistiken pro Kategorie

## 📦 Dateien

```
001_add_kontostand_historie.sql    # Migration für Kontostand-Historie
002_add_kreditlinien.sql           # Migration für Kreditlinien
003_add_kategorien.sql             # Migration für Kategorien
004_add_pdf_imports.sql            # Migration für PDF-Import-Tracking
005_add_views.sql                  # Migration für alle Views
run_phase1_migrations.sh           # Master-Script (führt alle aus)
README_PHASE1_MIGRATION.md         # Diese Anleitung
```

## 🔧 Installation

### Option 1: Master-Script (EMPFOHLEN)

```bash
# 1. Dateien auf Server kopieren
cd /opt/greiner-portal
mkdir -p migrations/phase1
cd migrations/phase1

# Upload aller .sql Dateien und run_phase1_migrations.sh hierher

# 2. Ausführbar machen
chmod +x run_phase1_migrations.sh

# 3. Ausführen (erstellt automatisch Backup!)
./run_phase1_migrations.sh
```

### Option 2: Manuelle Ausführung

```bash
cd /opt/greiner-portal/migrations/phase1

# Backup erstellen
cp /opt/greiner-portal/data/greiner_controlling.db \
   /opt/greiner-portal/data/greiner_controlling.db.backup_$(date +%Y%m%d_%H%M%S)

# Migrationen einzeln ausführen
sqlite3 /opt/greiner-portal/data/greiner_controlling.db < 001_add_kontostand_historie.sql
sqlite3 /opt/greiner-portal/data/greiner_controlling.db < 002_add_kreditlinien.sql
sqlite3 /opt/greiner-portal/data/greiner_controlling.db < 003_add_kategorien.sql
sqlite3 /opt/greiner-portal/data/greiner_controlling.db < 004_add_pdf_imports.sql
sqlite3 /opt/greiner-portal/data/greiner_controlling.db < 005_add_views.sql
```

## ✅ Validierung

Nach erfolgreicher Migration sollte folgendes verfügbar sein:

```bash
# Tabellen prüfen
sqlite3 /opt/greiner-portal/data/greiner_controlling.db ".tables"

# Sollte enthalten:
# - kontostand_historie
# - kreditlinien
# - kategorien
# - pdf_imports

# Views prüfen
sqlite3 /opt/greiner-portal/data/greiner_controlling.db \
  "SELECT name FROM sqlite_master WHERE type='view'"

# Sollte enthalten:
# - v_aktuelle_kontostaende
# - v_monatliche_umsaetze
# - v_transaktionen_uebersicht
# - v_kategorie_auswertung

# Daten prüfen
sqlite3 /opt/greiner-portal/data/greiner_controlling.db << EOF
SELECT 
    (SELECT COUNT(*) FROM kontostand_historie) as Kontostände,
    (SELECT COUNT(*) FROM kreditlinien) as Kreditlinien,
    (SELECT COUNT(*) FROM kategorien) as Kategorien,
    (SELECT COUNT(*) FROM pdf_imports) as PDF_Imports;
EOF
```

## 🎯 Erwartete Ergebnisse

Nach erfolgreicher Migration:

- ✅ **kontostand_historie**: Mind. 1 Eintrag pro Konto (aus letzter Transaktion)
- ✅ **kreditlinien**: Leer (manuell zu befüllen)
- ✅ **kategorien**: 16 Standard-Kategorien
- ✅ **pdf_imports**: 1 Eintrag pro eindeutige PDF-Quelle
- ✅ **Views**: Alle 4 Views funktionsfähig

## 🔄 Rollback

Falls etwas schiefgeht:

```bash
# Backup wiederherstellen
cp /opt/greiner-portal/data/greiner_controlling.db.backup_YYYYMMDD_HHMMSS \
   /opt/greiner-portal/data/greiner_controlling.db
```

## 📊 Nächste Schritte

Nach erfolgreicher Phase 1 Migration:

1. ✅ Schema-Basis ist komplett
2. 🔄 Phase 2: REST API entwickeln
3. 🔄 Phase 3: Frontend aufbauen
4. 🔄 Phase 4: Stellantis-Integration (`fahrzeugfinanzierungen` Tabelle)

## ⚠️ Wichtige Hinweise

- **Automatisches Backup**: Das Master-Script erstellt automatisch ein Backup vor der Migration
- **Sichere Ausführung**: Alle Migrationen nutzen `IF NOT EXISTS` - können mehrfach ausgeführt werden
- **Idempotent**: Erneute Ausführung ist sicher und verändert bestehende Daten nicht
- **Initiale Daten**: Einige Tabellen werden mit berechneten Daten aus bestehenden Transaktionen befüllt

## 📞 Support

Bei Problemen:
1. Prüfe das Backup: `ls -lh /opt/greiner-portal/data/*.backup*`
2. Prüfe die Datenbank-Integrität: `sqlite3 /opt/greiner-portal/data/greiner_controlling.db "PRAGMA integrity_check;"`
3. Schaue in die Fehlerausgabe des Scripts

---

**Version:** 1.0  
**Datum:** 2025-11-07  
**Projekt:** Greiner Portal - Bankenspiegel 3.0
