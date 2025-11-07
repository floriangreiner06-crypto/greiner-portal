# 🔍 DUPLIKATE-ANALYSE - ANLEITUNG

## 📋 Was macht die Analyse?

Diese Analyse prüft **5 kritische Bereiche**:

1. **Duplikate in letzten 30 Tagen** - Gleiche Buchungen mehrfach vorhanden?
2. **PDF-Import-Häufigkeit** - Welche PDFs haben viele Transaktionen erzeugt?
3. **Zeitraum-Logik** - Stimmen die Zahlen für die letzten 30 Tage?
4. **Gesamt-Statistik** - Überblick über alle Daten
5. **Duplikate gesamt** - Wie viele Duplikate gibt es insgesamt?

---

## 🚀 SCHNELLSTART (auf dem Server)

### Option A: Automatisches Script 🎯

```bash
# 1. SSH zum Server
ssh ag-admin@10.80.80.20
# Password: OHL.greiner2025

# 2. SQL-Script hochladen
# (du musst duplikate_analyse.sql nach /tmp/ kopieren)
scp duplikate_analyse.sql ag-admin@10.80.80.20:/tmp/

# 3. Script ausführen
cd /opt/greiner-portal
sqlite3 data/greiner_controlling.db < /tmp/duplikate_analyse.sql > /tmp/analyse_ergebnis.txt

# 4. Ergebnisse anzeigen
cat /tmp/analyse_ergebnis.txt
```

### Option B: Manuelle Queries 🔧

```bash
# SSH zum Server
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal

# SQLite öffnen
sqlite3 data/greiner_controlling.db

# Dann die Queries einzeln ausführen (siehe unten)
```

---

## 📊 DIE 5 QUERIES IM DETAIL

### Query 1: Duplikate letzte 30 Tage

```sql
SELECT 
    konto_id,
    buchungsdatum,
    betrag,
    SUBSTR(verwendungszweck, 1, 50) as verwendungszweck_kurz,
    COUNT(*) as anzahl,
    SUM(betrag) as summe
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck
HAVING COUNT(*) > 1
ORDER BY anzahl DESC
LIMIT 20;
```

**Was bedeutet das Ergebnis?**
- `anzahl > 1` = Duplikat gefunden!
- Je höher `anzahl`, desto öfter wurde die gleiche Buchung importiert

### Query 2: PDF-Import-Häufigkeit

```sql
SELECT 
    SUBSTR(pdf_quelle, 1, 60) as pdf_quelle,
    COUNT(*) as anzahl_transaktionen,
    COUNT(DISTINCT buchungsdatum) as verschiedene_tage,
    MIN(buchungsdatum) as erste_buchung,
    MAX(buchungsdatum) as letzte_buchung
FROM transaktionen
WHERE pdf_quelle IS NOT NULL
GROUP BY pdf_quelle
HAVING anzahl_transaktionen > 50
ORDER BY anzahl_transaktionen DESC
LIMIT 20;
```

**Was bedeutet das Ergebnis?**
- Zeigt PDFs, die mehr als 50 Transaktionen erzeugt haben
- `anzahl_transaktionen` vs `verschiedene_tage` gibt Hinweis auf Duplikate

### Query 3: Zeitraum-Logik

```sql
SELECT 
    DATE('now', '-30 days') as von_datum,
    DATE('now') as bis_datum,
    COUNT(*) as anzahl_transaktionen,
    ROUND(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 2) as einnahmen,
    ROUND(SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END), 2) as ausgaben,
    ROUND(SUM(betrag), 2) as saldo
FROM transaktionen
WHERE buchungsdatum >= DATE('now', '-30 days')
  AND buchungsdatum <= DATE('now');
```

**Was bedeutet das Ergebnis?**
- Sollte die gleichen Zahlen wie Dashboard zeigen
- Wenn nicht: Bug in Dashboard-Query

### Query 4: Gesamt-Statistik

