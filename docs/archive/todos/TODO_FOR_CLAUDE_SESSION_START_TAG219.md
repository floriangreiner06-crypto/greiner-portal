# TODO für Session-Start TAG 219

**Erstellt:** Session-Ende TAG 218  
**Nächste Session:** TAG 219

---

## 🎯 Priorität: E-Mail Reports unter Admin/Rechte (wie TAG 218)

**Kontext:** Unter **Drive → Admin → Rechte** (Tab „E-Mail Reports“) sind alle konfigurierbaren E-Mail-Reports gelistet. Einige wurden bereits auf „neue Standards“ gebracht (TEK Gesamt, TEK Verkauf).

**Todo:** Übrige E-Mail-Reports prüfen und – wo fachlich sinnvoll – auf gleiche Standards bringen (Kernkennzahlen, Detailtabellen, PDF-Struktur).

**Relevante Stellen:** `reports/registry.py`, `scripts/send_daily_tek.py`, `api/pdf_generator.py`.

---

## Optionale Verbesserungen (TAG 218 Nachlauf)

### VFW – SSOT Standort
- In `scripts/vfw_lohnsteuer_2023_2024.py` steht lokales `STANDORT_NAMEN`. Optional: Import aus `api.standort_utils` für SSOT-Konformität.

### ecoDMS
- Nach Passwort-Änderung in ecoDMS: `config/.env` auf Server anpassen (ECODMS_PASSWORD). Optional: UPE-Anreicherung aus Werksrechnungen (ecoDMS) für die 6 VFW ohne UPE prüfen (siehe `docs/VFW_UPE_ANREICHERUNG_ECODMS.md`).

### Aufräumen
- **docs/vfw_lohnsteuer_2023_2024.xml:** Falls nicht mehr benötigt, kann gelöscht oder archiviert werden.

---

## Weitere offene Punkte (wie zuvor)

- E-Mail-Vorschlag Doppeldomain: Falls in DB (`users.username`) noch doppelte Domain, einmaliges UPDATE zur Bereinigung.
- Optional: `get_absatzwege_drill_down` / `get_modelle_drill_down` in `api/pdf_generator.py` als gemeinsame Hilfsfunktionen auslagern.

---

## Wichtige Hinweise

- **Session-Wrap-up dieser Session:** `docs/sessions/SESSION_WRAP_UP_TAG218.md`.
- **VFW-Listen:** Bei neuer Abfrage: `python3 scripts/vfw_lohnsteuer_2023_2024.py --csv docs/vfw_lohnsteuer_2023_2024.csv`, dann `.venv/bin/python scripts/vfw_liste_to_excel.py`; danach ggf. `docs/` ins Sync kopieren (`rsync -av --delete /opt/greiner-portal/docs/ /mnt/greiner-portal-sync/docs/`).
- **Docs-Sync (nur docs):** `rsync -av --delete /opt/greiner-portal/docs/ /mnt/greiner-portal-sync/docs/` – damit Windows den aktuellen Docs-Stand hat.
