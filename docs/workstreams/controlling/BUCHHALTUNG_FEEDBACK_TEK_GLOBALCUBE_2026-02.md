# Buchhaltungs-Feedback: TEK Drive vs. Globalcube (Februar 2026)

Kurzfassung des Feedbacks der Buchhaltung für Florian. Die Buchhaltung kennt die Konten und kann in Globalcube Berichte erzeugen.

---

## 1. Lohn Mechanik / Service (4-Lohn) – Einsatz in der TEK

- **Globalcube:** Nutzt **statisch 40 %** als Einsatzquote (EW) für die TEK (bzw. 60 % der Lohnerlöse Kd Mechanik 840001/840002 pauschal als Einsatz).
- **Drive:** Nutzt eine **6-Monats-Durchschnitts-Quote** (kalkulatorischer Einsatz), weil der tatsächliche Einsatz erst mit der Verbuchung von Lohn/Gehalt gebucht wird.
- **Folgerung:** Die verbleibende Abweichung der Zahlen zwischen Drive und Globalcube ist **plausibel** und liegt an dieser unterschiedlichen Logik (6-Monats-Quote vs. statische 40 %-Einsatzquote). Wenn die 6-Monats-Quote z. B. 36 % oder 45 % ergibt, weichen Einsatz und DB1 für 4-Lohn entsprechend ab.

---

## 2. Konto 743002 (EW Fremdleistungen Landau)

- **Globalcube:** Schließt 743002 beim Einsatz aus – **Mapping wurde dort nicht angepasst, daher fachlich inkorrekt.**
- **Drive (TEK):** **743002 ist eingeschlossen** – das Konto wird bebucht und wird in der TEK im Einsatz berücksichtigt.
- **Hinweis:** In der BWA (controlling_api) bleibt 743002 weiterhin ausgeschlossen (bisherige Referenzlogik); nur die TEK rechnet mit 743002.

---

## 3. G&V-Abschlussbuchung

- **Globalcube:** Die Buchung **G&V-Abschlussbuchung** wird **nicht** berücksichtigt (gefiltert). Mit dieser Buchung werden die Aufwands- und Erlöskonten zum Jahresabschluss auf 0 gestellt.
- **Drive:** G&V-Abschlussbuchungen werden in TEK und BWA ebenfalls **ausgefiltert** (gleiche Logik wie Globalcube).

---

## 4. Clean Park (847301 / 747301) in der Abteilung Service

- **Problem:** In der Abteilung Service war Clean Park enthalten (letzte Zeile: Konto 847301 Erlös, 747301 Aufwand). Clean Park ist eine **eigene Kostenstelle** und wird am **Ende des Berichts** ausgewiesen.
- **Gewünscht:** Die Zeile 847301/747301 soll **aus der Service-Sparte entfernt** werden und nur noch als eigene Zeile „Clean Park“ am Schluss erscheinen.
- **Umsetzung in Drive:** 847301 und 747301 werden aus dem Bereich „4-Lohn“ (Service Werkstatt) herausgerechnet; die Zeile „Clean Park (847301 / 747301)“ bleibt am Ende des Berichts. Damit sollte sich auch die **Differenz von 3.787 €** zwischen erster und letzter Zeile Einsatzwerte Service auflösen.

---

## 5. Differenz 3.787 € und Report F.04

- **Service Werkstatt:** Erste Zeile Einsatzwerte und letzte Zeile Einsatzwerte wichen um 3.787 € ab (u. a. durch Doppelberücksichtigung von Clean Park in Service).
- **Globalcube:** Es gibt zwei TEK-Reports. **F.04 Tägliche Erfolgskontrolle** passt bis auf die 3.787 € mit Drive zusammen. Nach Ausgliederung von Clean Park aus Service sollte die Abweichung verschwinden.

---

## Zusammenfassung für die Buchhaltung

| Thema | Globalcube | Drive (Stand nach Anpassung) |
|-------|------------|------------------------------|
| Lohn-Einsatz 4-Lohn | **Statisch 40 % EW** (bzw. 60 % Pauschale auf 840001/840002) | 6-Monats-Durchschnitt (kalkulatorisch) |
| 743002 (EW Fremdleistungen Landau) | Ausgeschlossen (Mapping in GC nicht angepasst) | **Eingeschlossen** (fachlich korrekt) |
| G&V-Abschluss | Nicht berücksichtigt | Nicht berücksichtigt |
| Clean Park 847301/747301 | Eigene Zeile am Ende, nicht in Service | Eigene Zeile am Ende, nicht mehr in Service |
