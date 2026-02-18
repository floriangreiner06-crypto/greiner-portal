# Verifizierung: Urlaubsanspruch in Locosoft

**Datum:** 2026-02-13  
**Frage:** Steht der Urlaubsanspruch (inkl. ggf. übertragene Ansprüche) in Locosoft? Kann DRIVE ihn von dort lesen?

---

## Ergebnis der Prüfung

### In der Locosoft-PostgreSQL-Datenbank **nicht** vorhanden

- **Jahresurlaubsanspruch (J.Url.ges.)** und **Übertrag** werden in Locosoft **nicht** in einer Tabelle oder View gespeichert.
- Die Locosoft-**Anwendung** berechnet J.Url.ges. (z. B. „Standard + Resturlaub Vorjahr“) zur Laufzeit; diese Berechnung ist in der **Datenbank nicht** als Feld abgelegt.

### Geprüfte Objekte (Auszug)

| Objekt | Inhalt / Ergebnis |
|--------|-------------------|
| **Tabellen** | Keine Tabelle mit Namen wie „urlaub“, „anspruch“, „entitlement“. Relevante Tabelle: `absence_calendar` (nur **gebuchte** Tage, kein Anspruch). |
| **employees_history** / View **employees** | Spalten: u. a. name, employment_date, schedule_index, productivity_factor. **Kein** Feld für Urlaubstage oder Jahresanspruch. |
| **configuration** / **configuration_numeric** | Keine Einträge, die Urlaubsanspruch oder Übertrag pro MA/Jahr enthalten (nur betriebliche Konfiguration). |
| **absence_calendar** | Enthält nur **gebuchte** Abwesenheitstage (employee_number, date, reason, day_contingent). Daraus lässt sich **Verbrauch** pro Jahr berechnen, **nicht** der Anspruch. |
| **absence_reasons** | Nur Kennungen (Url, BUr, Krn, …) und Beschreibung; kein Anspruch. |

### Was in Locosoft **vorhanden** ist

- **Verbrauchte Urlaubstage** pro Mitarbeiter und Jahr: über `absence_calendar` (reason IN ('Url','BUr')), inkl. `day_contingent` für halbe Tage.
- **Kein** Feld für:
  - Jahresurlaubsanspruch (J.Url.ges.),
  - Übertrag aus Vorjahr,
  - individueller Soll-Anspruch (z. B. 12 Tage Teilzeit).

---

## Konsequenz für DRIVE

1. **Anspruch (inkl. Übertrag)** kann **nicht** direkt aus der Locosoft-DB gelesen werden. Er muss entweder:
   - in **DRIVE** gepflegt werden (`vacation_entitlements`: total_days, carried_over, added_manually), oder
   - per **Export aus der Locosoft-Anwendung** (z. B. J.Url.ges. pro MA/Jahr) nach DRIVE übernommen werden.
2. **Verbrauch** kann aus Locosoft genutzt werden: DRIVE macht das bereits (Balance-Anzeige: min(Resturlaub, Anspruch − Locosoft-Urlaub); Kalender: Locosoft-Tage werden angezeigt).

---

## Referenz

- Berechnungslogik Locosoft (laut Projekt): `docs/sessions/URLAUBSPLANER_ANSPRUECHE_LOCOSOFT_IMPORT_TAG167.md`  
  „J.Url.ges. = Standard-Anspruch + Resturlaub aus Vorjahr“ – berechnet in der Anwendung, nicht in der DB.
- Import-Script (berechnet Anspruch aus Vorjahr + Standard): `scripts/setup/import_vacation_entitlements_2026_from_locosoft.py`  
  Verwendet Portal-Vorjahr + Locosoft-Verbrauch für Resturlaub; **Standard-Anspruch** ist dabei fest (z. B. 27), kein Lesen aus Locosoft.

---

**Fazit:** Der Urlaubsanspruch (und Übertrag) steht **nicht** in Locosoft-PostgreSQL; er muss in DRIVE gepflegt oder aus der Locosoft-Anwendung exportiert werden. Die Prüfung wurde per Abfragen gegen die Locosoft-DB (Tabellen/Views/Spalten, configuration, absence_*) durchgeführt.
