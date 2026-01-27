# Analyse: Christian Meyer - App-Stempelung Auftrag 39779

**Datum:** 2026-01-21  
**TAG:** 206  
**Mitarbeiter:** Christian Meyer (employee_number: 1014)  
**Auftrag:** 39779  
**Stempelung:** Über "Mein Autohaus App" (ca. 1 Minute)

---

## 📋 Ausgangssituation

**Information vom User:**
> "Christian Meyer hat gerade auf den Auftrag 39779 über die Mein Autohaus App angestempelt und nach ca 1 Minute wieder abgestempelt."

**Erwartung:**
- Stempelung sollte in der `times`-Tabelle sichtbar sein
- `type = 2` (Stempelzeit)
- `order_number = 39779`
- `employee_number = 1014`
- Dauer: ca. 1 Minute

---

## 🔍 Datenbank-Analyse

### 1. Mitarbeiter-Identifikation

**Query:**
```sql
SELECT employee_number, name FROM employees 
WHERE name ILIKE '%meyer%' AND is_latest_record = true;
```

**Ergebnis:**
- ✅ **Christian Meyer gefunden:** `employee_number = 1014`
- Name in Locosoft: `Meyer,Christian`

### 2. Stempelzeiten für heute (2026-01-21)

**Query:**
```sql
SELECT employee_number, type, order_number, start_time, end_time, 
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
FROM times 
WHERE employee_number = 1014 
  AND DATE(start_time) = CURRENT_DATE 
  AND type = 2;
```

**Ergebnis:**
- ❌ **KEINE Stempelzeiten für heute gefunden** (0 Zeilen)

### 3. Stempelzeiten für Auftrag 39779

**Query:**
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE order_number = 39779 
  AND start_time >= NOW() - INTERVAL '24 hours';
```

**Ergebnis:**
- ❌ **KEINE Stempelzeiten für Auftrag 39779 in den letzten 24 Stunden** (0 Zeilen)

### 4. Alle Stempelzeiten von Christian Meyer

**Query:**
```sql
SELECT COUNT(*) as total, 
       MIN(start_time) as erste_stempelung, 
       MAX(start_time) as letzte_stempelung 
FROM times 
WHERE employee_number = 1014 AND type = 2;
```

**Ergebnis:**
- **Total:** 470 Stempelungen
- **Erste Stempelung:** 2023-09-06 14:21:10
- **Letzte Stempelung:** 2025-04-14 13:41:10 ⚠️

**⚠️ WICHTIG:** Die letzte Stempelzeit war am **14.04.2025** (vor fast 9 Monaten)!

### 5. Anwesenheitszeiten (type=1) für heute

**Query:**
```sql
SELECT employee_number, type, start_time, end_time, 
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
FROM times 
WHERE employee_number = 1014 
  AND DATE(start_time) = CURRENT_DATE 
  AND type = 1;
```

**Ergebnis:**
- ❌ **KEINE Anwesenheitszeiten für heute gefunden** (0 Zeilen)

### 6. Anwesenheitszeiten in den letzten 7 Tagen

**Query:**
```sql
SELECT employee_number, type, start_time, end_time, 
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
FROM times 
WHERE employee_number = 1014 
  AND start_time >= NOW() - INTERVAL '7 days' 
  AND type = 1;
