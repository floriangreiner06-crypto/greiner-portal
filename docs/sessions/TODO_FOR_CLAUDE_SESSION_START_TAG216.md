# TODO für Session-Start TAG 216

**Nächste Session:** Nach TAG 215 (TEK E-Mail/PDF Detaillierung)

---

## Offene Aufgaben

### 1. E-Mail-Reports nach neuen Standards überarbeiten (Priorität)
- **Kontext:** Unter **Drive → Admin → Rechte** (http://drive/admin/rechte) gibt es „E-Mail Reports“. Einige Reports (TEK Gesamt, TEK Verkauf) wurden auf die neuen Standards umgestellt (detaillierte E-Mails + PDF mit Absatzwegen/Modell).
- **Todo:** Alle übrigen E-Mail-Reports, die dort konfiguriert sind, prüfen und – wo fachlich sinnvoll – auf die gleichen Standards bringen:
  - E-Mail-Inhalt detaillierter (Kernkennzahlen, Bereiche/Detailtabellen wo passend).
  - PDF mit allen Details (z. B. Absatzwege/Modell bei Verkaufsreports, konsistente Struktur).
- **Relevante Stellen:** `reports/registry.py`, `scripts/send_daily_tek.py` (send_*_reports, build_*_email_html), `api/pdf_generator.py` (generate_tek_*_pdf). Welche Report-Typen in der Admin-UI „E-Mail Reports“ angeboten werden, prüfen und Liste der noch nicht überarbeiteten Reports anlegen.

### 2. Optional: Code-Duplikat in pdf_generator reduzieren
- `get_absatzwege_drill_down` und `get_modelle_drill_down` sind in `generate_tek_daily_pdf()` und in `generate_tek_verkauf_pdf()` jeweils lokal definiert (gleiche Logik).
- Optional: Als gemeinsame Hilfsfunktionen auf Modul-Ebene in `api/pdf_generator.py` auslagern und von beiden PDF-Generatoren aufrufen.

---

## Nächste Schritte (Vorschlag)

1. In der Admin-Oberfläche (E-Mail Reports) alle Report-Typen erfassen.
2. Pro Report-Typ prüfen: E-Mail-Inhalt und PDF-Struktur im Vergleich zu TEK Gesamt/TEK Verkauf.
3. Priorisierte Liste: welche Reports als nächstes auf „neue Standards“ umgestellt werden sollen.
4. Optional: Refactor der Absatzwege/Modell-Helfer in pdf_generator.

---

## Wichtige Hinweise für die nächste Session

- TEK Gesamt: E-Mail hat Stück-Spalte (NW/GW) vor Erlös; PDF unverändert mit Absatzwegen/Modell.
- TEK Verkauf: E-Mail mit Kernkennzahlen + „Bereiche im Detail“; PDF mit Absatzwegen + Modell (NW/GW).
- Datenquelle E-Mail/PDF: `get_tek_data_from_api()` (tek_api_helper); Absatzwege/Modell im PDF via `/api/tek/detail` und `/api/tek/modelle` (localhost).
- Session-Wrap-up dieser Arbeit: **docs/sessions/SESSION_WRAP_UP_TAG215.md**.
