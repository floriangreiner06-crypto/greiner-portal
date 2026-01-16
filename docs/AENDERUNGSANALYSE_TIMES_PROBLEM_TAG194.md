# Änderungsanalyse: Warum funktioniert `times` nicht mehr?

**Datum:** TAG 194  
**Frage:** Warum geht es nicht mehr? Was hat sich geändert?

**⚠️ UPDATE:** Root Cause identifiziert - Siehe `LOCOSOFT_DB_UPDATE_PROBLEM_TAG194.md`

**Root Cause:** Fehlerhafter Locosoft DB-Update-Prozess nach Server-Reboot (NICHT unser Code!)

## 🔍 Chronologie der Änderungen

### 1. Erste Fehler in Logs
- **05.01.2025 18:20** - Erste `UndefinedTable: Relation »times« existiert nicht` Fehler
- **16.01.2025 21:21** - Aktuelle Fehler (Spinner auf Werkstatt-Seiten)

### 2. Code-Änderungen (Git-Historie)

**Letzte Änderungen an `werkstatt_data.py`:**
- TAG 195: Code-Bereinigung (st_anteil_hybrid entfernt)
- TAG 185: Locosoft-kompatible Stempelzeit-Berechnung
- TAG 148: RealDictCursor Fix
- **Keine Änderungen an `FROM times` Queries!**

**Letzte Änderungen an `locosoft_mirror.py`:**
- TAG 146: TEK Refactoring
- **Keine Änderungen an `INCLUDE_VIEWS = ['times', 'employees']`!**

### 3. Datenbank-Status

**Aktuell:**
- ✅ `public.orders` - existiert
- ✅ `public.labours` - existiert
- ❌ `public.times` - **existiert NICHT**
- ✅ `private.times` - existiert (aber keine Berechtigung)

**Erkenntnis:**
- `times` existiert nur in `private` Schema
- Code sucht in `public` Schema (Standard)
- User `loco_auswertung_benutzer` hat keine Berechtigung für `private`

## 💡 Mögliche Ursachen

### Hypothese 1: VIEW wurde gelöscht
- **Früher:** `public.times` VIEW existierte (zeigte auf `private.times`)
- **Jetzt:** VIEW wurde gelöscht (unbeabsichtigt oder durch DB-Update)
- **Beweis:** Code hat schon immer `FROM times` verwendet → muss früher funktioniert haben

### Hypothese 2: Schema-Änderung in Locosoft-DB
- **Früher:** `times` war in `public` Schema
- **Jetzt:** `times` wurde nach `private` Schema verschoben
- **Beweis:** `times` existiert nur noch in `private`

### Hypothese 3: Berechtigungen geändert
- **Früher:** User hatte Zugriff auf `private.times` oder VIEW `public.times`
- **Jetzt:** Berechtigungen wurden entfernt
- **Beweis:** `private.times` existiert, aber Zugriff verweigert

### Hypothese 4: `locosoft_mirror.py` hat VIEW nie erstellt
- **Problem:** `locosoft_mirror.py` versucht `times` als VIEW zu spiegeln
- **Aber:** VIEW kann nicht gespiegelt werden, wenn es nicht existiert
- **Erkenntnis:** `INCLUDE_VIEWS = ['times']` existiert seit TAG 136 (PostgreSQL Migration)

## 🎯 Wahrscheinlichste Ursache

**Hypothese 1 + 2 kombiniert:**
1. Früher existierte ein VIEW `public.times` (zeigte auf `private.times`)
2. VIEW wurde gelöscht (durch Locosoft-DB-Update oder Wartung)
3. Code sucht weiterhin nach `public.times` → findet nichts
4. `private.times` existiert noch, aber User hat keine Berechtigung

## 📋 Was muss passiert sein?

**Vorher (funktionierte):**
```sql
-- In Locosoft-DB existierte:
CREATE VIEW public.times AS SELECT * FROM private.times;
```

**Jetzt (funktioniert nicht):**
- VIEW `public.times` existiert nicht mehr
- `private.times` existiert, aber keine Berechtigung

## 🔧 Lösung

**Option 1: VIEW wiederherstellen (EMPFOHLEN)**
- VIEW `public.times` in Locosoft-DB erstellen
- Benötigt: DB-Admin-Berechtigung

**Option 2: Code anpassen**
- `FROM times` → `FROM loco_times` (aus Portal-DB)
- Benötigt: Code-Änderungen

## ❓ Offene Fragen

1. **Wann wurde das VIEW gelöscht?** (zwischen TAG 136 und 05.01.2025?)
2. **Wer hat das VIEW gelöscht?** (Locosoft-Update? DB-Admin?)
3. **Kann das VIEW wiederhergestellt werden?** (DB-Admin-Berechtigung vorhanden?)

## 📊 Betroffene Features

- ❌ `/werkstatt/stempeluhr` - Spinner
- ❌ `/werkstatt/cockpit` - Spinner
- ❌ `/werkstatt/stempeluhr/monitor` - Spinner
- ❌ `/werkstatt/leistung` - KPI-Berechnung funktioniert nicht
- ❌ Celery Task: `benachrichtige_serviceberater_ueberschreitungen()` - Fehler

## ✅ Was funktioniert noch?

- ✅ Leerlauf-Stempelung-Erkennung (verwendet `orders`, nicht `times`)
- ✅ KPI-Berechnung (wenn `times` wieder verfügbar ist)
