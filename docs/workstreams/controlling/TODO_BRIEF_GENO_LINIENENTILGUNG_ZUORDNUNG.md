# TODO (Florian + Buchhaltung): Zuordnung Verkaufserlös → Finanzierungslinie (z. B. Brief Geno)

**Stand:** 2026-03-02  
**Ziel:** Der Liquiditätszugang bei Fahrzeugverkauf soll einer **konkreten Finanzierungslinie** (z. B. einer Genobank-Linie) zugeordnet werden können – unabhängig davon, welche Bank/Fianzierer im Spiel ist.

---

## Ausgangsfrage

Bei z. B. **„Brief Geno“** (Genobank-Finanzierung):  
**Wie können wir den Betrag einer Genobank-Linie zuordnen?**

- Wenn ein Fahrzeug verkauft wird, fließt Liquidität (Verkaufserlös).
- Diese Erlöse sollen einer **Linienentilgung** zugeordnet werden können („diese Einzahlung tilgt diese Genobank-Linie / diese Santander-Position“).
- Gilt generell: **Liquiditätszugang bei Verkauf ↔ Zuordnung zu einer Finanzierungslinie**, egal ob Genobank, Santander, Stellantis, Hyundai o. ä.

---

## Mögliche Ansätze (zu klären)

1. **Mehr Info in Locosoft?**
   - Gibt es in Locosoft (Fahrzeug, Rechnung, Buchung) bereits eine Kennung/Referenz, die eine Finanzierungslinie eindeutig macht?
   - Können wir daraus ableiten: „Diese Buchung/Einnahme gehört zu VIN X und damit zur Linie Y“?

2. **Kennzeichnung im DRIVE-Modul Bankenspiegel (Konto-Editor)?**
   - Können wir Konten oder Transaktionen im Bankenspiegel so kennzeichnen, dass eine **Einnahme** (z. B. Verkaufserlös) einer **bestimmten Finanzierungslinie** (z. B. Genobank-Vertrag/VIN) zugeordnet wird?
   - Z. B. bei der Transaktion: „Zuordnung: Linie/Fahrzeug X“ oder Konto-Merkmal „Einkaufsfinanzierung Genobank – Linie zuordenbar“.

3. **Hybrid**
   - Locosoft liefert VIN/Referenz; DRIVE speichert oder zeigt die Zuordnung „Einzahlung ↔ Linie“ und nutzt sie für Liquidität/Tilgungsansicht.

---

## Erwartetes Ergebnis (TODO)

- **Entscheidung:** Woher kommt die Zuordnung (Locosoft vs. DRIVE vs. beides)?
- **Umsetzung:** Konzept, wie wir „Verkaufserlös → Linienentilgung“ abbilden (Datenmodell, Bankenspiegel/Konto-Editor, ggf. Liquiditätsvorschau).
- **Buchhaltung:** Welche Infos braucht die Buchhaltung in Locosoft oder in DRIVE, um eine Linie eindeutig zu identifizieren und ggf. zu buchen?

---

## Betroffene Bereiche

- **Bankenspiegel:** Konten, Transaktionen, ggf. Konto-Editor / Transaktions-Kennzeichnung
- **Fahrzeugfinanzierungen / Einkaufsfinanzierung:** Genobank, Santander, Stellantis, Hyundai – Linien/VIN
- **Liquiditätsvorschau / Cashflow:** Tilgungen, Zuordnung Einnahme → Tilgung einer Linie

---

*Dieses TODO dient als gemeinsame Arbeitsgrundlage für Florian und Buchhaltung; Ergänzungen und Klärungsergebnisse bitte hier oder in CONTEXT.md festhalten.*
