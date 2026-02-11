# SESSION WRAP UP - TAG 185

**Datum:** 2026-01-13  
**Session:** TAG 185  
**Fokus:** Analyse Locosoft Stempelzeiten-Berechnung und Leistungsgrad

---

## 📋 WAS WURDE ERLEDIGT

### 1. Analyse Stempelzeiten-Abweichung DRIVE vs. Locosoft

**Problem:**
- Abweichung bei Stempelzeiten zwischen DRIVE und Locosoft Original
- Jan's November KPIs zeigen unterschiedliche Werte

**Durchgeführte Analysen:**
- ✅ Dezember-Analyse (jan_dezember.pdf)
- ✅ November-Analyse (Jan's KPI Screenshot)
- ✅ Interne Aufträge Analyse (Kunde 3000001)
- ✅ Leerlauf-Aufträge Analyse (order_number = 31)
- ✅ Pausenzeiten-Analyse (Pause innerhalb Stempelung)
- ✅ Leistungsgrad-Berechnung Reverse Engineering

**Erkenntnisse:**
1. **Locosoft verwendet unterschiedliche Stempelzeiten:**
   - "Stmp.Anteil" (angezeigt): 8.483 Min = Zeit-Spanne (erste bis letzte, alle) - Lücken - Pausen
   - Leistungsgrad-Stempelzeit: 7.846 Min = Zeit-Spanne (erste alle bis letzte externe) - Lücken (10-60 Min, nur extern)

2. **Interne Aufträge werden anders behandelt:**
   - Interne Aufträge zählen zur ersten Stempelung (Zeit-Spanne)
   - Interne Aufträge zählen NICHT zur letzten Stempelung (nur externe)
   - Zeit-Spanne: Erste Stempelung (auch intern) bis letzte externe Stempelung

3. **Lücken-Berechnung für Leistungsgrad:**
   - Nur Lücken zwischen externen Stempelungen
   - Nur Lücken zwischen 10-60 Minuten
   - Lücken < 10 Min werden ignoriert (normale Wechselzeiten)
   - Lücken > 60 Min werden ignoriert (Pausen oder andere Gründe)

4. **Pausen werden NICHT für Leistungsgrad abgezogen:**
   - Pausen werden für "Stmp.Anteil" abgezogen
   - Pausen werden NICHT für Leistungsgrad abgezogen
   - Daher ist der Leistungsgrad in Locosoft höher (145,6% vs. DRIVE 140,8%)

### 2. Implementierung Locosoft-Stempelzeiten-Berechnung

**Geänderte Dateien:**
- `api/werkstatt_data.py`: Locosoft-kompatible Stempelzeit-Berechnung implementiert
  - Zeit-Spanne (erste bis letzte Stempelung pro Tag)
  - Minus Lücken zwischen Stempelungen
  - Minus konfigurierte Pausenzeiten (wenn innerhalb Zeit-Spanne)
- `utils/kpi_definitions.py`: Neue Funktion `berechne_stempelzeit_locosoft()` hinzugefügt

**Status:**
- ✅ "Stmp.Anteil" Berechnung implementiert
- ⚠️ Leistungsgrad-Stempelzeit noch nicht implementiert (andere Logik)

### 3. Dokumentation erstellt

**Neue Dokumente:**
1. `ANALYSE_STEMPELZEITEN_ABWEICHUNG_JAN_TAG185.md` - Dezember-Analyse
2. `ANALYSE_STEMPELZEITEN_NOVEMBER_JAN_TAG185.md` - November-Analyse
3. `ANALYSE_INTERNE_AUFTRAEGE_LOCOSOFT_TAG185.md` - Interne Aufträge Analyse
4. `ANALYSE_LEISTUNGSGRAD_LOCOSOFT_TAG185.md` - Leistungsgrad Reverse Engineering
5. `ZUSAMMENFASSUNG_LOCOSOFT_BEREchnung_TAG185.md` - Zusammenfassung aller Erkenntnisse
6. `IMPLEMENTIERUNG_LOCOSOFT_STEMPELZEITEN_TAG185.md` - Implementierungs-Dokumentation

**Alle Dokumente wurden ins Windows-Sync-Verzeichnis kopiert:**
- `/mnt/greiner-portal-sync/docs/`
- Für Serviceleiter zur Nachfrage bei Locosoft

---

## 📁 GEÄNDERTE DATEIEN

### Code-Änderungen:
- `api/werkstatt_data.py` (+145 Zeilen, -85 Zeilen)
  - Locosoft-kompatible Stempelzeit-Berechnung
  - Neue CTEs: `stempelungen_dedupliziert`, `tages_spannen`, `luecken_pro_tag`, `pausenzeiten_pro_tag`, `stempelzeit_locosoft`
  
- `utils/kpi_definitions.py` (+114 Zeilen)
  - Neue Funktion: `berechne_stempelzeit_locosoft()`
  - SSOT für Locosoft-Stempelzeit-Berechnung

### Weitere Änderungen (aus vorherigen Sessions):
- `api/arbeitskarte_api.py` (136 Zeilen geändert)
- `api/arbeitskarte_pdf.py` (37 Zeilen geändert)
- `api/garantie_auftraege_api.py` (124 Zeilen geändert)
- `api/garantieakte_workflow.py` (6 Zeilen geändert)
- `api/werkstatt_live_api.py` (18 Zeilen geändert)
- `celery_app/tasks.py` (95 Zeilen geändert)
- `templates/aftersales/garantie_auftraege_uebersicht.html` (393 Zeilen geändert)
- `utils/locosoft_helpers.py` (3 Zeilen geändert)

### Neue Dokumente:
- `docs/ANALYSE_STEMPELZEITEN_ABWEICHUNG_JAN_TAG185.md`
- `docs/ANALYSE_STEMPELZEITEN_NOVEMBER_JAN_TAG185.md`
- `docs/ANALYSE_INTERNE_AUFTRAEGE_LOCOSOFT_TAG185.md`
- `docs/ANALYSE_LEISTUNGSGRAD_LOCOSOFT_TAG185.md`
- `docs/ZUSAMMENFASSUNG_LOCOSOFT_BEREchnung_TAG185.md`
- `docs/IMPLEMENTIERUNG_LOCOSOFT_STEMPELZEITEN_TAG185.md`

---

## ✅ QUALITÄTSCHECK

### Redundanzen
- ✅ Keine doppelten Dateien gefunden
- ✅ Keine doppelten Funktionen (get_db nur in db_connection.py)
- ⚠️ STANDORT_MAPPING in mehreren Dateien (aber zentral in standort_utils.py)

### SSOT-Konformität
- ✅ `get_db()` wird korrekt aus `api.db_connection` importiert
- ✅ `locosoft_session()` wird korrekt verwendet
- ✅ KPI-Berechnungen in `utils/kpi_definitions.py` zentralisiert
- ✅ Neue Funktion `berechne_stempelzeit_locosoft()` in SSOT-Modul

### Code-Duplikate
- ✅ Keine kritischen Code-Duplikate
- ✅ SQL-CTEs modular aufgebaut (keine Duplikate)

### Konsistenz
- ✅ DB-Verbindungen: PostgreSQL-Syntax (`%s`, `true`, `CURRENT_DATE`)
- ✅ Imports: Zentrale Utilities werden korrekt importiert
- ✅ Error-Handling: Konsistentes Pattern

### Dokumentation
- ✅ Alle Analysen dokumentiert
- ✅ Implementierung dokumentiert
- ✅ Formeln und Logik dokumentiert

---

## ⚠️ BEKANNTE ISSUES

### 1. Leistungsgrad-Stempelzeit noch nicht implementiert
**Status:** ⚠️ Offen  
**Beschreibung:** 
- Locosoft verwendet für Leistungsgrad eine andere Stempelzeit-Berechnung
- Formel: Zeit-Spanne (erste alle bis letzte externe) - Lücken (10-60 Min, nur extern)
- Aktuell verwendet DRIVE die gleiche Stempelzeit für Anzeige und Leistungsgrad

**Impact:** 
- Leistungsgrad in DRIVE (140,8%) vs. Locosoft (145,6%) zeigt Differenz
- Serviceleiter fragt bei Locosoft nach (Dokumentation vorhanden)

### 2. Pausen innerhalb Stempelungen
**Status:** ⚠️ Unklar  
**Beschreibung:**
- Pausen können innerhalb von Stempelungen liegen (z.B. 12:00-12:44 innerhalb Stempelung 11:16-12:48)
- Unklar, ob Locosoft diese Pausen abzieht oder nicht

**Impact:** 
- Gering (nur bei speziellen Fällen)

---

## 🎯 ERREICHTE ZIELE

1. ✅ Locosoft Stempelzeit-Berechnung verstanden
2. ✅ "Stmp.Anteil" Berechnung implementiert
3. ✅ Leistungsgrad-Berechnung reverse-engineered
4. ✅ Umfassende Dokumentation erstellt
5. ✅ Alle Dokumente ins Windows-Sync kopiert

---

## 📊 STATISTIKEN

- **Geänderte Dateien:** 10
- **Neue Zeilen:** +986
- **Gelöschte Zeilen:** -85
- **Neue Dokumente:** 6
- **Analysen durchgeführt:** 6

---

*Erstellt: TAG 185 | Autor: Claude AI*
