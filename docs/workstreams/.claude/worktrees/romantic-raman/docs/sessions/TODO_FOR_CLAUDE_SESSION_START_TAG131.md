# TODO für Claude - Session Start TAG 131

**Erstellt:** 2025-12-20

---

## Priorität 1: Anwesenheitsreport Finetuning

User zeigt Report am Montag den Serviceleitern. Mögliche Anpassungen:
- Sortierung (Name, Zeit, Betrieb)
- Filter "nur Probleme" (Type 1 vergessen)
- Export (Excel/PDF)
- Schwellwerte (Karenzzeit etc.)

**URL:** `/werkstatt/anwesenheit`
**API:** `/api/werkstatt/live/anwesenheit?datum=YYYY-MM-DD`

---

## Priorität 2: Sites weiter konsolidieren

Routen-Inventur erstellt in TAG 130. Noch offen:
- Legacy-Route `/werkstatt/uebersicht` entfernen oder redirecten?
- Navigation in `base.html` aufräumen
- Feature-Matrix erstellen (wer nutzt was)

**Doku:** `docs/ROUTEN_INVENTUR_TAG130.md`

---

## Priorität 3: Testumgebung Wartungsplan

Zurückgestellt. Web-UI unter `/test/wartungsplan` für Team-Validierung.

---

## Kontext TAG 130

- Routen-Inventur durchgeführt, 9 Duplikate bereinigt
- Anwesenheitsreport reaktiviert mit Type 2 Logik
- Type 1 (Anwesenheit) wird zusätzlich angezeigt für historische Daten
- SOAP kann Stempelzeiten nicht live lesen (kein readWorkTimes)
