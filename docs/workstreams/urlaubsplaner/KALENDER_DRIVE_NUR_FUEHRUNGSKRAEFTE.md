# Kalender drive@ nur für Führungskräfte sichtbar

**Stand:** 2026-02

## Ziel

- **drive@ („Autohaus Greiner“):** Zeigt alle genehmigten Urlaube zentral – soll **nur für Führungskräfte** sichtbar sein (Übersicht aller Teams).
- **Mitarbeiter-Kalender:** Jeder genehmigte Urlaub wird zusätzlich im **persönlichen M365-Kalender** des Mitarbeiters angelegt → erscheint in der **Team-Ansicht** des Vorgesetzten („Team: [Name]“ in Outlook).

## Technik (DRIVE)

- **Graph-Berechtigung:** Die App benötigt die Anwendungsberechtigung **Calendars.ReadWrite** (oder äquivalent), damit Einträge in der Shared Mailbox und in **beliebigen Benutzerkalendern** (Mitarbeiter) erstellt/gelöscht werden können. In Azure AD: App-Registrierung → API-Berechtigungen → Microsoft Graph → Anwendungsberechtigungen.
- DRIVE schreibt bei Genehmigung in **zwei** Ziele:
  1. Shared Mailbox **drive@auto-greiner.de** (wie bisher).
  2. **Persönlicher Kalender** des Mitarbeiters (E-Mail aus `employees.email`) per Graph API.
- Storno: Beide Einträge werden gelöscht (Event-IDs werden in `vacation_bookings` gespeichert).

## Sichtbarkeit drive@: Konfiguration in M365/Exchange

Die Einschränkung **„drive@ nur für Führungskräfte“** wird **nicht** im DRIVE-Portal gesteuert, sondern in **Microsoft 365 / Exchange**:

- **Option A – Kalenderberechtigung:**  
  An der Shared Mailbox **drive@auto-greiner.de** nur für bestimmte Benutzer oder Gruppen (z. B. „Führungskräfte“) die Berechtigung **„Kalender – Lesen“** (oder „Reviewer“) vergeben. Alle anderen haben keine Berechtigung und sehen den Kalender nicht, wenn sie ihn hinzufügen wollen.

- **Option B – Verteilung/Group:**  
  Eine M365-Gruppe oder Verteiler „Führungskräfte“ anlegen und nur dieser Gruppe Zugriff auf den Kalender der Shared Mailbox geben (per Exchange Admin Center / PowerShell).

**Konkrete Schritte** (Beispiel Exchange Admin Center / M365 Admin):

1. **Microsoft 365 Admin Center** → Benutzer → **Shared postfächer** (oder Exchange Admin Center → Empfänger → Freigegebene Postfächer).
2. Postfach **drive@auto-greiner.de** auswählen → **Berechtigungen** (bzw. Kalenderberechtigung).
3. Nur Führungskräfte (einzeln oder über Gruppe) als „Kann lesen“ / „Reviewer“ eintragen; Standard-Berechtigung für andere entfernen oder nicht vergeben.

So bleibt der drive@-Kalender die zentrale Übersicht für Führungskräfte; normale Mitarbeiter sehen nur ihren eigenen Kalender (und ggf. Team-Ansicht ihres Vorgesetzten).

## Nachträgliches Befüllen der Event-IDs (Backfill)

Für **bestehende** genehmigte Buchungen (vor Einführung der doppelten Kalender-Einträge) sind `calendar_event_id_drive` und `calendar_event_id_employee` zunächst leer. Storno nutzt dann den Fallback (Suche nach Datum/Inhalt) für drive@; der Mitarbeiter-Kalender-Eintrag kann ohne ID nicht gelöscht werden.

**Nachträgliches Befüllen:** Das Skript `scripts/backfill_vacation_calendar_event_ids.py` sucht in drive@ und im Mitarbeiter-Kalender nach Events am Buchungsdatum mit „via DRIVE“ im Body und passendem Betreff und schreibt die gefundenen Graph-Event-IDs in `vacation_bookings`. Danach funktioniert die Storno-Löschung auch für diese Buchungen.

```bash
cd /opt/greiner-portal
# Trockenlauf (keine DB-Änderungen)
python3 scripts/backfill_vacation_calendar_event_ids.py --dry-run
# Ausführen
python3 scripts/backfill_vacation_calendar_event_ids.py
# Nur Buchungen ab Datum
python3 scripts/backfill_vacation_calendar_event_ids.py --ab=2026-01-01
```

## Graph-Kalender testen

Zum Prüfen von Token, Kalenderliste drive@ und optional Anlegen/Löschen eines Test-Events:

```bash
cd /opt/greiner-portal
python3 scripts/test_graph_calendar.py
python3 scripts/test_graph_calendar.py --create-delete
python3 scripts/test_graph_calendar.py --user florian.greiner@auto-greiner.de --create-delete
```

## Referenzen

- `api/vacation_calendar_service.py` – Schreiben in drive@ und Mitarbeiter-Kalender, `find_vacation_events_on_date` für Backfill
- `scripts/test_graph_calendar.py` – Graph-Kalender-Funktionalität testen
- `scripts/backfill_vacation_calendar_event_ids.py` – Backfill Event-IDs
- `docs/workstreams/urlaubsplaner/CONTEXT.md` – Outlook-Kalender
- `docs/workstreams/urlaubsplaner/OUTLOOK_TEAMKALENDER_VS_DRIVE.md` – Team-Ansicht vs. drive@