```

**Ergebnis:**
- ✅ **Anwesenheitszeiten vorhanden:**
  - 2026-01-20: 07:41-12:17 (276 Min = 4:36 Std)
  - 2026-01-19: 07:08-15:29 (501 Min = 8:21 Std)
  - 2026-01-16: 07:46-15:01 (435 Min = 7:15 Std)
  - 2026-01-15: 07:47-15:53 (486 Min = 8:06 Std)

---

## ❓ Mögliche Erklärungen

### 1. Synchronisations-Verzögerung ⏰

**Hypothese:** Die App-Stempelung wurde noch nicht in die PostgreSQL-Datenbank synchronisiert.

**Mögliche Ursachen:**
- Locosoft synchronisiert App-Stempelungen nicht in Echtzeit
- Batch-Update (z.B. alle 15 Minuten, stündlich, täglich)
- Verzögerung zwischen App und Datenbank

**Prüfung:**
- ⏳ Warten und später erneut prüfen
- ⏳ Prüfen, ob es einen Sync-Job gibt (Celery, Cron, etc.)

### 2. Andere Datenquelle 📊

**Hypothese:** App-Stempelungen werden in einer anderen Tabelle gespeichert.

**Mögliche Tabellen:**
- `times_mobile` (falls vorhanden)
- `app_stampings` (falls vorhanden)
- Andere Tabelle für mobile Stempelungen

**Prüfung:**
```sql
-- Prüfe alle Tabellen mit "time" oder "stamp" im Namen
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name ILIKE '%time%' OR table_name ILIKE '%stamp%');
```

### 3. Falsche employee_number 🔢

**Hypothese:** Die App verwendet eine andere employee_number.

**Mögliche Ursachen:**
- App verwendet interne ID statt employee_number
- Mapping zwischen App-User und Locosoft employee_number fehlt
- Christian Meyer hat mehrere employee_numbers

**Prüfung:**
```sql
-- Prüfe alle employee_numbers für "Meyer"
SELECT employee_number, name, is_latest_record 
FROM employees 
WHERE name ILIKE '%meyer%';
```

### 4. Stempelung noch nicht abgeschlossen ⏸️

**Hypothese:** Die Stempelung wurde gestartet, aber noch nicht beendet (end_time IS NULL).

**Prüfung:**
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE employee_number = 1014 
  AND order_number = 39779 
  AND end_time IS NULL;
```

### 5. Auftrag 39779 existiert nicht oder ist nicht aktiv 📋

**Hypothese:** Der Auftrag existiert nicht oder ist in einem Status, der keine Stempelungen zulässt.

**Prüfung:**
```sql
-- Prüfe ob Auftrag 39779 existiert
SELECT number, status, created_date, closed_date 
FROM orders 
WHERE number = 39779;
```

---

## 🔧 Empfohlene Prüfungen

### Sofortige Prüfungen

1. **Prüfe alle Tabellen mit Zeitbezug:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
     AND (table_name ILIKE '%time%' OR table_name ILIKE '%stamp%' OR table_name ILIKE '%app%');
   ```

2. **Prüfe offene Stempelungen:**
   ```sql
   SELECT employee_number, type, order_number, start_time, end_time 
   FROM times 
   WHERE employee_number = 1014 
     AND end_time IS NULL 
     AND start_time >= NOW() - INTERVAL '24 hours';
   ```

3. **Prüfe Auftrag 39779:**
   ```sql
   SELECT number, status, created_date, closed_date, subsidiary 
   FROM orders 
   WHERE number = 39779;
   ```

4. **Prüfe alle Stempelungen für Auftrag 39779 (alle Mitarbeiter):**
   ```sql
   SELECT employee_number, type, start_time, end_time, 
          EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
   FROM times 
   WHERE order_number = 39779 
     AND start_time >= NOW() - INTERVAL '24 hours' 
   ORDER BY start_time DESC;
   ```

### Spätere Prüfungen (nach Sync-Zyklus)

1. **Erneut prüfen nach 15 Minuten:**
   - Falls Batch-Sync alle 15 Minuten läuft
   
2. **Erneut prüfen nach 1 Stunde:**
   - Falls Batch-Sync stündlich läuft

3. **Erneut prüfen am nächsten Tag:**
   - Falls Tagesabschluss nötig ist

---

## 📊 Vergleich: App vs. Terminal-Stempelung

### Erwartete Unterschiede

| Aspekt | Terminal-Stempelung | App-Stempelung |
|--------|---------------------|----------------|
| **Synchronisation** | Sofort | Möglicherweise verzögert |
| **Tabelle** | `times` | `times` (oder andere?) |
| **Felder** | Standard | Möglicherweise zusätzliche Felder |
| **Deduplizierung** | Standard | Möglicherweise andere Logik |

### Bekannte App-Features

- **"Mein Autohaus App"** von Locosoft
- Mobile Stempelung auf Aufträge
- Stempelung auf einzelne Positionen möglich
- Offline-Funktionalität (Sync später)

---

## 🎯 Nächste Schritte

### 1. Sofort (heute)
- [ ] Prüfe alle Tabellen mit Zeitbezug
- [ ] Prüfe offene Stempelungen (end_time IS NULL)
- [ ] Prüfe Auftrag 39779 (existiert er?)
- [ ] Prüfe alle Stempelungen für Auftrag 39779 (alle Mitarbeiter)

### 2. Später (nach Sync-Zyklus)
- [ ] Erneut prüfen nach 15 Minuten
- [ ] Erneut prüfen nach 1 Stunde
- [ ] Erneut prüfen am nächsten Tag

### 3. Dokumentation
- [ ] Sync-Zyklus für App-Stempelungen dokumentieren
- [ ] Unterschiede zwischen App und Terminal dokumentieren
- [ ] Troubleshooting-Guide erstellen

---

## 💡 Erkenntnisse

1. **Keine Stempelzeiten für heute gefunden**
   - Weder für Christian Meyer noch für Auftrag 39779
   - Letzte Stempelzeit war am 14.04.2025 (vor 9 Monaten)

2. **Anwesenheitszeiten vorhanden**
   - Letzte Anwesenheit: 2026-01-20 (gestern)
   - Christian Meyer ist aktiv (stempelt Anwesenheit)

3. **Mögliche Synchronisations-Verzögerung**
   - App-Stempelungen werden möglicherweise nicht in Echtzeit synchronisiert
   - Batch-Update-Zyklus unbekannt

4. **Weitere Prüfungen nötig**
   - Andere Tabellen prüfen
   - Offene Stempelungen prüfen
   - Auftrag 39779 prüfen

---

## 📝 SQL-Queries für weitere Analyse

### Prüfe alle Tabellen mit Zeitbezug
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (table_name ILIKE '%time%' OR table_name ILIKE '%stamp%' OR table_name ILIKE '%app%')
ORDER BY table_name;
```

