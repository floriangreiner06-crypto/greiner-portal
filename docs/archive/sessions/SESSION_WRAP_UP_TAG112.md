# SESSION WRAP-UP TAG 112
**Datum:** 2025-12-10
**Dauer:** Ganztägige Session
**Fokus:** Werkstatt Dashboard V2 + Stempeluhr Bugfixes + neue Features

---

## 📋 ÜBERSICHT ALLER ÄNDERUNGEN

### Teil 1: Werkstatt Dashboard V2 (aus compacted Session)
- ✅ 3 Gauges: Leistungsgrad, Produktivität, Effizienz
- ✅ Entgangener Umsatz Card
- ✅ Problemfälle Endpoint mit Filter-API
- ✅ Trend API mit Bayern-Feiertage Filter
- ✅ Trend Chart vereinfacht auf 2 Linien (Stempelzeit + AW)
- ✅ Anwesenheit in Labels statt eigener Linie
- ✅ Dokumentation: WERKSTATT_LEISTUNG_DOKU_TAG112.md
- ✅ Git: Branch `feature/tag112-onwards` erstellt

### Teil 2: Stempeluhr Bugfixes & Features (diese Session)
- ✅ Saldo-Bug Fix (kumulierte Zeit statt nur aktuelle Session)
- ✅ DISTINCT Fix (Duplikate in times-View)
- ✅ Python-Überschreibung gefixt (SQL-Saldo verwenden)
- ✅ auftrags_art (W/G/T/-) aus Locosoft
- ✅ ist_pausenzeit Flag für Mittagspause
- ✅ Pausen-Banner in beiden Templates
- ✅ Chrome Kiosk Script für Monitor
- ✅ Neue Kategorie "Pausiert / Wartet"

---

## 🐛 BUGFIX 1: Saldo-Berechnung in Stempeluhr

### Problem
Stempeluhr LIVE zeigte nur die aktuelle Session-Zeit, nicht die kumulierte Zeit (Saldo).

**Beispiel Auftrag 38946 (Dederer, Andreas):**
- MA 5004 arbeitete 10:37-11:42 = 65 min (beendet)
- MA 5004 startete neu 11:43 (aktuelle Session)
- **Anzeige:** 16 min ❌
- **Erwartet:** 81 min (65 + 16) ✅

### Ursache
1. SQL-Query berechnete nur: `NOW() - start_time`
2. Fehlte: `SUM(duration_minutes)` für abgeschlossene Sessions
3. Python überschrieb SQL-Wert mit `berechne_netto_laufzeit()`

### Lösung
SQL-Subquery addiert abgeschlossene Sessions:
```sql
EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 
+ COALESCE((
    SELECT SUM(dur) FROM (
        SELECT DISTINCT ON (start_time, end_time) duration_minutes as dur
        FROM times t2 
        WHERE t2.order_number = t.order_number 
          AND t2.employee_number = t.employee_number
          AND t2.end_time IS NOT NULL
          AND t2.type = 2
    ) dedup
), 0) as laufzeit_min
```

Python verwendet jetzt SQL-Wert:
```python
'laufzeit_min': int(r['laufzeit_min'] or 0),  # TAG 112: SQL-Saldo verwenden
```

### Betroffene Stellen
| Zeile | Stelle | Änderung |
|-------|--------|----------|
| ~697 | Stempeluhr produktiv CTE | Saldo-Subquery |
| ~908 | Response laufzeit_min | SQL-Wert statt berechne_netto_laufzeit() |
| ~912 | Response fortschritt_prozent | SQL-Wert verwenden |
| ~979 | Stempelung ohne Vorgabe CTE | Saldo-Subquery |
| ~2795 | Auftrags-API aktiv CTE | Saldo-Subquery |

---

## 🐛 BUGFIX 2: Duplikate in times-View

### Problem
Nach Saldo-Fix zeigten Mechaniker viel zu hohe Zeiten (z.B. 482 min statt 176 min).

