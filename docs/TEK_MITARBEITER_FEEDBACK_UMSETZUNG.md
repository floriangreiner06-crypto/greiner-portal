# TEK – Mitarbeiter-Feedback Umsetzung

**Quelle:** Zwei Rückmeldungen zu KST-Aufschlüsselung und TEK-Bericht.

---

## 1. Kostenstellen Aufschlüsselung – Spaltenbezeichnung

**Feedback:** Die Bezeichnung der Spalten sollte auf allen Seiten ganz oben angezeigt werden, sonst sehr unübersichtlich.

**Umsetzung:** In der PDF-Tabelle `repeatRows=2` setzen (Header + Subheader), damit auf jeder Seite die Spaltenköpfe wiederholt werden.

---

## 2. Absatzwege / Bezeichnungen

**Feedback:**
- Es werden keine Absatzwege z.B. T&Z oder Fremdleistung angezeigt (Hinweis: Absatzwege gelten fachlich für NW/GW; ggf. ist gemeint: bessere Sichtbarkeit/Reihenfolge).
- **Neuwagen:** „Sonstige Sonstige“ = **Sonstige Erlöse Neuwagen**
- **Gebrauchtwagen:** „Sonstige Sonstige“ = **Sonstige Erlöse Gebrauchtwagen**
- **GW aus Leasingrücknahme** (Konto 823101, 823102, 723101, 723102) laufen unter „Sonstige Sonstige“, sollen unter **Privat reg** laufen.

**Umsetzung:**
- Anzeigename: „Sonstige Sonstige“ je Bereich ersetzen durch „Sonstige Erlöse Neuwagen“ (1-NW) bzw. „Sonstige Erlöse Gebrauchtwagen“ (2-GW).
- Konten 823101, 823102 (Erlös) und 723101, 723102 (Einsatz) in `get_tek_absatzwege_direct` für Bereich 2-GW dem Absatzweg **Privat reg** zuordnen (nicht „Sonstige Sonstige“).

---

## 3. Reihenfolge Absatzwege (wie Global Cube)

**Feedback:** Zuerst Privat Käufe und Leasing, dann Gewerbekunden Kauf und Leasing, dann Großkunde Kauf und Leasing (Großkunde = Sonstige Kauf/Leasing). Privat Sonstige = verkaufte TW und VFW.

**Umsetzung:** Sortierung der Absatzwege:  
Privat Kauf → Privat Leasing → Gewerbe Kauf → Gewerbe Leasing → Sonstige Kauf → Sonstige Leasing → Privat Sonstige → Sonstige Erlöse NW/GW (statt alphabetisch).

---

## 4. Clean Park (KST)

**Feedback:** Clean Park: Erlöse und Aufwendungen fehlen (847301 und 747301). KST Clean Park (Erlöse 847301 und Aufwand 747301) fehlt.

**Umsetzung:** Clean Park als eigene Zeile in der TEK-KST-Aufschlüsselung (Konten 847301 Erlös, 747301 Aufwand). Entweder API um Clean-Park-Block erweitern oder im PDF eine zusätzliche Zeile mit Abfrage 847301/747301 ergänzen.

---

## 5. KST 7 Bezeichnung

**Feedback:** Punkt 7 Sonstige = Mietwagen. Bezeichnung ändern.

**Umsetzung:** KST 7 in der TEK von „Sonstige“ auf **„Mietwagen“** umbenennen (z. B. in `pdf_generator.py` KST_MAPPING).

---

## 6. Weitere Anmerkungen (für spätere Umsetzung)

- **NW/GW:** Zwei Zeilen NW auf Seite 1, dann Seite 2 – besser alles untereinander (Layout/Seitenumbruch prüfen).
- **Fahrzeuge:** Getrennte Zeilen „Erlöse (Klasse 8)“ und „Einsatzwerte (Klasse 7)“ verwirrend – ggf. in eine Zeile pro Position packen (größerer Layout-Change).
- **Service/Werkstatt:** Alles in einer Summe – Wunsch: Aufteilung nach Lohn Mechanik, Fremdleistung, sonstige Erlöse; monatliche Umlage Auto Greiner (12.500 €) unter sonstige Erlöse.
- **Teile und Zubehör:** Alles in einer Summe (inkl. 12.500 € Kostenumlage Auto Greiner) – ggf. Aufschlüsselung/Umlage sichtbar machen.

Diese Punkte können in weiteren Schritten umgesetzt werden (Datenbasis und Darstellung klären).