### Prüfe offene Stempelungen
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE employee_number = 1014 
  AND end_time IS NULL 
  AND start_time >= NOW() - INTERVAL '24 hours';
```

### Prüfe Auftrag 39779
```sql
SELECT number, status, created_date, closed_date, subsidiary 
FROM orders 
WHERE number = 39779;
```

### Prüfe alle Stempelungen für Auftrag 39779
```sql
SELECT employee_number, type, start_time, end_time, 
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
FROM times 
WHERE order_number = 39779 
  AND start_time >= NOW() - INTERVAL '24 hours' 
ORDER BY start_time DESC;
```

---

---

## ✅ ZUSÄTZLICHE ERKENNTNISSE (nach weiteren Prüfungen)

### 1. Auftrag 39779 existiert ✅

**Query:**
```sql
SELECT number, order_date, subsidiary, has_open_positions, has_closed_positions 
FROM orders 
WHERE number = 39779;
```

**Ergebnis:**
- ✅ **Auftrag 39779 existiert**
- **Order Date:** 2026-01-02 13:33:00
- **Subsidiary:** 1 (DEGO)
- **Has Open Positions:** true
- **Has Closed Positions:** false

### 2. Andere Stempelungen heute (Vergleich)

**Query:**
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE start_time >= NOW() - INTERVAL '2 hours' 
  AND type = 2 
ORDER BY start_time DESC 
LIMIT 20;
```

**Ergebnis:**
- ✅ **Andere Mitarbeiter haben heute gestempelt:**
  - MA 5014: Auftrag 220729 (15:53, noch offen - end_time = NULL)
  - MA 5004: Auftrag 220858 (15:48, noch offen - end_time = NULL)
  - MA 5017: Auftrag 39406 (15:42)
  - MA 5008: Auftrag 40226 (15:38)
  - MA 5003: Auftrag 31 (15:34)
  - MA 5016: Auftrag 313575 (15:21)

**⚠️ WICHTIG:** Viele Stempelungen haben `end_time = NULL` (noch offen)!

### 3. Keine Stempelungen für Christian Meyer heute

**Query:**
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE employee_number = 1014 
  AND start_time >= '2026-01-21 00:00:00' 
  AND start_time < '2026-01-22 00:00:00';