### Ursache
Die `times`-View in Locosoft liefert Duplikate - gleiche Stempelung erscheint 6-7x!
```
Auftrag 38946:
  2025-12-10 10:37:13 -> beendet (65 min)
  2025-12-10 10:37:13 -> beendet (65 min)  ← Duplikat!
  2025-12-10 10:37:13 -> beendet (65 min)  ← Duplikat!
  ... (6x insgesamt)
```

### Lösung
`DISTINCT ON (start_time, end_time)` in der Subquery verhindert mehrfaches Zählen.

---

## ✨ FEATURE 1: Auftragsart (W/G/T)

### Quelle
`labours.labour_type` in Locosoft

### Werte
| Code | Bedeutung |
|------|-----------|
| W | Werkstatt |
| G | Garantie |
| T | Teile |
| - | Keine Position zugewiesen |

### Implementierung
1. **API:** LATERAL JOIN erweitert um `MAX(labour_type) as auftrags_art`
2. **Response:** `'auftrags_art': r.get('auftrags_art') or '-'`
3. **Frontend:** Vor Auftragsnummer: `<strong>${m.auftrags_art || "-"}</strong>`

### Anzeige
- `werkstatt_stempeluhr.html` - Zeile 485
- `werkstatt_stempeluhr_monitor.html` - Zeile 253

---

## ✨ FEATURE 2: Pausenzeit-Flag

### Zweck
Frontend kann Mittagspause 12:00-13:00 erkennen und Banner anzeigen.

### API
```python
ist_pausenzeit = PAUSE_START <= jetzt_zeit <= PAUSE_ENDE  # TAG 112
```

Response:
```json
{
  "ist_arbeitszeit": true,
  "ist_pausenzeit": false
}
```

### Frontend
Orangener Banner in beiden Templates:
```html
<div id="pausenBanner" style="display: none; background: linear-gradient(135deg, #f5af19, #f12711);">
    🍽️ MITTAGSPAUSE (12:00 - 13:00) - Stempelzeiten werden fortgesetzt
</div>
```

JavaScript zeigt/versteckt basierend auf `data.ist_pausenzeit`.

---

## ✨ FEATURE 3: Kategorie "Pausiert / Wartet"

### Problem
MA Reitmeier drückte "Pause" auf Auftrag 38600 und verschwand komplett:
- ❌ Nicht in "Aktiv" (keine offene Stempelung)
- ❌ Nicht in "Leerlauf" (kein Auftrag 31 gestempelt)
- ❌ Nicht in "Abwesend" (nicht im absence_calendar)
- = **Unsichtbar!**

### Analyse Locosoft-Verhalten
Wenn MA "Pause" drückt:
1. Aktuelle Stempelung wird beendet (`end_time` gesetzt)
2. KEIN automatischer Leerlauf (Auftrag 31) wird gestartet
3. MA hat keine offene Stempelung mehr

### Erkenntnis: Anwesenheitserfassung
- `type=1` = Anwesenheit (nur Werkstattmeister Scheingraber nutzt das)
- `type=2` = Produktive Arbeit (alle anderen Mechaniker)
- Mechaniker haben KEINE type=1 Stempelung
- Ihre Arbeitszeit = Summe aller type=2 Stempelungen

### Lösung: Neue Kategorie
Query findet MA die:
1. Heute produktiv gearbeitet haben (type=2, order>31)
2. Aktuell KEINE offene Stempelung haben
3. Nicht abwesend sind (nicht im absence_calendar)

### API-Response
```json
{
  "pausiert_mechaniker": [
    {
      "employee_number": 5007,
      "name": "Reitmeier,Tobias",
      "betrieb": 1,
      "betrieb_name": "Deggendorf",
      "letzter_auftrag": 38600,
      "pausiert_seit": "14:37",
      "heute_min": 381,
      "heute_auftraege": 6,
      "status": "pausiert"
    }
  ],
  "summary": {
    "produktiv": 5,
    "leerlauf": 1,
    "pausiert": 1,    // NEU
    "abwesend": 3,
    "gesamt": 10      // Jetzt inkl. pausiert
  }
}
```

