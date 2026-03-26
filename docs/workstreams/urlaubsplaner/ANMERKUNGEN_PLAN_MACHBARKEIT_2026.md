# Urlaubsplaner – Neue Anmerkungen: Plan & Machbarkeit

**Stand:** 2026-03-11  
**Quelle:** User-Test-Anmerkungen (neueste)

**Umsetzung 2026-03-11:** Alle Punkte 1–8 wurden umgesetzt (Jahre bis 2030, HR-Empfänger, Zeitstempel-Hover, Samstagsdienst, Genehmiger für Team, Batch-HR-Mail, Arbeitstage Teilzeit, Hinweis Urlaubssperre).

---

## 1. Urlaubssperre: Bereits geplanter Urlaub nicht betroffen

**Anmerkung:** Wenn Admin eine Urlaubssperre einträgt, soll bereits geplanter Urlaub von Mitarbeitern davon **nicht betroffen** sein.

**Ist-Zustand:**  
- Beim Anlegen einer Sperre (`vacation_blocks`) werden **keine** bestehenden Buchungen geändert oder gelöscht.  
- Sperren wirken nur bei **neuen** Buchungen (Einzelbuchung, Buch-Batch, Masseneingabe): An gesperrten Tagen wird die Buchung abgelehnt.  
- Bereits genehmigter/geplanter Urlaub bleibt also unberührt.

**Bewertung:** **Bereits so umgesetzt.**  
**Empfehlung:** Optional einen kurzen Hinweis in der Admin-UI beim Anlegen einer Sperre ergänzen (z. B. „Bereits gebuchter Urlaub bleibt bestehen; die Sperre gilt nur für neue Anträge.“). Kein zwingender Code-Change nötig.

---

## 2. Neue Kategorie „Samstagsdienst“ (VKL für Verkäufer)

**Anmerkung:** VKL wünscht eine neue Kategorie „Samstagsdienst“. Damit sollen Samstage markiert werden, an denen ein Verkäufer **nicht** im Haus ist. Reine Info-Funktion – **keine** Auswirkung auf Arbeitszeit oder Urlaubskonto.

**Machbarkeit:** **Ja.**

| Schritt | Beschreibung |
|--------|--------------|
| 1 | Neuen Urlaubstyp in `vacation_types` anlegen (z. B. „Samstagsdienst“ / „Nicht im Haus (Sa)“). |
| 2 | In der Balance-View und allen Berechnungen (Anspruch, Rest, Verbraucht) diesen Typ **ausschließen** (wie z. B. Krankheit bei Resturlaub). |
| 3 | Im Kalender/Planer anzeigen (eigene Farbe/Icon), nur zur Information. |
| 4 | Keine E-Mails an HR/Locosoft für diesen Typ (reine Info). |

**Aufwand:** Klein (Migration + Anzeige + Ausschluss aus Kennzahlen).

---

## 3. Urlaubstage/Sperren für 2027 nicht übernommen/angezeigt – bis 2030 erweitern

**Anmerkung:** Urlaubstage bzw. Urlaubssperren für 2027 werden nicht übernommen bzw. angezeigt. Bitte bis 2030 erweitern.

**Ist-Zustand:**  
- Backend: `ALLOWED_YEARS = range(2020, 2031)` in `api/vacation_api.py` – Jahre 2027–2030 sind **bereits** erlaubt.  
- Views `v_vacation_balance_{year}` werden on-demand erzeugt (`ensure_vacation_year_setup_simple(year)`), wenn z. B. Balance oder Buchungen für ein Jahr abgefragt werden.  
- Frontend: Jahr-Dropdown in `urlaubsplaner_v2.html` ist aktuell `currentYear - 2` bis `currentYear + 3` (z. B. 2024–2029 bei Jahr 2026). **2030 fehlt** in der Auswahl.