```sql
SELECT 
    'Gesamt' as zeitraum,
    COUNT(*) as transaktionen,
    COUNT(DISTINCT konto_id) as konten,
    COUNT(DISTINCT pdf_quelle) as pdf_quellen,
    MIN(buchungsdatum) as aelteste,
    MAX(buchungsdatum) as neueste
FROM transaktionen;
```

### Query 5: Duplikate gesamt

```sql
SELECT 
    COUNT(*) as duplikat_gruppen,
    SUM(anzahl) as gesamt_duplikate,
    SUM(anzahl - 1) as zu_loeschende
FROM (
    SELECT 
        konto_id,
        buchungsdatum,
        betrag,
        verwendungszweck,
        COUNT(*) as anzahl
    FROM transaktionen
    GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck
    HAVING COUNT(*) > 1
);
```

**Was bedeutet das Ergebnis?**
- `duplikat_gruppen` = Anzahl verschiedener doppelter Buchungen
- `gesamt_duplikate` = Gesamtanzahl inklusive Originale
- `zu_loeschende` = Diese müssen gelöscht werden!

---

## 🔴 WAS TUN BEI DUPLIKATEN?

### Falls Duplikate gefunden werden:

1. **BACKUP ERSTELLEN** ⚠️
```bash
cd /opt/greiner-portal/data
cp greiner_controlling.db greiner_controlling.db.backup_vor_duplikat_bereinigung_$(date +%Y%m%d_%H%M%S)
```

2. **Duplikate löschen** (VORSICHT!)
```sql
-- Erstelle temporäre Tabelle mit IDs zum Behalten
CREATE TEMP TABLE keep_ids AS
SELECT MIN(id) as id
FROM transaktionen
GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck;

-- Zeige wie viele gelöscht würden (DRY RUN)
SELECT COUNT(*) as zu_loeschen
FROM transaktionen
WHERE id NOT IN (SELECT id FROM keep_ids);

-- ERST NACH PRÜFUNG: Tatsächlich löschen
-- DELETE FROM transaktionen WHERE id NOT IN (SELECT id FROM keep_ids);

-- Temp-Tabelle aufräumen
DROP TABLE keep_ids;
```

3. **Verifizieren**
```sql
-- Prüfe ob noch Duplikate existieren
SELECT COUNT(*) as remaining_duplicates
FROM (
    SELECT konto_id, buchungsdatum, betrag, verwendungszweck, COUNT(*) as cnt
    FROM transaktionen
    GROUP BY konto_id, buchungsdatum, betrag, verwendungszweck
    HAVING cnt > 1
);
```

4. **Dashboard neu testen**
```bash
curl -s http://localhost:5000/api/bankenspiegel/dashboard | python3 -m json.tool
```

---

## 📈 ERWARTETE ERGEBNISSE

### ✅ GUTES Szenario (keine Duplikate):
```
Query 1: Keine Zeilen (oder nur sehr wenige)
Query 2: PDF-Quellen zeigen sinnvolle Verteilung
Query 3: Zahlen entsprechen Dashboard (7,3 Mio scheint zu hoch!)
Query 5: zu_loeschende = 0
```

### ⚠️ PROBLEMATISCHES Szenario (viele Duplikate):
```
Query 1: Viele Zeilen mit anzahl > 2
Query 2: Gleiche PDF-Quelle mehrfach
Query 3: Zahlen viel zu hoch
Query 5: zu_loeschende > 1000
```

---

## 💡 NÄCHSTE SCHRITTE

1. **Analysiere die Ergebnisse** - Kopiere sie in den Chat
2. **Gemeinsam entscheiden** - Müssen Duplikate gelöscht werden?
3. **Backup erstellen** - Vor jeder Datenänderung!
4. **Bereinigung durchführen** - Falls nötig
5. **Frontend entwickeln** - Nachdem Daten sauber sind

---

## 📞 SUPPORT

Falls Probleme auftreten:
- Ergebnisse in Chat posten
- Niemals DELETE ohne Backup!
- Bei Unsicherheit: Erst fragen, dann löschen

---

**Version:** 1.0  
**Datum:** 2025-11-07  
**Projekt:** Greiner Portal - Bankenspiegel 3.0