---

## 🖥️ Chrome Kiosk Script

### Datei
`scripts/Stempeluhr_Monitor_Deggendorf.bat`

### URL
```
http://10.80.80.20/werkstatt/stempeluhr/monitor?token=Greiner2024Werkstatt!&subsidiary=1,2
```

### Features
- Vollbild (Kiosk-Modus)
- Token-Auth (kein Login erforderlich)
- Deggendorf-Filter (subsidiary=1,2)
- Beenden mit Alt+F4

### Token-Auth
Bereits implementiert in `app.py` (Zeile 512):
```python
MONITOR_TOKEN = 'Greiner2024Werkstatt!'
```

---

## 📁 GEÄNDERTE DATEIEN

### API
| Datei | Änderungen |
|-------|------------|
| `api/werkstatt_api.py` | Trend-Chart, Problemfälle-API |
| `api/werkstatt_live_api.py` | Saldo-Fix, DISTINCT, auftrags_art, ist_pausenzeit, pausiert_mechaniker |

### Templates
| Datei | Änderungen |
|-------|------------|
| `templates/aftersales/werkstatt_uebersicht.html` | Dashboard V2, Trend-Chart |
| `templates/aftersales/werkstatt_stempeluhr.html` | auftrags_art, Pausen-Banner |
| `templates/aftersales/werkstatt_stempeluhr_monitor.html` | auftrags_art, Pausen-Banner |

### Dokumentation
| Datei | Status |
|-------|--------|
| `docs/WERKSTATT_LEISTUNG_DOKU_TAG112.md` | NEU |
| `docs/SESSION_WRAP_UP_TAG112.md` | NEU |

### Scripts
| Datei | Status |
|-------|--------|
| `scripts/Stempeluhr_Monitor_Deggendorf.bat` | NEU |

---

## 🔍 LOCOSOFT-ERKENNTNISSE

### times-View Duplikate
- View liefert gleiche Stempelung 6-7x
- **Lösung:** DISTINCT ON (start_time, end_time) in allen Aggregationen

### Auftragsarten
- Kommen aus `labours.labour_type`
- W=Werkstatt, G=Garantie, T=Teile

### Auftrag 31 = Leerlauf
- Spezielle Auftragsnummer für "keine Arbeit"
- Wird NICHT automatisch bei Pause gestartet

### Betriebsstruktur
| ID | Name | Besonderheit |
|----|------|--------------|
| 1 | Deggendorf (Stellantis) | Hauptstandort |
| 2 | Hyundai DEG | Keine eigenen MA - Stellantis-MA arbeiten dort |
| 3 | Landau | Eigene MA |

---

## ✅ TESTS DURCHGEFÜHRT

- [x] Saldo-Berechnung korrekt (Dederer: 176 min statt 26 min)
- [x] Duplikate eliminiert durch DISTINCT
- [x] auftrags_art wird angezeigt (W/G/-)
- [x] ist_pausenzeit Flag im Response
- [x] Pausen-Banner in beiden Templates
- [x] Pausiert-Kategorie funktioniert (Hoffmann erschien korrekt)
- [x] Monitor-Script mit Token funktioniert
- [x] subsidiary=1,2 Filter funktioniert

---

## ⏭️ NÄCHSTE SCHRITTE (Optional)

1. **Frontend:** Pausiert-Kategorie im Stempeluhr-Template anzeigen
2. **Frontend:** Pausiert im Monitor anzeigen (eigene Kachel/Box)
3. **Alarm:** Bei langer Pause (>30 min ohne Aktivität) warnen?

---

