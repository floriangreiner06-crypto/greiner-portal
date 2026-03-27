# DRIVE Handbuch - Werkstatt & Service

**Zielgruppe:** Werkstattleitung, Serviceberater, Werkstattmitarbeiter
**Rollen im System:** werkstatt_leitung, service_leitung, serviceberater, werkstatt
**Stand:** Dezember 2025

---

## Ihre Module im Überblick

| Modul | URL | Hauptfunktion |
|-------|-----|---------------|
| Dashboard | /werkstatt/dashboard | Tages-KPIs, Übersicht |
| Cockpit | /werkstatt/cockpit | Ampel-System Live-Status |
| Live-Aufträge | /werkstatt/live | Offene Aufträge Echtzeit |
| Stempeluhr | /werkstatt/stempeluhr | Mechaniker An-/Abmeldung |
| Liveboard | /werkstatt/liveboard | Wer arbeitet woran? |
| Tagesbericht | /werkstatt/tagesbericht | Tägliche Auswertung |
| Serviceberater | /werkstatt/serviceberater | Berater-Performance |
| Teile-Status | /werkstatt/teile-status | Kritische Teile |
| Kapazitätsplanung | /aftersales/kapazitaet | Wochen-Forecast |

---

## 1. Werkstatt Dashboard

**URL:** https://drive.auto-greiner.de/werkstatt/dashboard

### KPI-Kacheln
| KPI | Beschreibung | Zielwert |
|-----|--------------|----------|
| Leistungsgrad | Produktive Stunden / Anwesenheit | > 85% |
| Auslastung | Gebuchte AW / Verfügbare AW | > 100% |
| Stückzahl | Abgeschlossene Aufträge | - |
| Umsatz | Fakturierter Tagesumsatz | - |

### Ansichten
- **Heute:** Aktuelle Tageswerte (Default)
- **Diese Woche:** Mo-Fr Übersicht
- **Dieser Monat:** Monatsauswertung

### Automatische Aktualisierung
Dashboard aktualisiert sich alle **5 Minuten** automatisch.

---

## 2. Werkstatt Cockpit (Ampel-System)

**URL:** https://drive.auto-greiner.de/werkstatt/cockpit

### Ampel-Bedeutung
| Farbe | Status | Aktion |
|-------|--------|--------|
| 🟢 Grün | Im Plan | Kein Handlungsbedarf |
| 🟡 Gelb | Verzögert (15-30 Min) | Beobachten |
| 🔴 Rot | Kritisch (> 30 Min) | Sofort handeln! |
| ⚪ Grau | Pausiert/Wartend | Auf Teile/Kunde wartend |

### Spalten
- **Auftrag:** Auftragsnummer + Kurzbeschreibung
- **Mechaniker:** Zugewiesener Mitarbeiter
- **Start:** Arbeitsbeginn
- **Vorgabe:** Geplante Dauer (AW)
- **Ist:** Tatsächliche Zeit
- **Status:** Ampel

### Filter
- **Standort:** DEG, LAN
- **Status:** Alle, Aktiv, Kritisch
- **Mechaniker:** Einzelauswahl

---

## 3. Werkstatt Live

**URL:** https://drive.auto-greiner.de/werkstatt/live

### Funktion
Zeigt alle **aktuell offenen** Werkstattaufträge in Echtzeit.

### Sortierung
- Nach Eingangszeit (Standard)
- Nach Priorität (Terminaufträge zuerst)
- Nach Status

### Klick auf Auftrag
Öffnet Detailansicht mit:
- Kundeninfo
- Fahrzeugdaten
- Auftragshistorie
- Gebuchte Arbeiten

---

## 4. Stempeluhr

**URL:** https://drive.auto-greiner.de/werkstatt/stempeluhr

### Für Werkstattleitung
Übersicht wer gerade **anwesend** ist und woran gearbeitet wird.

### Stempelzeiten-Typen
| Typ | Bedeutung |
|-----|-----------|
| Arbeitsbeginn | Mechaniker hat eingestempelt |
| Arbeitsende | Mechaniker hat ausgestempelt |
| Pause Start | Mittagspause begonnen |
| Pause Ende | Mittagspause beendet |
| Auftrag Start | Arbeit an Auftrag begonnen |
| Auftrag Ende | Arbeit an Auftrag beendet |

