# DRIVE Handbuch - Buchhaltung & Finanzen

**Zielgruppe:** Buchhaltung, Controlling
**Rolle im System:** buchhaltung
**Stand:** Dezember 2025

---

## Ihre Module im Überblick

| Modul | URL | Hauptfunktion |
|-------|-----|---------------|
| Bankenspiegel | /bankenspiegel/ | Konten & Transaktionen |
| Einkaufsfinanzierung | /bankenspiegel/einkaufsfinanzierung | Fahrzeug-Finanzierungen |
| Zinsen-Analyse | /bankenspiegel/zinsen-analyse | Zinsfreiheit-Tracking |
| Controlling/BWA | /controlling/ | Betriebswirtschaftliche Auswertung |
| TEK | /controlling/tek | Tägliche Erfolgskontrolle |
| Jahresprämie | /jahrespraemie/ | Prämienberechnung |

---

## 1. Bankenspiegel

**URL:** https://drive.auto-greiner.de/bankenspiegel/dashboard

### Dashboard
Das Dashboard zeigt alle Bankkonten mit:
- **Gesamtsaldo:** Summe aller Konten
- **Kontostand pro Bank:** Einzelsalden
- **Letzte Transaktionen:** Neueste Buchungen

### Kontenübersicht
Alle aktiven Konten mit:
- IBAN
- Aktueller Saldo
- Limit (falls hinterlegt)
- Verfügbarer Betrag

### Transaktionen
Alle Buchungen der letzten 90 Tage (Standard).

**Filter:**
- Zeitraum (Von/Bis)
- Konto
- Mindestbetrag
- Suchbegriff (Verwendungszweck)

**Export:** CSV-Download für Excel-Auswertungen

### Konto-Details
Klick auf ein Konto zeigt:
- Monatliche Entwicklung (Chart)
- Transaktions-Historie
- Wiederkehrende Buchungen

---

## 2. Einkaufsfinanzierung

**URL:** https://drive.auto-greiner.de/bankenspiegel/einkaufsfinanzierung

### Übersicht
Alle finanzierten Fahrzeuge gruppiert nach Bank:

| Bank | Beschreibung |
|------|--------------|
| Stellantis Floorplan | Neuwagen PSA/Opel |
| Santander | Gebrauchtwagen |
| Hyundai Capital | Hyundai/Genesis |

### Spalten
- **FIN:** Fahrgestellnummer
- **Modell:** Fahrzeugbezeichnung
- **Kaufdatum:** Übernahme ins Lager
- **Kaufpreis:** Einkaufspreis
- **Zinsfrei bis:** Ende der Zinsfreiheit
- **Zinsen/Tag:** Ab diesem Datum fällig
- **Status:** Ampel-Anzeige

### Ampel-System
- 🟢 **Grün:** > 30 Tage zinsfreie Zeit
- 🟡 **Gelb:** 15-30 Tage verbleibend
- 🔴 **Rot:** < 15 Tage oder bereits zinspflichtig

### Handlungsbedarf
Fahrzeuge mit 🔴 Status sollten prioritär verkauft werden!

**Tipp:** Sortieren Sie nach "Zinsfrei bis" aufsteigend um kritische Fahrzeuge zuerst zu sehen.

---

## 3. Zinsen-Analyse

**URL:** https://drive.auto-greiner.de/bankenspiegel/zinsen-analyse

### Dashboard
- **Gesamt-Zinslast:** Summe aller fälligen Zinsen
- **Zinsen pro Monat:** Hochrechnung
- **Kritische Fahrzeuge:** Anzahl mit Zinslast

### Analyse-Charts
- Zinsentwicklung über Zeit
- Verteilung nach Bank
- Top-10 Zinsträger

### Export
Detaillierte Zinsliste als CSV für Monatsabschluss.

---

## 4. Controlling / BWA

**URL:** https://drive.auto-greiner.de/controlling/

