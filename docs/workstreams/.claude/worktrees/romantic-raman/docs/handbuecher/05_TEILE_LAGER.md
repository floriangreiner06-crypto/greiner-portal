# DRIVE Handbuch - Teile & Lager

**Zielgruppe:** Teileleitung, Lageristen, Teile-Disponenten
**Rollen im System:** teile_leitung, teile, lager
**Stand:** Dezember 2025

---

## Ihre Module im Überblick

| Modul | URL | Hauptfunktion |
|-------|-----|---------------|
| Teilebestellungen | /werkstatt/teilebestellungen | Lieferschein-Tracking |
| Teile-Status | /werkstatt/teile-status | Kritische Teile für Aufträge |
| Renner & Penner | /werkstatt/renner-penner | Lagerumschlag-Analyse |
| Preisradar | /werkstatt/preisradar | Preisvergleich OEM vs. Fremd |

---

## 1. Teilebestellungen

**URL:** https://drive.auto-greiner.de/werkstatt/teilebestellungen

### Funktion
Übersicht aller **ServiceBox-Bestellungen** mit Tracking-Status.

### Status-Anzeige
| Status | Bedeutung |
|--------|-----------|
| 🟢 Zugebucht | Teil in Locosoft auf Lager gebucht |
| 🟡 In Locosoft | Teil gefunden, noch nicht zugebucht |
| 🔴 Geliefert | Lieferschein da, noch nicht erfasst |
| ⚪ Offen | Bestellt, noch nicht geliefert |

### Filter
- **Zeitraum:** Bestelldatum Von/Bis
- **Status:** Alle, Offen, Geliefert, Zugebucht
- **Standort:** DEG, LAN

### Detail-Ansicht
Klick auf Bestellung zeigt:
- Alle Positionen der Bestellung
- Lieferschein-Nummern
- Einzelstatus pro Position
- Locosoft-Referenzen

---

## 2. Teile-Status (Kritische Teile)

**URL:** https://drive.auto-greiner.de/werkstatt/teile-status

### Funktion
Zeigt Teile die für **aktive Werkstattaufträge** benötigt werden.

### Prioritäts-Sortierung
1. **Höchste:** Auftrag mit Termin heute
2. **Hoch:** Auftrag mit Termin diese Woche
3. **Mittel:** Auftrag ohne Termin, aber dringend markiert
4. **Normal:** Alle anderen

### Ampel-System
| Farbe | Status | Aktion |
|-------|--------|--------|
| 🔴 Rot | Fehlend | Sofort bestellen! |
| 🟡 Gelb | Bestellt | Lieferung tracken |
| 🟢 Grün | Verfügbar | Teile bereitstellen |

### Automatische Prüfung
System prüft alle 15 Minuten:
- Sind bestellte Teile eingetroffen?
- Neue fehlende Teile bei neuen Aufträgen?

---

## 3. Renner & Penner (Lageranalyse)

**URL:** https://drive.auto-greiner.de/werkstatt/renner-penner

### Kategorien

#### 🚀 Renner (Schnelldreher)
- **Definition:** Umschlag > 6x/Jahr
- **Aktion:** Mindestbestand sicherstellen
- **Anzeige:** Grün hinterlegt

#### 📦 Normal
- **Definition:** Umschlag 2-6x/Jahr
- **Aktion:** Bestand optimieren
- **Anzeige:** Weiß/neutral

#### 🔴 Penner (Langsamdreher)
- **Definition:** Umschlag < 2x/Jahr, oder > 6 Monate kein Verkauf
- **Aktion:** Bestand reduzieren, nicht nachbestellen
- **Anzeige:** Orange hinterlegt

#### 💀 Leichen (Ladenhüter)
- **Definition:** > 24 Monate kein Verkauf
- **Aktion:** Rückgabe an Lieferant oder Abschreibung
- **Anzeige:** Rot hinterlegt

### KPIs im Dashboard
| KPI | Beschreibung |
|-----|--------------|
| Gesamt-Lagerwert | Summe aller Teile auf Lager |
| Leichen-Wert | Kapital in Ladenhütern (24+ Monate) |
| Penner-Wert | Kapital in Langsamdrehern |
| Renner-Anteil | % der Teile mit hohem Umschlag |

### Filter
- **Betrieb:** Deggendorf, Landau, Hyundai DEG
- **Teile-Typ:** Opel, Hyundai, Fremdteile, AT-Teile
- **Kategorie:** Renner, Normal, Penner, Leichen
- **Mindest-Lagerwert:** Ab X Euro

### Verkaufschancen
Für Penner und Leichen werden automatisch **Marktpreise** ermittelt:
- Verkaufspreis-Empfehlung basierend auf Marktdaten
- Potenzielle Marge nach Abzug Lagerkosten
- Verkaufskanal-Empfehlung (eBay, Händler, Verschrotten)

### Export
CSV-Export für Excel mit allen Daten:
- Teilenummer, Beschreibung
- Bestand, EK-Preis, Lagerwert
- Umschlag, Reichweite
- Empfohlene Aktion

---

## 4. Preisradar

**URL:** https://drive.auto-greiner.de/werkstatt/preisradar