### Stempeluhr-Monitor (TV)
**URL:** /werkstatt/stempeluhr/monitor?token=xxx

Für Werkstatt-TV ohne Login. Token bei IT anfragen.

---

## 5. Liveboard

**URL:** https://drive.auto-greiner.de/werkstatt/liveboard

### Funktion
Zeigt in Echtzeit: **Wer arbeitet gerade an welchem Auftrag?**

### Ansichten
- **Kachel-Ansicht:** Pro Mechaniker eine Kachel
- **Gantt-Ansicht:** Horizontale Zeitleiste (/werkstatt/liveboard/gantt)

### Kachel-Infos
- Mechaniker-Name + Foto
- Aktueller Auftrag
- Fahrzeug (Kennzeichen + Modell)
- Arbeitszeit bisher
- Vorgabezeit

### Für Werkstatt-TV
**URL:** /werkstatt/liveboard?fullscreen=1

Ohne Navigation, optimiert für Großbildschirm.

---

## 6. Tagesbericht

**URL:** https://drive.auto-greiner.de/werkstatt/tagesbericht

### Inhalt
Zusammenfassung des Werkstatt-Tages:
- Abgeschlossene Aufträge
- Umsatz nach Auftragsart
- Leistungsgrad pro Mechaniker
- Nachkalkulation (Vorgabe vs. Ist)

### Zeitraum
- **Standard:** Gestern
- **Wählbar:** Jedes Datum der letzten 90 Tage

### Export
CSV-Export für Excel-Auswertungen.

### Automatischer E-Mail-Versand
Täglich um **18:00 Uhr** an Werkstattleitung.

---

## 7. Serviceberater-Übersicht

**URL:** https://drive.auto-greiner.de/werkstatt/serviceberater

### KPIs pro Berater
| KPI | Beschreibung |
|-----|--------------|
| Aufträge | Anzahl angenommener Aufträge |
| Umsatz | Fakturierter Umsatz |
| Ø Auftragswert | Durchschnittlicher Rechnungsbetrag |
| Wartezeit | Ø Wartezeit Kunden |

### Zeitraum
- Heute
- Diese Woche
- Dieser Monat
- Wählbar Von/Bis

---

## 8. Teile-Status

**URL:** https://drive.auto-greiner.de/werkstatt/teile-status

### Funktion
Zeigt **kritische Teile** die für Werkstattaufträge fehlen.

### Ampel
- 🔴 **Fehlend:** Teil nicht auf Lager, Auftrag wartet
- 🟡 **Bestellt:** Teil bestellt, Lieferung erwartet
- 🟢 **Verfügbar:** Teil ist eingegangen

### Sortierung
Nach Dringlichkeit (Aufträge mit Termin zuerst).

---

## 9. Kapazitätsplanung

**URL:** https://drive.auto-greiner.de/aftersales/kapazitaet

### Wochen-Forecast
Zeigt für die nächsten 4 Wochen:
- Gebuchte AW (Terminaufträge)
- Verfügbare AW (Personal)
- Auslastung %

### Quellen
- **Locosoft:** Terminaufträge
- **Gudat:** Externe Terminbuchungen
- **Personal:** Urlaubsplaner-Abgleich

### ML-Prognose
System prognostiziert basierend auf Historiedaten:
- Erwartete Durchläufer (ohne Termin)
- Nacharbeits-Quote
- Saisonale Faktoren

---

## 10. DRIVE Module (Erweitert)

### Morgen-Briefing
**URL:** /werkstatt/drive/briefing

Tägliche Zusammenfassung für Werkstattleiter:
- Wichtige Termine heute
- Kritische Aufträge
- Personal-Übersicht
- Offene Punkte gestern

### Kulanz-Monitor
**URL:** /werkstatt/drive/kulanz

Überwacht Kulanz-Kosten und identifiziert:
- Häufige Kulanz-Gründe
- Kosten pro Fahrzeugmodell
- Trend-Analyse

