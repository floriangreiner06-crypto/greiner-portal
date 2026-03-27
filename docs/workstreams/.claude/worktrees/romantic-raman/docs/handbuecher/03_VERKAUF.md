# DRIVE Handbuch - Verkauf

**Zielgruppe:** Verkaufsleitung, Verkäufer, Disposition
**Rolle im System:** verkauf_leitung, verkauf, disposition
**Stand:** Dezember 2025

---

## Ihre Module im Überblick

| Modul | URL | Hauptfunktion |
|-------|-----|---------------|
| Auftragseingang | /verkauf/auftragseingang | Bestellte Fahrzeuge |
| Auslieferungen | /verkauf/auslieferung | Fakturierte Fahrzeuge |
| Lieferforecast | /verkauf/lieferforecast | Geplante Auslieferungen |
| Leasys Programmfinder | /verkauf/leasys-programmfinder | Master-Agreements |
| Leasys Kalkulator | /verkauf/leasys-kalkulator | Preiskalkulation |
| Zinsen (nur Leitung) | /bankenspiegel/zinsen-analyse | Zinsfreiheit-Tracking |

---

## 1. Auftragseingang

**URL:** https://drive.auto-greiner.de/verkauf/auftragseingang

### Dashboard
Zeigt alle **bestellten aber noch nicht ausgelieferten** Fahrzeuge.

### Ansichten
- **Nach Verkäufer:** Stückzahlen pro Mitarbeiter
- **Nach Modell:** Bestellte Modelle
- **Nach Monat:** Zeitliche Verteilung

### Filter
- **Zeitraum:** Bestelldatum Von/Bis
- **Standort:** DEG, LAN, Gesamt
- **Typ:** NW, GW, TV (Tageszulassung)
- **Verkäufer:** Einzelauswahl

### Spalten
| Spalte | Beschreibung |
|--------|--------------|
| Verkäufer | Name des Verkäufers |
| Modell | Fahrzeugbezeichnung |
| Kunde | Kundenname |
| Bestelldatum | Auftragseingang |
| Liefertermin | Geplante Auslieferung |
| Preis | Verkaufspreis |

### Täglicher E-Mail-Report
Automatischer Versand um **17:15 Uhr** mit Tagesübersicht.

---

## 2. Auslieferungen

**URL:** https://drive.auto-greiner.de/verkauf/auslieferung/detail

### Was zeigt es?
Alle **fakturierten/ausgelieferten** Fahrzeuge.

### Filter
- **Zeitraum:** Rechnungsdatum Von/Bis
- **Standort:** DEG, LAN
- **Typ:** NW, GW

### Kennzahlen
- **Stückzahl:** Anzahl Fahrzeuge
- **Umsatz:** Summe Rechnungsbeträge
- **Ø Preis:** Durchschnittspreis

### Export
CSV-Export für eigene Auswertungen.

---

## 3. Lieferforecast

**URL:** https://drive.auto-greiner.de/verkauf/lieferforecast

### Funktion
Zeigt geplante Kundenauslieferungen der nächsten Wochen.

### Prognose
- **Woche 1-4:** Detaillierte Planung
- **Monatssumme:** Erwarteter Umsatz

### Basis
Daten aus Locosoft (geplantes Auslieferungsdatum).

---

## 4. Leasys Programmfinder

**URL:** https://drive.auto-greiner.de/verkauf/leasys-programmfinder

### Zweck
Schnelle Suche nach **Leasys Master-Agreements** für Firmenkunden.

### Suche nach
- Firmenname
- Steuernummer
- PLZ

### Ergebnis
- Agreement-Nummer
- Konditionen
- Laufzeit
- Gültig bis

---

## 5. Leasys Kalkulator

**URL:** https://drive.auto-greiner.de/verkauf/leasys-kalkulator

### Funktion
Fahrzeugsuche mit **Preiskalkulation**.

### Eingabe
1. Modell auswählen
2. Ausstattung konfigurieren
3. Leasingrate berechnen

### Ausgabe
- Listenpreis
- Rabatte
- Endpreis
- Leasingrate (bei Laufzeit X)

---

## 6. Zinsen-Analyse (Verkaufsleitung)

**URL:** https://drive.auto-greiner.de/bankenspiegel/zinsen-analyse

### Relevanz für Verkauf
Fahrzeuge mit ablaufender Zinsfreiheit sollten **prioritär verkauft** werden!

### Ampel-System
- 🟢 **Grün:** Kein Handlungsbedarf
- 🟡 **Gelb:** In 2-4 Wochen zinspflichtig → Fokussieren
- 🔴 **Rot:** Sofort verkaufen!

### Zins-Ranking
Sortiert nach "Zinsen/Tag" - höchste zuerst.

---

## Arbeitsabläufe

### Tägliche Routine (Verkäufer)
1. **Morgens:** Auftragseingang prüfen (neue Bestellungen)
2. **Mittags:** Lieferforecast für Kundentermine
3. **Abends:** Tages-Report lesen (17:15 Uhr)

### Tägliche Routine (Verkaufsleitung)
1. **Morgens:** Team-Übersicht Auftragseingang
2. **Mittags:** Zinsen-kritische Fahrzeuge prüfen
3. **Abends:** TEK-Report Verkauf (17:30 Uhr)

### Monatliche Aufgaben
1. **Monatsanfang:** Vormonats-Auswertung
2. **Monatsmitte:** Ziel-Check (Stückzahlen)
3. **Monatsende:** Auslieferungs-Push

---

## Ziele & Kennzahlen

### Typische Monatsziele
| KPI | Ziel Beispiel |
|-----|---------------|
| Aufträge NW | 20 Stück |
| Aufträge GW | 15 Stück |
| Auslieferungen gesamt | 30 Stück |
| Umsatz NW | 500.000 EUR |
| Umsatz GW | 250.000 EUR |

### Tracking
Die Ziele werden im Dashboard als Fortschrittsbalken angezeigt.

---

## Tipps & Tricks

### Schnellzugriff
- **Klick auf Verkäufer-Name:** Zeigt nur dessen Fahrzeuge
- **Doppelklick auf Zeile:** Öffnet Fahrzeug-Details

### Kundeninfo schnell finden
Im Auftragseingang: Mauszeiger über Kundenname zeigt Kontaktdaten.

### Leasys-Tipps
- Programmfinder vor Kundengespräch nutzen
- Agreement-Nummer notieren für Angebotserstellung

---

## Häufige Fragen

**Q: Warum fehlt meine heutige Bestellung?**
A: Daten werden aus Locosoft synchronisiert. Neue Aufträge erscheinen nach dem nächsten Sync (stündlich).

**Q: Auslieferung zeigt falsches Datum?**
A: Basis ist das Rechnungsdatum in Locosoft, nicht die physische Übergabe.

**Q: Leasys zeigt keine Ergebnisse?**
A: Prüfen Sie die Schreibweise. Firmennamen müssen exakt übereinstimmen.

---

## Kontakt

| Thema | Ansprechpartner |
|-------|-----------------|
| Technische Probleme | IT-Abteilung |
| Leasys-Fragen | [Leasys-Verantwortlicher] |
| Datenqualität | Disposition |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