### Funktion
Vergleicht Preise für eine Teilenummer:
- **Locosoft OEM:** Listpreis + EK mit Rabatt
- **Schäferbarthold:** IAM-Preise
- **Dello/Automega:** (optional, langsamer)

### Eingabe
Teilenummer eingeben (mit oder ohne Bindestriche).

### Ergebnis
| Quelle | UPE | EK | Marge |
|--------|-----|----|----|
| Opel OEM | 89,00€ | 62,30€ | 30% |
| Schäferbarthold | 45,00€ | 32,00€ | 29% |

### Verwendung
- Vor Teilebestellung: Günstigste Quelle finden
- Für Preisverhandlung mit Kunden
- Fremdteile vs. OEM Entscheidung

---

## Arbeitsabläufe

### Morgen-Routine (Teile-Disposition)
1. **07:30:** Teilebestellungen prüfen - neue Lieferscheine?
2. **08:00:** Teile-Status checken - kritische Teile für heute?
3. **08:30:** ServiceBox-Bestellungen auslösen für fehlende Teile
4. **Laufend:** Wareneingang erfassen

### Wöchentliche Aufgaben
1. **Montags:** Renner & Penner Report analysieren
2. **Mittwochs:** Penner-Liste durchgehen, Rückgaben vorbereiten
3. **Freitags:** Wochen-Statistik, Bestellbedarf für nächste Woche

### Monatliche Aufgaben
1. **Monatsanfang:** Leichen-Liste prüfen, Abschreibungen vorbereiten
2. **Monatsmitte:** Bestandsoptimierung durchführen
3. **Monatsende:** Inventurdifferenzen klären

---

## Lager-Kennzahlen

### Zielwerte
| KPI | Ziel | Berechnung |
|-----|------|------------|
| Umschlagshäufigkeit | > 4x/Jahr | Jahresumsatz / Ø Lagerbestand |
| Lagerreichweite | < 3 Monate | Ø Bestand / Monatsverbrauch |
| Leichen-Quote | < 5% | Leichen-Wert / Gesamt-Lagerwert |
| Servicegrad | > 95% | Sofort lieferbar / Nachfrage |

### Lagerkosten-Kalkulation
Jährliche Lagerkosten ca. **10% des Lagerwerts**:
- Kapitalbindung (Zinsen)
- Lagerplatz
- Versicherung
- Schwund/Obsoleszenz

**Beispiel:** Teil mit 100€ EK und 2 Jahren ohne Verkauf:
- Lagerkosten: 2 × 10€ = 20€
- Effektiver EK: 120€
- → Bei VK 80€ = 40€ Verlust!

---

## Teile-Typen in Locosoft

| Code | Typ | Bemerkung |
|------|-----|-----------|
| 0 | Opel/Stellantis | OEM-Teile |
| 1 | Opel AT | Austauschteile |
| 5 | Hyundai | OEM-Teile |
| 6 | Hyundai Zubehör | Zubehör, Lifestyle |
| 10 | Fremdteil | IAM, Schäferbarthold etc. |
| 30 | Öl/Schmierstoff | Öle, Fette |
| 60 | Opel (AT) | Austauschteile |
| 65 | Hyundai (AT) | Austauschteile |

### Ausnahmen bei Renner/Penner
Folgende Teile werden **nicht** als Penner gewertet:
- **AT-Teile:** Garantie/Gewährleistung
- **Kautionsteile:** Kommen zurück
- **Saisonware:** Winterreifen etc. (saisonbereinigt)

---

## Tipps & Tricks

### Schnelle Teilesuche
- **Strg+K:** Portal-Suche, dann Teilenummer eingeben
- **Preisradar:** Direkter Preisvergleich

### Bestandsoptimierung
- Renner mit niedrigem Bestand → Mindestbestand erhöhen
- Penner mit hohem Bestand → Nicht nachbestellen
- Leichen → Aktiv vermarkten oder abschreiben

### ServiceBox-Tipps
- Bestellungen vor 12:00 Uhr = Lieferung nächster Tag
- Express-Bestellung nur bei dringendem Auftrag
- Sammelbestellung für nicht-kritische Teile

---

## Häufige Fragen

**Q: Teil wird als Penner angezeigt, aber wir brauchen es regelmäßig?**
A: Prüfen Sie ob alle Verkäufe korrekt gebucht sind. System zählt nur gebuchte Abgänge.

**Q: Warum sind AT-Teile nicht in der Penner-Liste?**
A: AT-Teile sind Garantie-/Gewährleistungsteile und werden separat betrachtet.

**Q: Wie werden die Marktpreise ermittelt?**
A: Automatischer Abgleich mit Online-Marktplätzen (eBay, Daparto). Nur als Richtwert!

**Q: Teil im System nicht gefunden?**
A: Locosoft-Stammdaten prüfen. Sync erfolgt nächtlich.

---

## Kontakt

| Thema | Ansprechpartner |
|-------|-----------------|
| Technische Probleme | IT-Abteilung |
| Locosoft-Teile-Stamm | Locosoft-Support |
| ServiceBox | Opel Teile-Service |
| Hyundai-Teile | Hyundai Teile-Service |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
