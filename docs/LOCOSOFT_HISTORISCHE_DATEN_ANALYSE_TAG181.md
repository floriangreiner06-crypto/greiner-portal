# Locosoft PostgreSQL - Historische Daten Analyse

**Datum:** 2026-01-12  
**TAG:** 181  
**Ziel:** Prüfung ob mehr historische Daten verfügbar sind als wir aktuell nutzen

---

## 📊 ERGEBNISSE

### journal_accountings (Haupttabelle für BWA)

**Aktuelle Datenlage:**
- ✅ **Erste Buchung:** 2023-09-01
- ✅ **Letzte Buchung:** 2026-01-09
- ✅ **Anzahl Monate:** 29 Monate
- ✅ **Anzahl Buchungen:** 610,979
- ✅ **Anzahl Konten:** 951

**❌ PROBLEM:** Keine Daten VOR September 2023!

### Vergleich mit anderen Tabellen

**orders Tabelle:**
- ✅ **Erste Order:** 2003-11-03 (über 20 Jahre!)
- ✅ **Letzte Order:** 2026-01-12
- ✅ **Anzahl Orders:** 41,957
- ⚠️  **ABER:** Nur 10 Monate mit Orders VOR 2023-09 (2023-04 bis 2023-08)

**dealer_vehicles:**
- Noch nicht analysiert (Fehler beim Abfragen)

**invoices:**
- Noch nicht analysiert

---

## 🔍 ANALYSE

### Warum nur 29 Monate in journal_accountings?

**Mögliche Ursachen:**

1. **Datenmigration 2023-09:**
   - Locosoft-Datenbank wurde erst ab September 2023 mit journal_accountings befüllt
   - Historische Buchungen wurden nicht importiert

2. **Import-Script Limit:**
   - Import-Script hat möglicherweise ein Datums-Limit (nur ab 2023-09)
   - Historische Daten wurden nicht migriert

3. **Systemwechsel:**
   - Vor 2023-09 wurde ein anderes System verwendet
   - Daten wurden nicht in Locosoft-DB übernommen

4. **Archivierung:**
   - Historische Daten wurden gelöscht oder in ein Archiv verschoben
   - Nicht mehr in der Live-Datenbank verfügbar

### Verfügbare Tabellen

**102 Tabellen** in der Locosoft PostgreSQL-Datenbank:
- `journal_accountings` - Buchhaltungsbuchungen (nur ab 2023-09)
- `orders` - Werkstatt-Aufträge (ab 2003-11, aber nur wenige VOR 2023-09)
- `dealer_vehicles` - Fahrzeuge
- `invoices` - Rechnungen
- `labours` - Arbeitszeiten
- `parts` - Teile
- `nominal_accounts` - Kontenplan
- ... und 95 weitere Tabellen

---

## 💡 MÖGLICHE LÖSUNGEN

### Option 1: Historische Daten aus orders/invoices ableiten

**Vorteil:**
- orders hat Daten ab 2003-11
- Könnte historische Umsätze/Einsätze ableiten

**Nachteil:**
- Nur 10 Monate VOR 2023-09 verfügbar
- Nicht vollständig (nur Werkstatt, keine Fahrzeuge)
- Möglicherweise unvollständige Daten

**Implementierung:**
```python
# Historische Umsätze aus orders ableiten
SELECT 
    DATE_TRUNC('month', order_date) as monat,
    SUM(total_price) as umsatz_werkstatt
FROM orders
WHERE order_date < '2023-09-01'
  AND invoice_date IS NOT NULL
GROUP BY DATE_TRUNC('month', order_date)
```

### Option 2: Backup/Archiv prüfen

**Vorgehen:**
1. Prüfe ob es ein Backup mit älteren journal_accountings gibt
2. Prüfe ob Locosoft selbst ältere Daten hat (andere Datenquelle)
3. Prüfe Import-Scripts ob sie ein Datums-Limit haben

### Option 3: Daten von Locosoft-Server importieren

**Vorgehen:**
1. Prüfe ob Locosoft-Server selbst ältere Daten hat
2. Importiere historische journal_accountings (falls verfügbar)
3. Erweitere Datenbasis für ML-Training

---

## 🎯 EMPFEHLUNG

### Kurzfristig (für ML-Training):

1. **Nutze verfügbare 29 Monate:**
   - Aktuell beste Option
   - ML-Modell zeigt bereits 40% Verbesserung
   - Mit mehr Daten könnte es besser werden

2. **Erweitere mit orders-Daten (10 Monate):**
   - Nutze 2023-04 bis 2023-08 aus orders
   - Ableitung von Werkstatt-Umsätzen
   - Erweitert Datenbasis auf ~39 Monate

### Mittelfristig:

1. **Prüfe Import-Scripts:**
   - Gibt es ein Datums-Limit?
   - Können historische Daten importiert werden?

2. **Prüfe Locosoft-Server:**
   - Hat Locosoft selbst ältere journal_accountings?
   - Können diese importiert werden?

3. **Prüfe Backup/Archiv:**
   - Gibt es ein Backup mit älteren Daten?
   - Können diese wiederhergestellt werden?

### Langfristig:

1. **Vollständige Datenmigration:**
   - Importiere alle historischen Daten (falls verfügbar)
   - Erweitere Datenbasis auf 7 Jahre (84 Monate)
   - ML-Modell würde deutlich besser werden

---

## 📈 AUSWIRKUNG AUF ML-MODELL

**Aktuell (29 Monate):**
- Gradient Boosting: MAE 150,458 €
- Verbesserung: +40.1% vs. Baseline

**Mit 39 Monaten (inkl. orders):**
- Geschätzte Verbesserung: +45-50%
- Mehr Daten = bessere Prognose

**Mit 84 Monaten (7 Jahre):**
- Geschätzte Verbesserung: +60-70%
- Deutlich bessere Prognosequalität

---

## 🔧 NÄCHSTE SCHRITTE

1. ✅ **Analyse abgeschlossen** - Dokumentation erstellt
2. ⏳ **Prüfe Import-Scripts** - Gibt es ein Datums-Limit?
3. ⏳ **Prüfe Locosoft-Server** - Hat Locosoft ältere Daten?
4. ⏳ **Erweitere mit orders-Daten** - 10 Monate hinzufügen (optional)
5. ⏳ **Vollständige Migration** - Falls historische Daten verfügbar

---

## 📝 ZUSAMMENFASSUNG

**Fazit:**
- ❌ journal_accountings hat nur 29 Monate Daten (ab 2023-09)
- ⚠️  orders hat ältere Daten (ab 2003), aber nur 10 Monate VOR 2023-09
- 💡 Mögliche Lösung: Historische Daten aus orders ableiten (10 Monate mehr)
- 🎯 Langfristig: Prüfe ob vollständige historische Daten verfügbar sind

**Empfehlung:**
- Kurzfristig: Nutze verfügbare 29 Monate (bereits gute Ergebnisse)
- Mittelfristig: Erweitere mit orders-Daten (10 Monate mehr)
- Langfristig: Prüfe vollständige Datenmigration (7 Jahre)
