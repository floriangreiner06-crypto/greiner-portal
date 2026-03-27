# TODO FOR CLAUDE SESSION START - TAG 184

## WICHTIG: Session-Start Checkliste

1. ✅ `CLAUDE.md` lesen (Projekt-Kontext)
2. ✅ `docs/sessions/SESSION_WRAP_UP_TAG183.md` lesen (vorherige Session)
3. ✅ `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG184.md` lesen (diese Datei)

## Offene Aufgaben

### 1. Landau BWA-Differenzen analysieren (HOCH)
- **Problem:** 
  - Betriebsergebnis: DRIVE -63.057,49 € vs. GlobalCube -82.219,00 € → Differenz: 19.161,51 €
  - Neutrales Ergebnis: DRIVE 0,00 € vs. GlobalCube -127,00 € → Differenz: 127,00 €
- **Status:** Analyse-Script erstellt (`scripts/systematische_landau_analyse.py`), HAR-Analyse noch nicht vollständig
- **Nächste Schritte:**
  1. HAR-Datei vollständig analysieren - alle Konten aus GlobalCube extrahieren
  2. Konten-Level-Vergleich: DRIVE-Konten vs. GlobalCube-Konten für jede Position
  3. Fehlende oder falsche Konten identifizieren
  4. Filter entsprechend korrigieren
- **Hinweis:** Systematisch vorgehen, nicht raten! Position für Position analysieren.

### 2. Gesamtsumme Indirekte Kosten prüfen (NIEDRIG)
- **Differenz:** 31,40 € (kleine Differenz, möglicherweise Rundungsfehler)
- **Status:** Nicht kritisch, sollte aber noch geprüft werden

### 3. Code-Refactoring: Variable Kosten-Filter (NIEDRIG)
- **Problem:** Variable Kosten-Filter-Logik ist in 3 Funktionen dupliziert:
  - `_berechne_bwa_werte`
  - `_berechne_bwa_ytd`
  - `get_bwa_v2`
- **Lösung:** In separate Funktion `_get_variable_kosten_filter(firma, standort)` auslagern
- **Vorteil:** Wartbarkeit, Konsistenz, weniger Code-Duplikate

## Wichtige Hinweise

### BWA-Filter-Logik
- **Deggendorf:**
  - Umsatz: `branch_number = 1`
  - Einsatz: `(6. Ziffer='1' OR (74xxxx AND branch=1)) AND branch != 3`
  - Variable Kosten: `6. Ziffer='1'` (NICHT `branch=1 AND 6. Ziffer='1'`, da es Variable Kosten mit branch=3 gibt!)
  - Direkte/Indirekte Kosten: `branch=1 AND 6. Ziffer='1'`
- **Landau:**
  - Umsatz: `branch_number = 3`
  - Einsatz: `branch_number = 3`
  - Variable/Direkte/Indirekte Kosten: `6. Ziffer='2' AND subsidiary=1`
- **Hyundai:**
  - Umsatz: `branch=2 AND subsidiary=2` (inkl. 89xxxx außer 8932xx)
  - Einsatz: `6. Ziffer='1' AND subsidiary=2`
  - Variable Kosten: `6. Ziffer='1' AND subsidiary=2` (OHNE 8910xx!)
- **Gesamtsumme:**
  - Kombination der drei Einzelbetriebe
  - Variable Kosten: 8910xx für Hyundai ausschließen

### Systematisches Vorgehen
- **WICHTIG:** Nicht raten, systematisch vorgehen!
- Position für Position analysieren
- Konten-Level-Vergleich durchführen
- Filter schrittweise korrigieren

## Dateien die geändert wurden (TAG 183)

- `api/controlling_api.py` - BWA-Filter-Korrekturen
- `scripts/systematische_landau_analyse.py` (NEU) - Analyse-Script

## Git Status

```bash
M api/controlling_api.py
M api/werkstatt_api.py
M api/werkstatt_data.py
M app.py
M celery_app/tasks.py
M templates/aftersales/werkstatt_uebersicht.html
M utils/__init__.py
M utils/kpi_definitions.py
?? docs/ANWESENHEITSGRAD_STEUERUNG_TAG181.md
?? docs/KPI_HELP_SYSTEM_TAG181.md
?? scripts/systematische_landau_analyse.py
?? static/js/kpi_help.js
```

**Hinweis:** Nicht alle geänderten Dateien sind BWA-relevant. Prüfe welche Dateien für BWA relevant sind.

## Server-Sync

Nach Git-Commit auf Windows:
- Server: `ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git pull"`
- Service-Restart: `sudo systemctl restart greiner-portal` (nur bei Python-Änderungen)
