# Bugfix: „Nicht genügend Resturlaub“ trotz angezeigter Resttage (Buchhaltung)

**Datum:** 2026-02  
**Betroffen:** Buchung/Eintrag von Urlaub durch Buchhaltung (und andere); tritt mehrfach auf, wenn Locosoft mehr Urlaubstage meldet als Portal-Anspruch.

---

## Symptom

- In der **Mitarbeiterliste** werden z. B. **6 Tage Rest** angezeigt.
- Beim **Buchen** (einzelner Tag oder Bereich) erscheint: **„Nicht genug Resturlaub! Verfügbar: -5,0 Tage, angefragt: X Tag(e)“**.
- Betroffen u. a.: Bianca Greindl, Silvia (bereits früher).

---

## Ursache

- **Anzeige (Balance-API):**  
  Resturlaub = `min(View-Resturlaub, max(0, Anspruch − Locosoft-Urlaub))` plus Fallback. Die Anzeige wird also nach unten begrenzt und nutzt ggf. View/Fallback → z. B. **6** sichtbar.

- **Buchungsvalidierung:**  
  Es wurde nur gerechnet: **Verfügbar = Anspruch − Locosoft-Urlaub − Portal-Pending**.  
  Wenn Locosoft **mehr** Urlaubstage meldet als der Portal-Anspruch (z. B. 17 bei Anspruch 12), wird **Verfügbar negativ** (z. B. **-5**). Die Validierung lehnt dann ab, obwohl die Liste noch Rest anzeigt.

- **Hintergrund:**  
  Locosoft-Daten (z. B. `absence_calendar`, Aggregation) können von der Portal-Logik abweichen (andere Stichtage, Übertrag, Doppelzählung). Dadurch kommt es immer wieder zu „Anzeige zeigt Rest, Buchung sagt nicht genug“.

---

## Lösung (Fix)

In **`api/vacation_api.py`** an **beiden** Stellen der Resturlaub-Prüfung (Einzelbuchung + Batch `book-batch`):

- **Wenn** aus Locosoft ein **negativer** verfügbarer Rest entsteht (**available_days < 0**):
  - **Fallback:** Resturlaub aus der **View** `v_vacation_balance_{Jahr}` lesen.
  - **available_days** = dieser View-Wert, mindestens 0.
- Damit gilt: **Die Buchungsvalidierung verwendet dieselbe logische Quelle wie die Anzeige** (View-Resturlaub), wenn Locosoft zu einem negativen Wert führt.

**Code-Stellen:**

1. **Einzelbuchung** (Route um `POST /api/vacation/book`): nach `available_days = round(anspruch - urlaub_locosoft - portal_pending, 1)` → wenn `available_days < 0` → View abfragen, `available_days` aus View setzen (≥ 0).
2. **Batch-Buchung** (Route um `POST /api/vacation/book-batch`): gleiche Logik nach der Berechnung von `available_days`.

---

## Regeln für künftige Änderungen

- **Resturlaub-Anzeige** und **Resturlaub-Validierung bei Buchung** müssen **sachlich zusammenpassen**: Was in der Liste als „Rest“ angezeigt wird, muss für die Buchung als verfügbar gelten (bis auf die tatsächlich angefragten Tage).
- Wenn **Locosoft** genutzt wird: Bei **negativem** „Verfügbar“ (Anspruch − Locosoft − Portal) **immer** auf View-Resturlaub (oder dieselbe Logik wie in der Balance-API) zurückfallen, damit keine „-5,0 Tage“-Meldung bei sichtbarem Rest entsteht.

---

## Referenz

- **CONTEXT.md:** Abschnitt „Bugfix: Resturlaub-Validierung bei negativem Locosoft-Wert“.
- **Datei:** `api/vacation_api.py` (Suche nach „Buchhaltung-Fix“ bzw. `available_days < 0`).