```

**Ergebnis:**
- ❌ **KEINE Stempelungen für Christian Meyer heute** (0 Zeilen)

### 4. Keine Stempelungen für Auftrag 39779 heute

**Query:**
```sql
SELECT employee_number, type, order_number, start_time, end_time 
FROM times 
WHERE order_number = 39779 
  AND start_time >= NOW() - INTERVAL '24 hours';
```

**Ergebnis:**
- ❌ **KEINE Stempelungen für Auftrag 39779 heute** (0 Zeilen)

---

## 🎯 FAZIT

### Zusammenfassung

1. **Auftrag 39779 existiert** ✅
   - Order Date: 2026-01-02
   - Subsidiary: 1 (DEGO)
   - Hat offene Positionen

2. **Keine Stempelung für Christian Meyer heute** ❌
   - Weder für Auftrag 39779 noch für andere Aufträge
   - Letzte Stempelzeit: 2025-04-14 (vor 9 Monaten)

3. **Andere Mitarbeiter stempeln heute** ✅
   - Viele Stempelungen mit `end_time = NULL` (noch offen)
   - Stempelungen werden in Echtzeit synchronisiert (für andere Mitarbeiter)

4. **Mögliche Erklärungen:**
   - ⏰ **Synchronisations-Verzögerung:** App-Stempelung wurde noch nicht synchronisiert
   - 🔢 **Falsche employee_number:** App verwendet möglicherweise andere ID
   - ⏸️ **Stempelung noch offen:** Möglicherweise mit `end_time = NULL` gespeichert, aber nicht gefunden
   - 📱 **App-spezifisches Problem:** Stempelung wurde nicht korrekt übertragen

### Empfehlung

1. **Sofort prüfen:**
   - Prüfe Locosoft-UI direkt (nicht nur Datenbank)
   - Prüfe ob Christian Meyer in der App korrekt angemeldet ist
   - Prüfe ob die Stempelung in Locosoft sichtbar ist

2. **Später prüfen:**
   - Erneut prüfen nach 15-30 Minuten (Sync-Zyklus)
   - Prüfe ob Stempelung am nächsten Tag sichtbar ist

3. **Dokumentation:**
   - Sync-Zyklus für App-Stempelungen dokumentieren
   - Unterschiede zwischen App und Terminal dokumentieren

---

---

## 🎯 WICHTIGE ERKENNTNIS: Stempelung existiert in Locosoft, aber nicht in Datenbank!

### Locosoft-UI zeigt Stempelung ✅

**Aus Locosoft-Screenshot (21.01.2026, 15:35):**
- **Auftrag:** 39779
- **MA-Nr.:** 1014 (Christian Meyer)
- **Stempelung:** 21.01.26 15:35 - 15:37 (2 Minuten)
- **Stemp.AW:** 0,50
- **Position:** 1,02 (Opel Rent)
- **Realzeit:** 15:35 (gestempelt) → 15:37 (aktuell)

**⚠️ KRITISCH:** Die Stempelung ist in Locosoft sichtbar, aber **NICHT in der PostgreSQL-Datenbank**!

### Datenbank-Abfrage (erneut)

**Query:**
```sql
SELECT employee_number, type, order_number, order_position, start_time, end_time 
FROM times 
WHERE employee_number = 1014 
  AND order_number = 39779 
  AND start_time >= '2026-01-21 15:30:00' 
  AND start_time <= '2026-01-21 15:40:00';
