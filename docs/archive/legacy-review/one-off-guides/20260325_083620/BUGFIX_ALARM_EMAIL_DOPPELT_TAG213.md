# Bugfix: Alarm-E-Mail doppelt/dreifach (TAG 213)

**Datum:** 2026-02-12  
**Problem:** Matthias und Florian erhalten dieselben Alarm-E-Mails („Auftrag überschreitet Vorgabe“) mehrfach – z. B. 09:45 und 10:00 für denselben Auftrag.

---

## Kontext Entwicklungsstand Alarm-E-Mail

- **TAG 171:** Serviceberater-Benachrichtigung per E-Mail bei Zeitüberschreitung; Task alle 15 Min (Mo–Fr, 7–18 Uhr).
- **TAG 182:** Doppelte Mails (u. a. Christian Meyer >80 Mails) → Task deaktiviert, Analyse, Fixes: Tracking-Tabelle `email_notifications_sent`, Empfänger-Deduplizierung, Fallback nur Matthias König. Task reaktiviert.
- **TAG 185:** Matthias König (3007) erhält immer alle Überschreitungs-E-Mails (Quality-Check).
- **TAG 192/193/194:** Logik für aktive vs. abgeschlossene Aufträge, 30-Min-Mindestlaufzeit, nur heute_session_min für aktive.
- **TAG 206:** Report-Subscriber (Admin → E-Mail Reports) für `alarm_auftrag_ueberschreitung`, Spalte `recipient_email` in `email_notifications_sent`.

Trotz „max. 1 E-Mail pro Auftrag/Empfänger/Tag“ (SELECT vor SEND, INSERT nach SEND) traten weiterhin Doppel-/Dreifach-E-Mails auf.

---

## Ursache: Race-Condition

Zwei (oder mehr) Task-Läufe können **gleichzeitig** oder in kurzem Abstand laufen (z. B. 09:45 und 10:00):

1. **Lauf 1 (09:45):** SELECT → „noch nicht gesendet“ → E-Mail senden → INSERT.
2. **Lauf 2 (10:00):** SELECT (evtl. bevor Lauf 1 committed) → „noch nicht gesendet“ → E-Mail senden → INSERT.

Wenn beide die SELECT-Prüfung bestehen, bevor einer den INSERT committed, werden zwei E-Mails für denselben Auftrag/Empfänger/Tag versendet.

---

## Lösung (TAG 213): „INSERT first“

- **Vorher:** SELECT → bei „nicht gesendet“ in Liste → SEND → INSERT.
- **Nachher:** Für jeden Empfänger **zuerst** INSERT in `email_notifications_sent`. Nur wenn der INSERT **erfolgt** (kein UNIQUE-Konflikt), wird der Empfänger in `empfaenger_zu_senden` aufgenommen und erhält die E-Mail. Bei UNIQUE-Verletzung (pgcode 23505) → „bereits heute gesendet“ → überspringen.

Damit ist die **Datenbank** (UNIQUE-Constraint/Index) die einzige Quelle der Wahrheit; nur ein Lauf kann pro (Auftrag, Empfänger, Tag) den Eintrag anlegen und damit senden.

**Datei:** `celery_app/tasks.py`, Task `benachrichtige_serviceberater_ueberschreitungen`.

---

## Kurzfassung

| Vorher | Nachher |
|--------|--------|
| SELECT → SEND → INSERT | INSERT → bei Erfolg SEND |
| Race möglich | Atomar: nur wer INSERT schafft, sendet |

**Status:** ✅ Implementiert. Nach Deployment: Celery Worker (und ggf. Beat) neu starten.
