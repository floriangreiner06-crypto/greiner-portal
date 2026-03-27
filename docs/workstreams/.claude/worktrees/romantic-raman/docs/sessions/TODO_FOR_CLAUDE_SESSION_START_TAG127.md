# TODO FOR CLAUDE - SESSION START TAG 127

## ZU TESTEN (aus TAG 126)

### 1. Tobias Pausiert-Anzeige
- Stempeluhr Monitor prüfen
- Sollte zeigen: **"Reitmeier seit HH:MM"** (nicht mehr "(6h)")
- Template-Fix wurde deployed, aber erst morgen testbar

### 2. Verwaiste Stempelungen im Gantt-Liveboard
- Prüfen ob Balken bei verwaisten Stempelungen korrekt enden
- Tobias' REG-CH 113 sollte als Block 09:48-10:43 erscheinen (nicht bis "jetzt")

### 3. Feierabend-Anzeige
- Grüner Footer in Liveboard (Karten + Gantt)
- Grüne Karte in Stempeluhr
- MA mit Feierabend sollten dort erscheinen mit Geh-Uhrzeit

---

## KONTEXT TAG 126

### Neue Features implementiert:
1. **Feierabend-Erkennung** - Type 1 mit end_time = gegangen
2. **Verwaiste Stempelungen** - Offene Stempelungen mit späteren abgeschlossenen
3. **Kiosk-Scripts** - Liveboard für Monitor-Betrieb

### Wichtige Code-Stellen:
- `api/werkstatt_live_api.py:1042-1049` - Feierabend CTE
- `api/werkstatt_live_api.py:4927-4954` - Verwaiste Stempelungen Fix
- `api/werkstatt_live_api.py:1124-1192` - Feierabend Query

### Monitor-URLs:
- `/monitor/liveboard?token=Greiner2024Werkstatt!&betrieb=deg` (Karten)
- `/monitor/liveboard/gantt?token=Greiner2024Werkstatt!&betrieb=deg` (Gantt)

---

## BEKANNTE ISSUES

- Keine offenen Bugs bekannt

---

*Erstellt: 2025-12-18*
