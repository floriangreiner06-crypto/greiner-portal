# TEK-Vergleich: Globalcube (Referenz) vs. Metabase – Monat bisher NW DEG Opel

**Stand:** Februar 2026  
**Vergleich:** „Monat bisher NW DEG Opel“ (Neuwagen, Deggendorf Opel, Feb./2026)

---

## 1. Zahlenvergleich

### Metabase / fact_bwa (DRIVE-Datenbasis)

| Kennzahl   | Wert (Feb. 2026) |
|-----------|-------------------|
| **Erlös (€)**  | 320.792,62 |
| **Einsatz (€)**| 396.678,87 |
| **DB1 (€)**    | **-75.886,25** |
| **DB1 (%)**    | (negativ) |
| **Stück**      | – (nicht in fact_bwa; nur in Locosoft) |
| **DB/Stück (€)** | – |

Quelle: `fact_bwa`, Standort = 1 (Deggendorf Opel), Konten 81xxxx (Umsatz) / 71xxxx (Einsatz), Zeitraum 01.02.–29.02.2026.

### Globalcube (Referenz-Screenshot)

Im Referenz-Screenshot „Feb./2026“ erscheint u. a.:

- **Zeile „1 - Neuwagen“ (Summe):**  
  Menge: 9, Umsatzerlöse: **244.351**, Einsatzwerte: **214.577**, DB 1 ber.: **29.775**, DB 1 in % ber.: 12,2.

Wichtig: Im Screenshot ist nicht eindeutig, ob „1 - Neuwagen“ genau **nur DEG Opel** ist oder z. B. ein anderer Standort / eine andere Auswahl. Wenn Globalcube an dieser Stelle **nur DEG Opel** abbildet, ergibt sich:

| Kennzahl (Globalcube) | Wert (Referenz) |
|-----------------------|------------------|
| Umsatzerlöse          | 244.351 €        |
| Einsatzwerte         | 214.577 €        |
| DB 1 ber.             | 29.775 €         |
| DB 1 in %             | 12,2 %           |
| Menge (Stück)         | 9                |

---

## 2. Mögliche Gründe für Abweichungen

- **Abgrenzung:**  
  - Metabase/fact_bwa: alle Buchungen Konten 81xxxx/71xxxx, Standort 1, Monat Feb. 2026.  
  - Globalcube: ggf. andere Konten-Auswahl, andere Absatzweg-/Produktfilter oder anderer Standort für die Zeile „1 - Neuwagen“. Wenn „1 - Neuwagen“ in Globalcube **nicht** nur DEG Opel ist (z. B. Landau oder Gesamt), sind die Werte nicht direkt vergleichbar.

- **Stück / DB pro Stück:**  
  Globalcube zeigt **Menge** und **DB 1 in %** (bzw. DB/Stück-Logik). In Metabase sind **Stück** und **DB/Stück (€)** als Spalten vorhanden, aber **leer**, weil die Stückzahlen aus **Locosoft** kommen und in `fact_bwa` nicht abgebildet sind.

- **Struktur / Kumulationszeilen:**  
  Globalcube: feine Hierarchie (NW Kunden Kauf, Leasing, Gewerbek., Großkunden, …) mit **Kumulationszeilen** pro Kategorie und Summe „1 - Neuwagen“.  
  Metabase: Darstellung nach **Standort + Bereich** (z. B. Deggendorf Opel, Neuwagen) mit Summenzeilen pro Standort und pro Bereich (Kostenstelle), **ohne** Aufteilung nach Absatzwegen wie in Globalcube.

---

## 3. Kurzfassung

- **Metabase (NW DEG Opel, Feb. 2026):**  
  Erlös 320.792,62 €, Einsatz 396.678,87 €, DB1 -75.886,25 €; Stück/DB-Stück leer.

- **Globalcube (Referenz „1 - Neuwagen“, Feb./2026):**  
  244.351 € Umsatz, 214.577 € Einsatz, 29.775 € DB1, 9 Stück – sofern diese Zeile **nur DEG Opel** ist, weichen die Werte stark ab (u. a. anderes Vorzeichen DB1). Dann müssen Abgrenzung und Filter (Konten, Standort, Absatzwege) in Globalcube vs. DRIVE/fact_bwa abgeglichen werden.

- **Stück / DB pro Stück:** In Metabase nur als leere Spalten; Referenzwerte aus Globalcube/Locosoft können hier nicht 1:1 nachgebildet werden.

- **Kumulationszeilen:** In Metabase sind Summen pro Standort und pro Kostenstelle (Bereich) umgesetzt; eine Absatzweg-Struktur wie in Globalcube (mit Kumulation pro „NW Kunden Kauf“ etc.) ist in Metabase derzeit nicht abgebildet.

---

## 4. Nächste Schritte (optional)

1. In Globalcube prüfen: Ist „1 - Neuwagen“ im gezeigten Report **ausschließlich DEG Opel** (Standortfilter)?
2. Wenn ja: Konten- und Filterlogik (inkl. G&V, Absatzwege) in Globalcube mit `fact_bwa`/DRIVE abgleichen, um die Differenz (u. a. 244k vs. 320k Umsatz, DB1 +30k vs. -76k) zu erklären.
3. Stückzahlen: weiter nur in DRIVE/Locosoft; Metabase zeigt die Spalten Stück/DB-Stück bewusst leer.