```

**Ergebnis:**
- ❌ **KEINE Stempelung in Datenbank gefunden** (0 Zeilen)

### Mögliche Erklärungen

1. **Synchronisations-Verzögerung** ⏰
   - Locosoft zeigt Stempelung in Echtzeit
   - PostgreSQL-Datenbank wird nicht in Echtzeit aktualisiert
   - Batch-Update-Zyklus unbekannt (möglicherweise stündlich, täglich, etc.)

2. **Andere Datenquelle** 📊
   - App-Stempelungen werden möglicherweise in einer anderen Tabelle gespeichert
   - Erst nach Verarbeitung in `times`-Tabelle übertragen
   - Zwischenspeicherung in App-spezifischer Tabelle

3. **Transaktions-Verzögerung** 🔄
   - Stempelung wird in Locosoft-Hauptdatenbank gespeichert
   - PostgreSQL-Datenbank (`loco_auswertung_db`) wird separat synchronisiert
   - Verzögerung zwischen Hauptdatenbank und Auswertungsdatenbank

4. **App-spezifische Verarbeitung** 📱
   - App-Stempelungen werden möglicherweise anders verarbeitet als Terminal-Stempelungen
   - Zusätzliche Validierung oder Verarbeitungsschritte
   - Erst nach Abschluss der Verarbeitung in `times`-Tabelle

### Auswirkungen auf KPI-Berechnung

**⚠️ KRITISCH für KPI-Berechnung:**
- Wenn App-Stempelungen nicht in Echtzeit in der Datenbank sind
- Dann werden aktuelle KPIs nicht korrekt berechnet
- Verzögerung kann Stunden oder Tage betragen

**Empfehlung:**
- Sync-Zyklus für App-Stempelungen dokumentieren
- KPI-Berechnung entsprechend anpassen (z.B. nur abgeschlossene Stempelungen)
- Oder: Direkt aus Locosoft-API lesen (falls verfügbar)

---

---

## ✅ UPDATE: Stempelung jetzt in Datenbank gefunden!

### Datenbank-Abfrage (erneut nach Sync)

**Query:**
```sql
SELECT employee_number, type, order_number, order_position, start_time, end_time, 
       EXTRACT(EPOCH FROM (end_time - start_time))/60 AS dauer_min 
FROM times 
WHERE employee_number = 1014 
  AND order_number = 39779 
  AND start_time >= '2026-01-21 15:30:00';
```

**Ergebnis:**
- ✅ **Stempelung gefunden!**
  - **employee_number:** 1014
  - **order_number:** 39779
  - **order_position:** 1
  - **order_position_line:** 2 (entspricht Position 1,02 in Locosoft)
  - **start_time:** 2026-01-21 15:35:16
  - **end_time:** 2026-01-21 15:37:50
  - **dauer_min:** 2.57 Minuten (≈ 2 Minuten 34 Sekunden)

### Vergleich: Locosoft-UI vs. Datenbank

| Aspekt | Locosoft-UI | PostgreSQL-Datenbank |
|--------|-------------|---------------------|
| **Startzeit** | 15:35 | 15:35:16 ✅ |
| **Endzeit** | 15:37 | 15:37:50 ✅ |
| **Dauer** | ~2 Minuten | 2.57 Minuten ✅ |
| **Position** | 1,02 | 1 (order_position_line: 2) ✅ |
| **Stemp.AW** | 0,50 | - (nicht in times-Tabelle) |

**✅ ÜBEREINSTIMMUNG:** Die Zeiten stimmen überein!

### Synchronisations-Verzögerung bestätigt ⏰

**Timeline:**
1. **15:35-15:37:** Stempelung in Locosoft-UI sichtbar
2. **15:51 (erste Prüfung):** Stempelung NICHT in Datenbank
3. **16:00+ (spätere Prüfung):** Stempelung JETZT in Datenbank

**Verzögerung:** Ca. 15-30 Minuten zwischen Locosoft-UI und PostgreSQL-Datenbank

### Erkenntnisse

1. **App-Stempelungen werden synchronisiert** ✅
   - Aber nicht in Echtzeit
   - Verzögerung: ca. 15-30 Minuten

2. **Daten sind korrekt** ✅
   - Startzeit, Endzeit, Dauer stimmen überein
   - Position korrekt erfasst

3. **Auswirkungen auf KPI-Berechnung:**
   - Aktuelle KPIs können um 15-30 Minuten verzögert sein
   - Für Echtzeit-Dashboards: Problem
   - Für Tages-/Monatsauswertungen: Kein Problem

---

**Status:** ✅ Analyse abgeschlossen  
**Ergebnis:** Stempelung existiert und wurde synchronisiert - **Synchronisations-Verzögerung von ca. 15-30 Minuten bestätigt!**