## 📊 TAG 112 MARKER IM CODE
```
werkstatt_live_api.py:
  Zeile 697:  -- TAG 112: Aktuelle Session + bereits abgeschlossene Zeit
  Zeile 741:  MAX(labour_type) as auftrags_art  -- TAG 112
  Zeile 830:  ist_pausenzeit = ... # TAG 112: Mittagspause
  Zeile 875:  # 4. PAUSIERT / WARTET - TAG 112
  Zeile 978:  'ist_pausenzeit': ist_pausenzeit,  # TAG 112
  Zeile 1002: 'laufzeit_min': ... # TAG 112: SQL-Saldo verwenden
  Zeile 1005: 'auftrags_art': ... # TAG 112: W=Werkstatt
  Zeile 1036: # TAG 112: Neue Kategorie für Mechaniker
  Zeile 1093: -- TAG 112: Saldo = aktuelle Session + abgeschlossene Zeiten
  Zeile 2909: -- TAG 112: Saldo (Auftrags-API)
```

---

**Session abgeschlossen:** 2025-12-10 15:45
**Branch:** feature/tag112-onwards
**Bereit für:** Git Commit

---

## 🖥️ FRONTEND: Pausiert-Kategorie (Nachtrag)

### Implementierung
Beide Stempeluhr-Templates wurden um die neue Kategorie "Pausiert / Wartet" erweitert.

### werkstatt_stempeluhr.html
- **Summary Cards:** Neue lila Kachel "Pausiert / Wartet" mit Zähler
- **Neue Section:** Card mit Header + Container für pausierte MA
- **renderData():** countPausiert + badgePausiert aktualisieren
- **renderPausiert():** Neue Funktion für Pausiert-Anzeige
  - Name, Betrieb, Pausiert-seit
  - Heute-Zeit (Stunden/Minuten)
  - Anzahl Aufträge heute
  - Letzter Auftrag

### werkstatt_stempeluhr_monitor.html
- **Stats Row:** Neue lila Kachel zwischen Leerlauf und Abwesend
- **pausiertNamen:** Badges mit Namen und Arbeitszeit
- **renderData():** countPausiert + pausiertNamen aktualisieren

### Styling
- Lila Gradient: `linear-gradient(135deg, #667eea, #764ba2)`
- Konsistent mit Pause-Thematik

---

## ✅ FINAL STATUS TAG 112

| Feature | API | Frontend | Getestet |
|---------|-----|----------|----------|
| Saldo-Bug Fix | ✅ | ✅ | ✅ |
| DISTINCT Duplikate | ✅ | - | ✅ |
| auftrags_art (W/G/T) | ✅ | ✅ | ✅ |
| ist_pausenzeit | ✅ | ✅ | ✅ |
| Pausen-Banner | ✅ | ✅ | ✅ |
| Pausiert-Kategorie | ✅ | ✅ | ✅ |

**Alle Features komplett implementiert und getestet!**

---

**Session abgeschlossen:** 2025-12-10 15:45
**Letzter Test:** produktiv=6, pausiert=1, leerlauf=0

---

## ⚠️ KNOWN ISSUE: Pausiert-Logik

### Problem
Die aktuelle Pausiert-Erkennung zeigt auch MA die:
- Ihren Arbeitstag beendet haben (Feierabend)
- Früh angefangen und lange nicht mehr gestempelt haben

**Screenshot:** Raith (7h), Hoffmann (3h), Ebner (6h) - das sind keine echten Pausen!

### Ursache
Logik unterscheidet nicht zwischen:
- ✅ Echte Pause (kurze Unterbrechung, z.B. 30 min)
- ❌ Feierabend (Tag beendet)

### TODO für spätere Session
1. Zeitfenster prüfen (z.B. letzte Stempelung > 2h = Feierabend?)
2. Locosoft-Anwesenheit (type=1) besser nutzen?
3. Schicht-/Arbeitszeit-Logik einbauen?
4. Oder: In Locosoft anders/besser stempeln

### Aktueller Status
Feature funktioniert technisch, aber Datenqualität erfordert Überarbeitung.
