# Analyse: Wiederkehrende Fehler bei der Resturlaubsberechnung

**Stand:** 2026-02-24  
**Ziel:** Strukturelle Ursachen verstehen, warum es immer wieder zu Abweichungen und Bugfixes bei Anspruch/Resturlaub kommt. Kein Coding – nur Analyse.

---

## 1. Beobachtete Fehler (Auswahl)

| Thema | Symptom | Ursache (kurz) |
|-------|---------|----------------|
| Krankheit mindert Rest | Resturlaub sank nach Krankheitseintrag | Locosoft führt teils Krankheit als Url/BUr; Formel nutzte nur „Anspruch − Locosoft-Urlaub“ |
| Gebuchter Urlaub nicht abgezogen | Rest blieb z. B. 28 trotz verplanter Tage | Rest nur aus Portal-View; Locosoft-Urlaub nicht oder fehlerhaft einbezogen |
| „Verfügbar: -5 Tage“ trotz 6 Rest | Liste zeigte Rest, Buchung lehnte ab | Validierung rechnete nur Anspruch − Locosoft; kein View-Fallback bei negativem Wert |
| Weihnachten/Silvester | 59 Anspruch → 58 in Locosoft, 59 im Drive | Halbe Tage 24.12./31.12. wurden nirgends abgezogen |
| Margit Loibl / Jennifer | Falscher Anspruch bzw. Rest trotz Verplanung | Anspruch in Portal (23) abweichend von Locosoft (27/28); Rest hängt an Locosoft-Anbindung |

---

## 2. Strukturelle Ursachen

### 2.1 Zwei Quellen, eine Kennzahl

- **Portal:** `vacation_entitlements` (Anspruch), `vacation_bookings` (Verbraucht/Geplant), View `v_vacation_balance_*` (Rest = Anspruch − Verbraucht − Geplant, nur Urlaub type_id=1).
- **Locosoft:** `absence_calendar` (Url, BUr, ZA, Krn, …) – führend für „was ist bereits gebucht/genommen“.

**Resturlaub** ist damit keine einzelne gespeicherte Größe, sondern wird abgeleitet aus:
- Portal-Anspruch (evtl. nach Abzügen),
- Portal-Verbrauch (nur Urlaub),
- Locosoft-Urlaub (Summe Url/BUr),
- plus Sonderregeln (Krankheit-Safeguard, Weihnachten/Silvester, negative Verfügbarkeit).

Sobald eine der Quellen fehlt, falsch ist oder anders interpretiert wird, weicht der Rest ab. Es gibt **keine einzige Stelle**, an der „der Resturlaub“ verbindlich berechnet und gespeichert wird.

### 2.2 Formel an vielen Stellen dupliziert

Die „Resturlaub-Logik“ (inkl. Abzug Weihnachten/Silvester, Locosoft-Cap, Safeguard) kommt an **mindestens** folgenden Stellen vor:

- **vacation_api.py:** `get_all_balances`, `get_my_balance`, `get_my_team`, `_get_available_rest_days_for_validation`
- **vacation_admin_api.py:** CSV-Export Urlaubsreport, Jahresend-Report (JSON + CSV)
- **vacation_chef_api.py:** Chef-Dashboard (liest Balance von vacation_api)

Jede neue Regel (z. B. Weihnachten/Silvester, Safeguard bei Krankheit) muss an **allen** diesen Stellen nachgezogen werden. Wird eine vergessen, entstehen Inkonsistenzen (z. B. Liste zeigt 58, Export zeigt 59; oder Anzeige stimmt, Validierung nicht).

### 2.3 View liefert nur „Rohwerte“

Die View berechnet:

- **Anspruch** = total_days + carried_over + added_manually − freie Tage (affects_entitlement)
- **Resturlaub** = Anspruch − verbraucht − geplant (nur Urlaub)

Sie kennt **nicht**:

- Abzug Weihnachten/Silvester (1 Tag),
- Locosoft-Urlaub,
- Safeguard „Krankheit in Locosoft nicht als Urlaub werten“.

Damit sind **Anspruch** und **Resturlaub** aus der View nirgends die endgültigen Anzeige- oder Validierungswerte. Sie werden in der API nachbearbeitet. Die „eigentliche“ Formel liegt in Python, nicht in der View – und dort mehrfach (siehe 2.2). Das macht es schwer, eine einzige, verbindliche Definition von „Anspruch“ und „Rest“ zu haben und Änderungen sicher zu machen.

### 2.4 Anspruch: Wer ist führend?

- **Locosoft:** Führend für Abwesenheiten (was genommen/geplant ist).
- **Portal:** `vacation_entitlements` ist führend für den **Jahresanspruch** – aber wird oft nicht aus Locosoft oder HR abgeglichen.

Fälle wie Margit Loibl (23 im Portal, 27/28 in Locosoft) zeigen: Es gibt **keinen automatischen Abgleich**. Wenn HR/Locosoft 27 pflegen und das Portal 23 hat, bleibt die Abweichung, bis jemand manuell in der Mitarbeiterverwaltung oder per Migration korrigiert. Fehlende SSOT für den Anspruch begünstigt solche Fehler.

