# TODO für Session-Start TAG 217

**Erstellt:** Session-Ende TAG 216  
**Nächste Session:** TAG 217

---

## 🎯 Priorität: E-Mail Reports unter Admin/Rechte nach neuen Standards

**Kontext:** Unter **Drive → Admin → Rechte** (http://drive/admin/rechte) → Tab **„E-Mail Reports“** sind alle konfigurierbaren E-Mail-Reports gelistet. Einige wurden bereits auf „neue Standards“ gebracht (z. B. TEK Gesamt, TEK Verkauf: detaillierte E-Mails, PDF mit Absatzwegen/Modell).

**Todo:** Alle übrigen E-Mail-Reports, die dort erscheinen, prüfen und – wo fachlich sinnvoll – auf die gleichen Standards bringen:

- E-Mail-Inhalt: Kernkennzahlen, Bereiche/Detailtabellen wo passend.
- PDF: einheitliche Struktur, alle relevanten Details (z. B. Absatzwege/Modell bei Verkaufsreports).
- Konsistenz mit den bereits überarbeiteten Reports.

**Relevante Stellen:**

- **Report-Liste:** `reports/registry.py` (alle REPORT_REGISTRY-Einträge).
- **Versand/Inhalt:** `scripts/send_daily_tek.py` (send_*_reports, build_*_email_html), ggf. weitere Scripts je Report.
- **PDF:** `api/pdf_generator.py` (generate_tek_*_pdf, weitere generate_*).

**Vorgehen (Vorschlag):**

1. In der Admin-Oberfläche (E-Mail Reports) alle Report-Typen erfassen.
2. Pro Report-Typ prüfen: E-Mail-Inhalt und PDF-Struktur im Vergleich zu TEK Gesamt / TEK Verkauf.
3. Priorisierte Liste: welche Reports als nächstes auf „neue Standards“ umgestellt werden.
4. Schrittweise Umsetzung (ein Report nach dem anderen).

---

## Weitere offene Punkte

### E-Mail-Vorschlag Doppeldomain (falls noch sichtbar)
- API normalisiert bereits die **Ausgabe** (`_normalize_report_email`).
- Falls weiterhin doppelte Domain angezeigt wird: prüfen ob **users.username** in der DB doppelte Domain enthält; ggf. einmaliges UPDATE zur Bereinigung.

### Optional: Code-Duplikat in pdf_generator
- `get_absatzwege_drill_down` und `get_modelle_drill_down` in mehreren PDF-Generatoren – optional als gemeinsame Hilfsfunktionen in `api/pdf_generator.py` auslagern.

---

## Wichtige Hinweise

- **Alarm E-Mail:** Konfiguration unter E-Mail Reports („Alarm E-Mail Auftragsüberschreitung“); Empfänger wie bei anderen Reports verwaltbar. Migration für 1×/Tag-Tracking: `migrations/add_email_notifications_recipient_email_tag206.sql`.
- **Session-Wrap-up dieser Session:** `docs/sessions/SESSION_WRAP_UP_TAG216.md`.