### BWA-Aufbau
```
Umsatzerlöse
- Fahrzeugverkauf NW
- Fahrzeugverkauf GW
- Werkstatt/Service
- Teile & Zubehör
- Sonstige

./. Materialaufwand
= ROHERTRAG

./. Personalkosten
./. Sonstige Kosten
= BETRIEBSERGEBNIS
```

### Filter
- **Zeitraum:** Monat, Quartal, Jahr
- **Standort:** Deggendorf, Landau, Gesamt
- **Vergleich:** Vorjahr, Plan

### Drill-Down
Klick auf eine Position zeigt Detail-Buchungen.

---

## 5. TEK - Tägliche Erfolgskontrolle

**URL:** https://drive.auto-greiner.de/controlling/tek

### Was ist TEK?
Die TEK zeigt täglich aktualisierte Erfolgszahlen pro Bereich.

### Bereiche
| Bereich | Inhalt |
|---------|--------|
| NW | Neuwagen-Verkauf |
| GW | Gebrauchtwagen-Verkauf |
| Teile | Teile & Zubehör |
| Werkstatt | Service/Reparatur |
| Sonstige | Vermietung, etc. |

### Kennzahlen pro Bereich
- **Umsatz:** Fakturierter Umsatz
- **Einsatz:** Wareneinsatz/Kosten
- **DB1:** Deckungsbeitrag 1 (Rohertrag)
- **Marge %:** DB1/Umsatz
- **Stück:** Anzahl (nur NW/GW)

### Breakeven-Analyse
- **Fixkosten:** Monatliche Gemeinkosten
- **Breakeven:** Erforderlicher DB1 zur Kostendeckung
- **Abstand:** Aktueller Stand vs. Breakeven

### Täglicher E-Mail-Report
Automatischer Versand um 17:30 Uhr.

**Empfänger verwalten:**
Einstellungen → Report-Subscriptions → tek_daily

---

## 6. Jahresprämie

**URL:** https://drive.auto-greiner.de/jahrespraemie/

### Funktionen
- Prämienberechnung nach Tarifvertrag
- Mitarbeiter-Liste mit Ansprüchen
- Berechnungsgrundlagen

### Berechnungslogik
- Basis: Jahresbrutto
- Faktor: Betriebsergebnis
- Kürzungen: Fehlzeiten, Teilzeit

---

## Arbeitsabläufe

### Tägliche Aufgaben
1. **Morgens:** Bankenspiegel prüfen (neue Transaktionen)
2. **Mittags:** TEK-Vorschau (aktuelle Zahlen)
3. **Abends:** TEK-Report lesen (17:30 Uhr)

### Wöchentliche Aufgaben
1. **Montag:** Zinsen-Analyse prüfen
2. **Freitag:** Wochen-BWA erstellen

### Monatliche Aufgaben
1. **Monatsanfang:** BWA Vormonat abschließen
2. **Monatsmitte:** Zinsabrechnung
3. **Monatsende:** TEK-Monatsreport

---

## Tipps & Tricks

### Schnelle Filter
- **Doppelklick auf Konto:** Öffnet Transaktionen gefiltert
- **Rechtsklick auf Betrag:** Kopiert Wert

### Export-Formate
- **CSV:** Für Excel-Import
- **PDF:** Für Archivierung

### Häufige Fragen

**Q: Warum fehlen Transaktionen?**
A: Import erfolgt täglich morgens. Aktuelle Buchungen erscheinen am nächsten Tag.

**Q: Zinsen stimmen nicht?**
A: Prüfen Sie das Kaufdatum und die Zinsfreiheit-Vereinbarung.

**Q: TEK-Zahlen weichen von Fibu ab?**
A: TEK zeigt Tages-Ist, Fibu enthält Abgrenzungen.

---

## Kontakt bei Problemen

| Problem | Ansprechpartner |
|---------|-----------------|
| Technische Fehler | IT-Abteilung |
| Fehlende Daten | [Verantwortlicher] |
| Berechtigungen | Florian Greiner |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
