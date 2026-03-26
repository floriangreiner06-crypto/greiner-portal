# TODO für Session-Start TAG 216

**Erstellt:** Session-Ende TAG 215 (2026-02-13)

---

## Offene Aufgaben (nicht zwingend Urlaubsplaner)

- Aus dem aktuellen Git-Status: Viele weitere geänderte Dateien (WhatsApp, Verkauf, Controlling, Navigation, etc.). Nur Urlaubsplaner-Vertretung/Resturlaub/Abwesenheitsgrenzen/Krankheit wurden in der letzten Session gezielt bearbeitet.
- Nächste Urlaubsplaner-Themen laut CONTEXT: Outlook-Kalender (bereits teilweise), E-Mails HR/MA, ggf. Urlaubsanspruch aus Mitarbeiterverwaltung.

---

## Nächste Schritte (optional)

1. **Locosoft prüfen:** Für Stefan Geier (und ggf. andere) sicherstellen, dass Krankheitstage in Locosoft als **Krn** geführt werden (nicht Url/BUr).
2. **Safeguard vereinheitlichen:** Die Logik „capped < resturlaub_view - 0.5 → nimm View“ könnte in eine Hilfsfunktion `_resturlaub_display_with_locosoft_cap(view_rest, anspruch, loco_urlaub)` ausgelagert werden (DRY).

---

## Qualitätsprobleme (optional zu beheben)

- Keine kritischen; siehe SESSION_WRAP_UP_TAG215.md (Code-Duplikat Safeguard optional auslagern).

---

## Wichtige Hinweise für die nächste Session

- **Server = Master:** Entwicklung auf `/opt/greiner-portal/`; Sync nur Backup.
- Nach Python-Änderungen: `sudo systemctl restart greiner-portal`; bei Celery-Task-Änderungen auch `celery-worker` und `celery-beat`.
- Urlaubsplaner-CONTEXT: `docs/workstreams/urlaubsplaner/CONTEXT.md`.
- Resturlaub/Krankheit: `docs/workstreams/urlaubsplaner/RESTURLAUB_KEINE_KRANKHEIT.md`.