**Maßnahmen:**  
1. **Frontend:** Jahr-Auswahl bis mindestens **2030** erweitern (z. B. `currentYear + 4` oder fest 2020–2030).  
2. **Prüfen:** Beim ersten Aufruf für 2027/2028/2029/2030 die View- und Entitlement-Erstellung (evtl. Fehlermeldung oder fehlende Anzeige loggen und beheben).  
3. **Sperren:** `vacation_blocks` und `blocks-and-free-days` sind jahresunabhängig (EXTRACT(YEAR FROM block_date)); für 2027+ werden sie angezeigt, sobald das Jahr im Frontend wählbar ist und die API mit `year=2027` aufgerufen wird.

**Aufwand:** Gering (Dropdown + ggf. eine Prüfung der View-Erstellung für 2027–2030).

---

## 4. Abteilungsleiter/Genehmiger: Urlaub, Schulung etc. für Teammitglieder eintragen

**Anmerkung:** Abteilungsleiter/Genehmiger sollen die Berechtigung haben, Urlaub, Schulung usw. für **alle Teammitglieder** selbst eintragen zu können.

**Ist-Zustand:**  
- „Buchung für anderen“ (target_employee_id / booking_for_other) ist heute im Wesentlichen **Admin** vorbehalten (z. B. Krankheit, ZA, direkte Buchung).  
- Genehmiger können Anträge genehmigen/ablehnen, aber keine Abwesenheiten **im Namen** von Teammitgliedern anlegen.

**Machbarkeit:** **Ja.**

| Schritt | Beschreibung |
|--------|--------------|
| 1 | In `api/vacation_api.py` (Einzelbuchung `/book` und ggf. Buch-Batch): Prüfung erweitern: Neben Admin darf auch ein **Genehmiger** für ein Teammitglied buchen, wenn dieses Teammitglied zu seinem Team gehört (`get_team_for_approver`). |
| 2 | Rechte: Für Genehmiger nur erlauben: Urlaub (1), Schulung (9), ggf. Sonderurlaub/Arzttermin – **nicht** Krankheit (5) oder Zeitausgleich (6), sofern weiterhin nur Admin. |
| 3 | Frontend: Auswahl „Für Mitarbeiter buchen“ bzw. Mitarbeiter-Dropdown für Genehmiger sichtbar machen, beschränkt auf Teammitglieder. |

**Aufwand:** Mittel (Backend-Rechtelogik + Frontend-Anpassung).

---

## 5. E-Mail an Dennis, Katrina und Jennifer geht nicht raus bei Genehmigung – für alle prüfen

**Anmerkung:** E-Mail an Dennis, Katrina und Jennifer geht bei Genehmigung nicht raus; bitte für alle prüfen.

**Klarstellung:** Dennis, Katrina und Jennifer sind **die genehmigten Mitarbeiter** (nicht HR). Sie sollen die **Genehmigungs-Benachrichtigung** („Dein Urlaub wurde genehmigt“) erhalten, wenn ihr Vorgesetzter genehmigt.

**Umsetzung 2026-03:**  
- **E-Mail-Fallback:** Wenn `employees.email` leer ist, wird die E-Mail aus der Tabelle **users** (via `ldap_employee_mapping`) geholt, damit alle eingeloggten Mitarbeiter die Genehmigungs-Mail erhalten.  
- Bitte trotzdem in der **Mitarbeiterverwaltung** (oder AD) die E-Mail-Adresse der Mitarbeiter pflegen; Fallback greift nur, wenn der User sich schon mal eingeloggt hat (Eintrag in `users`).

---

## 6. Arbeitstage von Teilzeitkräften (Arbeitszeitmodell in Personalakte)

**Anmerkung:** Arbeitstage von Teilzeitkräften eintragen (Arbeitszeitmodell in Personalakte), z. B. 4 von 5 Werktagen oder Halbtage; am besten Klickfelder für Wochentage und Halbe im Arbeitszeitmodell.

