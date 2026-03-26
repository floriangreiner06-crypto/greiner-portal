# Auswertung HAR-Dateien (Urlaubsplaner Workstream)

**Quelle:** HAR-Dateien und ggf. Mails/Bilder liegen im Windows-Sync unter  
`docs\workstreams\urlaubsplaner\` (Server: `/mnt/greiner-portal-sync/docs/workstreams/urlaubsplaner/`).

---

## Fehler Krankheitstage.har

**Inhalt (ausgelesen):**
- **POST /api/vacation/book-batch** mit `dates: ["2026-01-12","2026-01-13","2026-01-14"], vacation_type_id: 5` (Krankheit).
- **Response:** `"booking_ids":[0,0,0], "email_sent":true, "message":"3 Tag(e) beantragt", "success":true`
- **Problem:** `booking_ids` sind 0,0,0 – unter PostgreSQL liefert `cursor.lastrowid` nichts (nur bei SQLite). Die Buchungen wurden trotzdem angelegt (success true), aber die zurückgegebenen IDs waren falsch.
- **Fix (umgesetzt):** In `vacation_api.py` book-batch: Bei PostgreSQL wird `INSERT ... RETURNING id` verwendet und die ID aus `fetchone()` gelesen; die Response enthält dann die echten Buchungs-IDs.
- **my-balance (Vanessa):** In der HAR: anspruch 28, geplant 1.0, verbraucht 0, resturlaub 27 → rechnerisch korrekt (Krankheitstage mindern Rest nicht). Die E-Mail „genehmigter Urlaub gelöscht“ bei Typ-Änderung wurde separat behoben (keine HR-Storno-Mail bei Grund „Typ geändert“).

---

## Masseneingabe.har

- Datei sehr groß (>1 Mio Zeichen); für Details gezielt nach `/api/vacation/admin/mass-booking` und Response `skipped` suchen.
- Die API liefert inzwischen pro Überspring-Grund Zähler (`skipped.block`, `skipped.already_booked`, `skipped.substitute`, `skipped.max_absence`) und das Frontend zeigt sie in der Erfolgsmeldung an (z. B. „65 Buchungen erstellt. Übersprungen: 7 Vertretungsregel …“).

---

## Weitere HAR-Dateien im Ordner

- `Fehler Urlaubsantrag bereits gebucht.har`
- `drive_urlaub_bianca.har`

Bei Bedarf können diese separat ausgewertet werden.

---

## Mails mit Bildern

- Im gleichen Workstream-Ordner (Windows) können Mails/Bilder liegen; auf dem Server unter `/mnt/greiner-portal-sync/docs/workstreams/urlaubsplaner/` nach Bilddateien (z. B. .png, .jpg) oder Mail-HTML suchen. Bisher wurde nur `MOCKUP_Rechteverwaltung_Urlaub_Mitarbeiter.html` gefunden; weitere Anhänge ggf. in Unterordnern.