### 2.5 Locosoft-Anbindung als Risiko

- Rest = min(View-Rest, Anspruch − Locosoft-Urlaub) (+ Safeguard).
- Wenn Locosoft nicht erreichbar ist, liefert die Abfrage 0 oder Fehler → Rest bleibt hoch (nur View).
- Wenn `employee_number` / `locosoft_id` falsch oder nicht gepflegt ist, wird kein Locosoft-Urlaub zugeordnet → Rest bleibt hoch.
- Wenn in Locosoft falsche Gründe genutzt werden (Krn als Url), sinkt der Rest ungewollt → Safeguard (0,5-Tage-Regel) mildert das, ist aber heuristisch.

Die Resturlaubsanzeige hängt also stabil von einer zweiten System- und Datenquelle ab; Fehler dort schlagen direkt auf die Kennzahl durch.

### 2.6 Validierung vs. Anzeige

Mehrfach trat auf: **Anzeige** (z. B. „6 Rest“) und **Buchungsvalidierung** („Verfügbar: -5 Tage“) nutzten unterschiedliche Berechnungen. Der Fix war, eine gemeinsame Hilfsfunktion `_get_available_rest_days_for_validation()` zu verwenden und überall dieselbe Logik wie in der Balance-Anzeige zu nutzen. Das zeigt: Sobald „verfügbarer Rest“ an zwei Stellen anders berechnet wird, entstehen für Nutzer unerklärliche Widersprüche.

---

## 3. Zusammenfassung: Warum es immer wieder Fehler gibt

1. **Keine einzige Definition von „Resturlaub“**  
   Rest ist eine abgeleitete Größe aus Portal + Locosoft + mehreren Sonderregeln, nirgends zentral gespeichert oder in einer einzigen Funktion berechnet.

2. **Formel an vielen Stellen dupliziert**  
   Jede neue Regel muss in mehreren Endpoints und Hilfsfunktionen nachgezogen werden; eine vergessene Stelle reicht für einen sichtbaren Bug.

3. **View ≠ Endwert**  
   Die View liefert nur Rohwerte; die „echte“ Logik (Abzüge, Locosoft, Safeguard) liegt in der API und ist mehrfach implementiert. Das erschwert ein klares Modell: „Eine Quelle der Wahrheit für Anspruch und Rest.“

4. **Zwei Systeme (Portal + Locosoft)**  
   Unterschiedliche Datenqualität, Verfügbarkeit und Codierung (Url vs. Krn etc.) führen zu Abweichungen; das System versucht das mit Fallbacks und Safeguards zu kitten, statt eine klare SSOT zu haben.

5. **Anspruch nicht konsistent gepflegt**  
   Wenn Portal-Anspruch und Locosoft/HR voneinander abweichen (z. B. 23 vs. 27), entstehen systematische Fehler bei Rest und Validierung; ohne Prozess für Abgleich bleiben solche Fälle erhalten.

6. **Regeln nacheinander ergänzt**  
   Jede neue Anforderung (Krankheit, Weihnachten, negative Verfügbarkeit, Locosoft-Fallback) wurde als Zusatz in bestehende Pfade eingebaut. Das erhöht die Komplexität und die Gefahr, dass bei der nächsten Änderung eine Stelle übersehen wird.

---

## 4. Mögliche Richtungen (ohne konkrete Umsetzung)

- **Eine Berechnungsfunktion:** Alle Anzeigen und die Validierung beziehen „Anspruch (effektiv)“ und „Resturlaub“ aus **einer** gemeinsamen Funktion (z. B. im Vacation-Service), die View + Locosoft + alle Abzüge/Safeguards kapselt. Keine Duplikation der Formel in mehreren Endpoints.
- **SSOT Anspruch:** Klar definieren, ob Anspruch aus Portal (Mitarbeiterverwaltung) oder aus Locosoft/Import kommt; Abgleich-Prozess oder technischer Sync, damit Abweichungen wie 23 vs. 27 nicht dauerhaft stehen bleiben.
- **View oder Service als „Single Calculator“:** Entweder die View so erweitern, dass sie alle Abzüge (inkl. Weihnachten/Silvester) enthält und Locosoft-Urlaub per Join/Funktion einbezieht – oder bewusst alles in einen zentralen Service legen und die View nur als Rohdatenquelle nutzen. Beides reduziert Duplikation.
- **Dokumentation der Formel:** Eine einzige, gepflegte Doku (z. B. in CONTEXT oder eigenes Doc), in der die **vollständige** Formel für Anspruch und Rest (inkl. aller Sonderfälle) steht. Hilft bei künftigen Änderungen und beim Testen.

Diese Analyse soll als Grundlage dienen, um bei der nächsten Runde (z. B. „Urlaubsanspruch aus Mitarbeiterverwaltung“, SSOT) die Architektur so anzupassen, dass Resturlaubsfehler seltener und leichter nachvollziehbar werden.