**Ist-Zustand:**  
- Tabelle `employee_working_time_models`: enthält u. a. `hours_per_week`, `working_days_per_week` – **keine** Aufschlüsselung, **welche** Wochentage und ob halbe Tage.  
- Doku: `FREIE_TAGE_ARBEITSZEITMODELL_VORSCHLAG.md` beschreibt bereits Vorschläge für „Freie Tage“ (welche Wochentage frei).

**Machbarkeit:** **Ja.**

| Schritt | Beschreibung |
|--------|--------------|
| 1 | Schema: In `employee_working_time_models` optionale Spalten ergänzen, z. B. `work_weekdays` (ARRAY oder JSON: Mo–So, 0/1 oder Mo–So + „half“ pro Tag). Alternativ eigene Tabelle „Arbeitstage pro Wochentag“ (employee_id, weekday, half_day). |
| 2 | Personalakte/Arbeitszeitmodell-UI: Klickfelder für Mo–So (Arbeitstag ja/nein) und pro Tag optional „halber Tag“. Speichern über bestehende API (employee_management_api) erweitern. |
| 3 | Urlaubsplaner: Optional – Anzeige „arbeitet nicht“ an diesen Tagen (z. B. ausgegraut), sofern gewünscht; Resturlaub/Anspruch kann bei Bedarf später daran geknüpft werden (nicht zwingend für erste Version). |

**Aufwand:** Mittel (Migration + Backend + Frontend Personalakte).

---

## 7. Zeitstempel Beantragung/Genehmigung (Hover)

**Anmerkung:** Zeitstempel der Beantragung (wer zuerst beantragt hat) anzeigen, evtl. Hover: „Beantragt am …“, „Genehmigt am …“.

**Ist-Zustand:**  
- `vacation_bookings` hat `created_at` und `approved_at` (laut Schema und Code).  
- API liefert `created_at` bereits in einigen Endpoints (z. B. all-bookings, my-bookings).  
- `approved_at` wird beim Genehmigen gesetzt und kann in den gleichen Endpoints mit ausgeliefert werden.

**Maßnahmen:**  
1. Sicherstellen, dass alle relevanten Buchungs-Abfragen für die Kalender-/Listenanzeige `created_at` und `approved_at` zurückgeben.  
2. Frontend: Beim Hover (oder Klick) über eine Buchungszelle Tooltip/Title anzeigen: z. B. „Beantragt am 01.03.2026, 14:30“ und „Genehmigt am 02.03.2026, 09:15“ (falls genehmigt).

**Aufwand:** Gering.

---

## 8. E-Mail an HR bei Genehmigung: Zeitraum pro Mail statt pro Tag

**Anmerkung:** Umstellung der Genehmigungs-E-Mail an HR – zu viele Mails. Besser: **Ein Zeitraum in einer Mail** statt pro Tag. Weniger zum Löschen, angenehmer für HR. Zuerst Plan und Machbarkeit prüfen und erklären.

**Ist-Zustand:**  
- Bei Genehmigung wird aktuell **pro genehmigtem Tag** einmal `send_approval_email_to_hr(booking_details, approver_name)` aufgerufen (ein Aufruf pro `booking_id`).  
- Werden z. B. 5 Tage nacheinander genehmigt (oder im Batch), entstehen 5 separate E-Mails an HR.

**Ziel:**  
- **Eine E-Mail pro Genehmigungsvorgang** (z. B. „Urlaub genehmigt: Max Mustermann, 10.03.2026 – 14.03.2026“) mit einer **Tabelle** aller betroffenen Tage (Datum, Art, Umfang, ggf. Halbtag) statt 5 Einzelmails.

**Machbarkeit:** **Ja.**