### Reparaturpotenzial
**URL:** /werkstatt/reparaturpotenzial

ML-basierte Upselling-Empfehlungen:
- Fahrzeuge mit fälligen Wartungen
- Historische Reparatur-Muster
- Cross-Selling Chancen

---

## Arbeitsabläufe

### Morgen-Routine (Werkstattleitung)
1. **07:00:** DRIVE Briefing lesen (/werkstatt/drive/briefing)
2. **07:15:** Cockpit prüfen - alle Mechaniker gestempelt?
3. **07:30:** Teile-Status prüfen - Engpässe?
4. **Laufend:** Cockpit im Blick behalten (Ampeln)

### Tages-Routine (Serviceberater)
1. **Morgens:** Termine des Tages sichten
2. **Bei Annahme:** Auftrag anlegen, AW schätzen
3. **Bei Abholung:** Auftrag prüfen, fakturieren
4. **Abends:** Offene Aufträge checken

### Abend-Routine (Werkstattleitung)
1. **17:00:** Tagesbericht vorprüfen
2. **17:30:** Alle Aufträge abgeschlossen?
3. **18:00:** E-Mail-Report lesen

---

## Liveboard für TV in der Werkstatt

### Einrichtung
1. TV an Werkstatt-PC anschließen
2. Browser öffnen (Chrome empfohlen)
3. URL: `https://drive.auto-greiner.de/werkstatt/liveboard?fullscreen=1`
4. F11 für Vollbild

### Alternatives Setup
Bei separatem TV ohne PC-Anbindung:
- Token bei IT anfragen
- URL: `/werkstatt/liveboard?token=xxx&fullscreen=1`

---

## Wichtige Kennzahlen

### Werkstatt-Ziele
| KPI | Ziel | Berechnung |
|-----|------|------------|
| Leistungsgrad | 85% | Produktiv-AW / Anwesenheits-AW |
| Auslastung | 100% | Fakturiert-AW / Produktiv-AW |
| Nachkalk-Quote | < 10% | Überzeit-Aufträge / Gesamt |
| Durchlaufzeit | < 2h | Ø Zeit Annahme bis Abholung |

### Ampel-Schwellwerte
- 🟢 Leistungsgrad > 80%
- 🟡 Leistungsgrad 70-80%
- 🔴 Leistungsgrad < 70%

---

## Tipps & Tricks

### Schnellzugriff
- **Strg+K:** Portal-Suche öffnen
- **Klick auf Mechaniker:** Zeigt nur dessen Aufträge
- **Doppelklick auf Auftrag:** Öffnet Locosoft-Auftrag

### Cockpit-Tipps
- Rote Aufträge zuerst bearbeiten!
- Bei mehreren Roten: Ältesten zuerst
- Graue Aufträge täglich prüfen (vergessen?)

### Stempeluhr-Tipps
- Stempeln vergessen? → Werkstattleitung informieren
- Pausenzeit wird automatisch abgezogen (45 Min bei >6h)

---

## Häufige Fragen

**Q: Auftrag zeigt falsche Vorgabezeit?**
A: Vorgabezeit kommt aus Locosoft. Bei falschen AW → Auftrag in Locosoft korrigieren.

**Q: Mechaniker erscheint nicht im Liveboard?**
A: Prüfen ob Stempelung erfolgt ist. Ohne "Arbeitsbeginn" keine Anzeige.

**Q: Teile-Status zeigt Teil als fehlend, aber es ist auf Lager?**
A: Lager-Buchung in Locosoft prüfen. Sync erfolgt alle 15 Minuten.

**Q: Kapazität zeigt keine Gudat-Termine?**
A: Gudat-Sync läuft 2x täglich. Neue Termine erscheinen nach nächstem Sync.

---

## Kontakt

| Thema | Ansprechpartner |
|-------|-----------------|
| Technische Probleme | IT-Abteilung |
| Locosoft-Fragen | Locosoft-Support |
| Kapazitätsplanung | Werkstattleitung |
| Gudat-Termine | Serviceleitung |

---

*Letzte Aktualisierung: TAG 143 - Dezember 2025*
