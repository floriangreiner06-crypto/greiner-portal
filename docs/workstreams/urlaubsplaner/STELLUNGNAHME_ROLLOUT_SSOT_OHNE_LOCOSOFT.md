# Stellungnahme: Rollout Urlaubsplaner mit SSOT ohne Locosoft-Daten

**Stand:** 2026-02-24  
**Zweck:** Verbindliche Festlegung für den Rollout – keine Locosoft-Daten in der Resturlaubsberechnung; Anspruch führend aus Mitarbeiterverwaltung (DRIVE).  
**Vor Coding:** Diese Stellungnahme dient als Freigabe für die technische Umsetzung.

---

## 1. Beschluss für den Rollout

Für den **Rollout des Urlaubsplaners** gilt:

1. **Locosoft-Daten werden in der Resturlaubsberechnung nicht genutzt.**  
   Weder Locosoft-Verbrauch (Url/BUr) noch Locosoft-Rest fließen in Anzeige, Buchungsprüfung oder Exporte ein.

2. **Führend für den Urlaubsanspruch ist die Mitarbeiterverwaltung in DRIVE.**  
   Die Tabelle `vacation_entitlements` (gepflegt über die Mitarbeiterverwaltung / Urlaubseinstellungen) ist die **einzige Quelle** für den Jahresanspruch pro Mitarbeiter und Jahr.

3. **Resturlaub** wird ausschließlich aus DRIVE-Daten berechnet:  
   **Rest = Anspruch (Mitarbeiterverwaltung, nach Abzügen) − Verbraucht (Portal) − Geplant (Portal).**  
   Abzüge: Weihnachten/Silvester (1 Tag), ggf. freie Tage mit `affects_vacation_entitlement`. Keine Locosoft-Werte.

---

## 2. Warum das passt

- **Mitarbeiterverwaltung ist von HR bereits korrekt gepflegt.**  
  Die Ansprüche (Vollzeit, Teilzeit, unterschiedliche Tage) stehen damit in DRIVE. Es gibt keine Abhängigkeit von Locosoft für die Anspruchshöhe.

- **Unterschiedliche Ansprüche (z. B. Teilzeit) sind damit abgedeckt.**  
  Jeder MA hat in `vacation_entitlements` seinen Anspruch für das Jahr (5,5 / 11 / 16 / 22 / 27 / 30 oder individuell). Die Rest-Berechnung nutzt genau diese Werte – ohne Locosoft-Mischlogik.

- **Eine Quelle, eine Formel.**  
  Keine Zeitversätze (HR-Nachpflege in Locosoft), keine Abweichungen durch Locosoft-Codierung (Krn vs. Url), keine Safeguards. Anzeige und Buchungsprüfung sind identisch.

- **Rollout wird vereinfacht.**  
  Kein Abgleich mit Locosoft nötig für die Rest-Zahl; keine Abhängigkeit von Locosoft-Erreichbarkeit oder Mapping (locosoft_id) für die Kernfunktion „Resturlaub“.

---

## 3. Was das konkret bedeutet

| Thema | Rollout-Entscheidung |
|-------|----------------------|
| **Anspruch (Jahre, Tage)** | Nur aus `vacation_entitlements` (Mitarbeiterverwaltung). Kein Lesen aus Locosoft für Anspruch. |
| **Verbraucht / Geplant** | Nur aus `vacation_bookings` (Portal). Kein Locosoft-Urlaub in der Formel. |
| **Resturlaub (Anzeige)** | Rest = Anspruch (Portal, nach Abzügen) − Verbraucht (Portal) − Geplant (Portal). |
| **Buchungsprüfung** | Gleiche Formel wie Anzeige. Kein Locosoft-Cap, kein Safeguard. |
| **Exporte / Reporte** | Nutzen dieselbe Berechnung (nur Portal). Keine Locosoft-Werte in Rest/Anspruch. |
| **Locosoft im Kalender** | Option: Locosoft-Tage weiter zur **Information** anzeigen (z. B. anders dargestellt), aber **nicht** in die Rest-Zahl einrechnen. Kann beim Rollout so belassen oder später vereinheitlicht werden. |

---

## 4. Abgrenzung zu Locosoft

- **Locosoft** bleibt führend für Lohn, HR und die dort gepflegten Abwesenheiten.  
- **DRIVE** ist für den Rollout führend für **Planung und angezeigten Resturlaub** auf Basis der im Portal geführten Buchungen und der in der Mitarbeiterverwaltung gepflegten Ansprüche.  
- **Kommunikation:** „Rest im DRIVE = Stand nach genehmigten und geplanten Buchungen im Portal. Maßgeblich für Lohn/Personal bleibt Locosoft.“

---

## 5. Technische Konsequenz (nach Freigabe)

Nach dieser Stellungnahme ist die **technische Umsetzung**:

- In Balance, My-Balance, Team, Validierung und Admin-Exporten die **Locosoft-Logik für Rest/Anspruch entfernen** (kein Abruf Locosoft-Urlaub für die Rest-Berechnung, kein min(View, Anspruch − Locosoft), kein Safeguard).
- **Eine** zentrale Berechnungslogik: nur View (bzw. Anspruch aus `vacation_entitlements`) + Abzüge (Weihnachten/Silvester, freie Tage); Verbraucht/Geplant aus `vacation_bookings`.

Kalender-Anzeige von Locosoft-Einträgen (falls gewünscht) bleibt optional und hat keinen Einfluss auf die Rest-Zahl.

---

## 6. Zusammenfassung

- **Rollout:** Locosoft-Daten **weg** aus der Resturlaubsberechnung.  
- **Anspruch:** Führend aus **Mitarbeiterverwaltung (DRIVE)**; HR hat sie bereits korrekt gepflegt.  
- **Teilzeit / unterschiedliche Ansprüche:** Über die Mitarbeiterverwaltung abgedeckt; keine Locosoft-Anbindung nötig.  
- **Stellungnahme** damit: Freigabe für die Umsetzung (Entfernung der Locosoft-Rest-/Verbrauchs-Logik, eine Quelle, eine Formel).
