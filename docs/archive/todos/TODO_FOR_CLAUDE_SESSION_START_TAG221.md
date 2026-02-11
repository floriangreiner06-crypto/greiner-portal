# TODO für Session-Start TAG 221

**Erstellt:** Session-Ende TAG 220  
**Nächste Session:** TAG 221

---

## Session-Start lesen

1. `CLAUDE.md`
2. `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG221.md` (diese Datei)
3. `docs/sessions/SESSION_WRAP_UP_TAG220.md`

---

## Offene / optionale Punkte (aus TAG 220)

### TEK-PDF
- **Web-Download:** Falls TEK „Gesamt“-PDF im Browser über einen anderen Endpunkt/Client erzeugt wird (nicht über send_daily_tek), prüfen ob Werkstatt-KPIs dort ebenfalls ankommen (Datenquelle und Schlüssel `bereich`/`id`).

### Vorherige TODOs (TAG 219)
- E-Mail-Reports unter Admin/Rechte: Übrige Reports auf gleiche Standards prüfen (`reports/registry.py`, `scripts/send_daily_tek.py`, `api/pdf_generator.py`).
- Optional: VFW `STANDORT_NAMEN` in `scripts/vfw_lohnsteuer_2023_2024.py` durch SSOT aus `api.standort_utils` ersetzen.
- Optional: `get_absatzwege_drill_down` / `get_modelle_drill_down` in `api/pdf_generator.py` als gemeinsame Hilfsfunktionen auslagern.

---

## Wichtige Hinweise

- **TEK-PDF:** Nach Python-Änderungen an API/Routes/Scripts: `sudo systemctl restart greiner-portal` auf Server; Script-Pfad (send_daily_tek) nutzt beim nächsten Lauf die geänderten Dateien.
- **Sync:** Bei Bearbeitung im Windows-Sync: Dateien nach Server syncen, dann ggf. Restart (siehe CLAUDE.md).
- **Server-Git:** Am Session-Ende: `ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG220 - TEK PDF Werkstatt-KPIs, Detail Werkstatt/Teile'"`
- **Qualitätscheck-Template:** `docs/QUALITAETSCHECK_TEMPLATE.md` (falls vorhanden).
