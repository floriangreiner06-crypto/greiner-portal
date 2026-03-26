# Stand: Leerer Start – warum die Fehler, was ist gefixt

**Workflow (wie beschrieben):** MA trägt in DRIVE ein → E-Mail an Genehmiger → Genehmigung/Ablehnung in DRIVE → bei Genehmigung E-Mail an HR → HR trägt in Locosoft ein (keine Rückwirkung auf DRIVE) → Vanessa führt mit allen durch, Eintrag in leeres Modul.

---

## Warum so viele Abweichungen?

Der Urlaubsplaner ist **historisch mit zwei Quellen** gewachsen:

1. **DRIVE** (vacation_bookings, vacation_entitlements, View) für Anträge, Genehmigung, Anspruch.
2. **Locosoft** (absence_calendar) wurde zusätzlich genutzt für: Resturlaub-Kappe, Kalender-Anzeige, Banner „Urlaub/ZA/Krank“.

„Leerer Start“ und „nur DRIVE“ bedeuten aber: **eine Quelle**. Jede Stelle, die noch Locosoft einlas oder anzeigte, führte zu Abweichungen (leer in DB vs. voll im Kalender, Banner mit Locosoft-Werten usw.).

---

## Was wurde angepasst (ohne Workflow zu ändern)

| Thema | Ursache | Fix |
|-------|---------|-----|
| Rest 26 statt erwartet | Locosoft-Kappe in der Berechnung | Berechnung nur aus View (DRIVE), Locosoft raus (bereits vorher). |
| Kalender „voll“ trotz leerer DB | `/all-bookings` lud Locosoft-Tage für die Anzeige | Locosoft-Zuschaltung in all-bookings deaktiviert → Kalender nur aus DRIVE. |
| Banner „Urlaub/ZA/Krank“ | my-balance lieferte Locosoft-Werte, Frontend zeigte sie zuerst | my-balance: kein Locosoft-Abruf mehr; Frontend: „Urlaub“ = verbraucht (DRIVE). |
| **Rest 27 → 26 nach Buchung (Vanessa)** | Nach Buchung: Optimistic Update zeigte 27, dann Reload rief loadMe/loadAllEmployees auf; dabei wurde `_lastVacationBooking` noch gesetzt und die „Korrektur“ (Rest − gebuchte Tage) ein zweites Mal angewendet. Server lieferte bereits 27 → 27−1 = 26. | `_lastVacationBooking` wird **vor** dem Reload (loadAllEmployees/loadMe) gelöscht, damit die API-Werte unverändert angezeigt werden. |

**Workflow unverändert:** Antrag → Genehmiger → Genehmigung/Ablehnung in DRIVE → E-Mail an HR → HR trägt in Locosoft. E-Mails „Bitte in Locosoft eintragen“ bleiben.

---

## Weitere Stellen (keine Bugs für den Workflow)

- **get_my_bookings:** Setzt pro Buchung `in_locosoft` (Anzeige „in Locosoft“). Optional, kein Einfluss auf Rest oder Kalender-Füllstand.
- **Admin-Reporte / vacation_admin_api:** Nutzt teils Locosoft für Übersichten. Eigenes Feature, kein Teil des MA-Genehmigungs-Workflows.
- **Validierung (verfügbare Tage):** Nutzt nur View (DRIVE), kein Locosoft mehr.

---

## Kurzfassung

- Die Abweichungen kamen von der **Mischung DRIVE + Locosoft** an mehreren Stellen (Rest, Kalender, Banner).
- Diese Stellen sind auf **nur DRIVE** umgestellt (Rest, Kalender-Anzeige, Banner „Urlaub“).
- Der von dir beschriebene Workflow (Eintrag in DRIVE, Genehmigung in DRIVE, HR in Locosoft) ist im Code nicht verändert und sollte ohne weitere Bugs laufen.

Nach Portal-Neustart und hartem Reload (Strg+F5) sollten Kalender und Banner konsistent leer bzw. DRIVE-only sein.