| Option | Beschreibung | Aufwand |
|--------|--------------|---------|
| **A** | **Batch-Genehmigung erweitern:** Neuer Endpoint `POST /api/vacation/approve-batch` mit `{ booking_ids: [1,2,3,4,5] }`. Backend genehmigt alle Buchungen in einer Transaktion, ruft **einmal** eine neue Funktion `send_approval_email_to_hr_batch(bookings_details_list, approver_name)` auf, die eine E-Mail mit einer Tabelle (Zeitraum + alle Tage) versendet. Frontend: Bei Mehrfachauswahl „Genehmigen“ diesen Endpoint nutzen statt mehrfach `/approve`. | Mittel |
| **B** | **„Zeitraum-E-Mail“ bei Einzelgenehmigung:** Wenn der Nutzer einen Tag genehmigt, prüfen ob es weitere **pending** Buchungen derselben Person mit aufeinanderfolgenden Tagen gibt; wenn ja, alle in einer Mail zusammenfassen. Deutlich aufwendiger und fachlich fragil (welche Tage „dazuzählen“?). | Hoch, nicht empfohlen |
| **C** | **Nur UI: „Mehrere genehmigen“** wie heute, aber Backend: Beim Aufruf von approve für mehrere IDs (bereits vorhanden oder neu) **eine** Sammelmail senden. Entspricht im Ergebnis Option A. | Mittel |

**Empfehlung:** **Option A (oder C):**  
- Einen klaren **Batch-Genehmigungs-Endpoint** einführen, der mehrere `booking_ids` auf einmal genehmigt und **eine** HR-E-Mail mit Zeitraum und Tabelle sendet.  
- Einzelgenehmigung (ein Klick auf einen Tag) kann weiterhin eine E-Mail pro Tag senden, oder optional: Einzelgenehmigung ruft denselben Endpoint mit einer Ein-Element-Liste auf, dann einheitliche Mail-Logik (ebenfalls eine Mail).

**Inhalt der Sammel-Mail (Vorschlag):**  
- Betreff: z. B. „Urlaub genehmigt: [Name], [Datum von] – [Datum bis]“  
- Tabelle: Zeilen pro Tag (Datum, Wochentag, Art, Umfang, Genehmigt von).  
- Hinweis: „Bitte in Locosoft eintragen.“

**Aufwand gesamt:** Mittel (Backend: Batch-Approve + eine Batch-Mail-Funktion; Frontend: Mehrfachauswahl „Genehmigen“ auf Batch-Endpoint umstellen).

---

## Zusammenfassung Prioritäten (Vorschlag)

| Prio | Thema | Aufwand | Anmerkung |
|------|--------|--------|-----------|
| 1 | Urlaubssperre: bestehender Urlaub nicht betroffen | Keiner / optional | Bereits erfüllt; optional UI-Hinweis |
| 2 | E-Mail HR: Dennis, Katrina, Jennifer + alle prüfen | Gering | Konfiguration Mehrfach-Empfänger |
| 3 | Jahre bis 2030 (Anzeige/Sperren) | Gering | Dropdown + ggf. View-Check |
| 4 | Zeitstempel Beantragung/Genehmigung (Hover) | Gering | created_at/approved_at ausliefern + Tooltip |
| 5 | Samstagsdienst (neue Kategorie) | Klein | Typ anlegen, von Kennzahlen ausschließen |
| 6 | Genehmiger/AL: für Teammitglieder eintragen | Mittel | Rechte + UI |
| 7 | E-Mail HR: eine Mail pro Zeitraum (Batch) | Mittel | Batch-Approve + Sammel-Mail |
| 8 | Arbeitstage Teilzeit (Klickfelder Arbeitszeitmodell) | Mittel | Schema + Personalakte-UI |

---

**Nächste Schritte:**  
- Punkte 1–4 können schnell umgesetzt werden.  
- Punkt 8 (E-Mail Zeitraum) wie oben geplant (Option A) umsetzbar; nach Freigabe Implementierung.  
- CONTEXT.md nach Umsetzung aktualisieren.
