# TODO für Session-Start TAG 218

**Erstellt:** Session-Ende TAG 217  
**Nächste Session:** TAG 218

---

## 🎯 Priorität: E-Mail Reports unter Admin/Rechte nach neuen Standards

**Kontext:** Unter **Drive → Admin → Rechte** (Tab „E-Mail Reports“) sind alle konfigurierbaren E-Mail-Reports gelistet. Einige wurden bereits auf „neue Standards“ gebracht (TEK Gesamt, TEK Verkauf).

**Todo:** Übrige E-Mail-Reports prüfen und – wo fachlich sinnvoll – auf gleiche Standards bringen (Kernkennzahlen, Detailtabellen, PDF-Struktur).

**Relevante Stellen:** `reports/registry.py`, `scripts/send_daily_tek.py`, `api/pdf_generator.py`.

---

## Optionale Verbesserungen (TAG 217 Nachlauf)

### VFW Lohnsteuer – SSOT Standort
- In `scripts/vfw_lohnsteuer_2023_2024.py` steht ein lokales `STANDORT_NAMEN`-Dict.
- **Optional:** Import aus `api.standort_utils` (z. B. `from api.standort_utils import STANDORT_NAMEN`) für SSOT-Konformität.

### Aufräumen
- **docs/vfw_lohnsteuer_2023_2024.xml:** Falls nicht mehr benötigt (nutzer nutzen .xlsx), kann gelöscht oder in Archiv verschoben werden.
- **.venv:** Falls im Projekt genutzt, prüfen ob `.venv/` in `.gitignore` soll (aktuell nur `venv/`).

---

## Weitere offene Punkte (wie zuvor)

- E-Mail-Vorschlag Doppeldomain: Falls in DB (`users.username`) noch doppelte Domain, einmaliges UPDATE zur Bereinigung.
- Optional: `get_absatzwege_drill_down` / `get_modelle_drill_down` in `api/pdf_generator.py` als gemeinsame Hilfsfunktionen auslagern.

---

## Wichtige Hinweise

- **Session-Wrap-up dieser Session:** `docs/sessions/SESSION_WRAP_UP_TAG217.md`.
- **VFW-Listen:** Bei neuer Abfrage: `python3 scripts/vfw_lohnsteuer_2023_2024.py --csv docs/vfw_lohnsteuer_2023_2024.csv`, dann `vfw_liste_to_excel.py` und ggf. `vfw_liste_to_html.py` ausführen; danach ggf. erneut in Windows-Sync kopieren.
