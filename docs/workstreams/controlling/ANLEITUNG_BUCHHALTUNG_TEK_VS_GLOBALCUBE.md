# Kurzanleitung: TEK Drive vs. Globalcube – Abgleich für die Buchhaltung

**Ziel:** Die DB1-Abweichung zwischen Drive-TEK und Globalcube eingrenzen. Die Buchhaltung kennt die Konten und kann in Globalcube Berichte erzeugen – diese Anleitung sagt, worauf zu achten ist.

---

## 1. Ausgangslage

- **Erlöse/Umsätze** in Drive und Globalcube sind gleich.
- **DB1** weicht ab (DB1 = Umsatz − Einsatz → die Differenz steckt im **Einsatz**).
- Die **Datenquelle** (Locosoft) ist identisch; die Abweichung kommt von **unterschiedlicher Auswertungslogik**.

---

## 2. Was Sie in Globalcube prüfen können

### 2.1 Einsatz-Definition

- **Welche Konten** zählen in Globalcube zum „Einsatz“ für die TEK / Tägliche Erfolgskontrolle?
  - Drive nutzt die Bereiche **71xxxx (NW), 72xxxx (GW), 73xxxx (Teile), 74xxxx (Lohn), 76xxxx (Sonst)** (70–79 ohne 75/77–79 als eigene Bereiche).
- Wird das Konto **743002** („EW Fremdleistungen für Kunden“) im Einsatz **ein- oder ausgeschlossen**?
  - Drive schließt 743002 beim Einsatz aus (wie die BWA).
- Gibt es **weitere Ausnahmen** (z. B. bestimmte 74er, 75er, 77er)?

### 2.2 G&V-Abschluss

- Werden Buchungen mit **Buchungstext „G&V-Abschluss“** beim Umsatz und beim Einsatz **ausgefiltert**?
  - Drive filtert diese Buchungen in TEK und BWA heraus.

### 2.3 Bereich 4-Lohn (Werkstatt) im laufenden Monat

- Zeigt Globalcube für den **aktuellen Monat** den **verbuchten FIBU-Einsatz** (74xxxx) oder eine **Hochrechnung / Quote**?
  - Drive verwendet im laufenden Monat eine **kalkulatorische Quote** (6-Monats-Durchschnitt), weil der FIBU-Einsatz oft verzögert gebucht wird.

### 2.4 Standort / Firma

- Welche **Filter** (Standort, Firma, Kostenstelle) sind im Globalcube-Report für die TEK aktiv?
  - Drive kann „Alle“, „nur Stellantis“, „nur Deggendorf“, „nur Landau“ etc. – bitte gleichen Zeitraum und gleiche Filter wählen.

---

## 3. Vergleich konkret durchführen

1. **Gleichen Zeitraum wählen** (z. B. Februar 2026, 01.02. bis 28./29.02.).
2. **In Globalcube einen Report erzeugen**, der mindestens zeigt:
   - Umsatz (Erlöse) gesamt und ggf. pro Bereich,
   - **Einsatz** gesamt und ggf. pro Bereich,
   - **DB1** (oder Marge).
3. **In Drive** die TEK für denselben Monat öffnen (Web oder PDF).
4. **Vergleichen:**
   - Wenn **Umsatz** übereinstimmt, **Einsatz** aber abweicht → die Differenz liegt in der **Einsatz-Definition** (Konten/Filter/Ausnahmen wie 743002 oder G&V).
   - Wenn die Abweichung **nur bei 4-Lohn** auftritt → vermutlich unterschiedliche Logik „laufender Monat“ (kalkulatorisch vs. FIBU).

---

## 4. Nützliche Infos für die Buchhaltung

| Thema | Drive (TEK) |
|--------|-------------|
| **Einsatz-Konten** | 70xxxx–79xxxx, aufgeteilt in 71 (NW), 72 (GW), 73 (Teile), 74 (Lohn), 76 (Sonst). |
| **743002** | Wird beim Einsatz **ausgeschlossen**. |
| **G&V-Abschluss** | Buchungen mit Text „G&V-Abschluss“ werden **ausgefiltert**. |
| **4-Lohn aktueller Monat** | **Kalkulatorischer** Einsatz (6-Monats-Quote), kein reiner FIBU-Stand. |
| **Zeitbasis** | **Buchungsdatum** (accounting_date). |

Wenn Sie in Globalcube prüfen können, ob 743002 aus dem Einsatz ausgeschlossen wird und ob G&V-Abschluss gefiltert wird, lässt sich die Abweichung oft schon eingrenzen.

---

## 5. Ansprechpartner / Weitere Auswertung

- **Technische Details / Abfragen:** siehe `docs/workstreams/controlling/TEK_DB1_ABWEICHUNG_DRIVE_VS_GLOBALCUBE_ANALYSE.md`.
- **Vergleich Locosoft vs. Portal:** Skript `scripts/vergleiche_tek_locosoft_vs_portal_feb2026.py` (bestätigt: Datenquelle identisch).

Wenn die Buchhaltung die Globalcube-Definition (Konten, 743002, G&V, 4-Lohn) dokumentiert, kann die Drive-Auswertung bei Bedarf angepasst werden.
