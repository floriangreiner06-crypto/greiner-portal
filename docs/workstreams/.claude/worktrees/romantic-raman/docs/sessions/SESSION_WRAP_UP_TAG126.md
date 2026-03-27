# SESSION WRAP-UP TAG 126
**Datum:** 2025-12-18
**Fokus:** Werkstatt Live-Board Gantt, Feierabend-Erkennung, Verwaiste Stempelungen

---

## ERLEDIGTE AUFGABEN

### 1. Feierabend-Erkennung (NEU)
**Problem:** Patrick wurde als "Pausiert" angezeigt, obwohl er bereits ausgestempelt hatte (16:39)

**Lösung:**
- Neue Kategorie `feierabend_mechaniker` in Stempeluhr-API
- Type 1 mit `end_time` = Mitarbeiter hat Feierabend
- `pausiert`-Query filtert jetzt Feierabend-MA aus
- Grüne "Feierabend"-Karte in allen Stempeluhr-Templates
- Grüner "Feierabend"-Footer in beiden Liveboard-Ansichten

**Betroffene Dateien:**
- `api/werkstatt_live_api.py` (Zeile 1042-1049, 1124-1192, 1280-1300)
- `templates/aftersales/werkstatt_stempeluhr.html`
- `templates/aftersales/werkstatt_stempeluhr_monitor.html`
- `templates/aftersales/werkstatt_liveboard.html`
- `templates/aftersales/werkstatt_liveboard_gantt.html`

---

### 2. Verwaiste Stempelungen Fix
**Problem:** Tobias zeigte 6+ Stunden auf REG-CH 113, obwohl er längst andere Aufträge bearbeitet hatte

**Ursache:** "Verwaiste" offene Stempelungen - Position 1 nie geschlossen, aber danach andere Aufträge beendet

**Lösung:**
- Verwaiste Stempelungen bekommen jetzt ein virtuelles `ende_ts` (= Start der nächsten Stempelung)
- `ist_aktiv = false` UND `ende_ts` wird gesetzt
- Neues Flag `ist_verwaist = true` für UI-Kennzeichnung

**Betroffene Dateien:**
- `api/werkstatt_live_api.py` (Zeile 4927-4954)

---

### 3. Pausiert-Anzeige korrigiert
**Problem:** Bei "Pausiert" wurde "(6h)" angezeigt - das war die Gesamtarbeitszeit, nicht "seit wann pausiert"

**Lösung:**
- Monitor-Template zeigt jetzt "seit HH:MM" statt Gesamtarbeitszeit

**Betroffene Dateien:**
- `templates/aftersales/werkstatt_stempeluhr_monitor.html` (Zeile 226-236)

---

### 4. Werkstatt LIVE Dashboard - Aktive Mechaniker
**Problem:** Patrick wurde als "Aktiver Mechaniker" angezeigt, obwohl er Feierabend hatte

**Lösung:**
- Dashboard-API filtert MA mit Feierabend aus der "Aktive Mechaniker" Liste
- Neues Feld `heute_gestempelt` für UI-Warnung
- MA die heute nicht gestempelt haben werden halbtransparent + Warnsymbol angezeigt

**Betroffene Dateien:**
- `api/werkstatt_live_api.py` (Zeile 679-717, 757-765)
- `templates/aftersales/werkstatt_live.html` (Zeile 435-465)

---

### 5. Kiosk-Scripts erstellt
**Dateien:**
- `scripts/kiosk/Liveboard_Monitor_Deggendorf.bat` (Gantt-Ansicht)
- `scripts/kiosk/Liveboard_Monitor_Deggendorf_Karten.bat` (Karten-Ansicht)
- `scripts/kiosk/README.md` (Dokumentation)

**Features:**
- Chrome Kiosk-Modus (Vollbild, keine Leisten)
- Token-Authentifizierung (Greiner2024Werkstatt!)
- Betrieb=deg Filter (Deggendorf + Hyundai)

---

### 6. Monitor-Routes in app.py
**Neue Routes:**
- `/monitor/liveboard` - Karten-Ansicht ohne Login (Token-Auth)
- `/monitor/liveboard/gantt` - Gantt-Ansicht ohne Login (Token-Auth)

**Betroffene Dateien:**
- `app.py` (Zeile 589-622)

---

## TECHNISCHE DETAILS

### Feierabend-Erkennung SQL
```sql
-- Type 1 mit end_time = Mitarbeiter ist gegangen
SELECT employee_number, MAX(end_time) as gegangen_um
FROM times
WHERE type = 1
  AND DATE(start_time) = CURRENT_DATE
  AND end_time IS NOT NULL
GROUP BY employee_number
```

### Verwaiste Stempelungen Logic
```python
# Finde nächste abgeschlossene Stempelung nach offener
for s in stempelungen:
    if s['ist_aktiv']:
        naechste = next(
            (a for a in abgeschlossene_sorted if a['_start_time'] > s['_start_time']),
            None
        )
        if naechste:
            s['ist_aktiv'] = False
            s['ende_ts'] = naechste['_start_time'].isoformat()
            s['ist_verwaist'] = True
```

---

## OFFENE PUNKTE / TESTS

1. **Tobias Pausiert-Anzeige** - Erst morgen testbar (heute bereits Feierabend)
   - Sollte zeigen: "Reitmeier seit 16:24" statt "(6h)"

2. **Verwaiste Stempelungen im Gantt** - Visuell prüfen ob Balken korrekt enden

---

## SYNC-BEFEHLE (bereits ausgeführt)

```bash
sudo cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/
sudo cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_live.html /opt/greiner-portal/templates/aftersales/
sudo cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_liveboard*.html /opt/greiner-portal/templates/aftersales/
sudo cp /mnt/greiner-portal-sync/templates/aftersales/werkstatt_stempeluhr*.html /opt/greiner-portal/templates/aftersales/
sudo systemctl restart greiner-portal
```

---

*TAG 126 abgeschlossen - 2025-12-18*
