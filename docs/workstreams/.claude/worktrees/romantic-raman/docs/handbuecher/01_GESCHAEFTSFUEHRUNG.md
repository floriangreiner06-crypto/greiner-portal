# DRIVE Handbuch - Geschäftsführung

**Zielgruppe:** Peter Greiner, Florian Greiner
**Rolle im System:** Administrator (Vollzugriff)
**Stand:** Dezember 2025

---

## Übersicht

Als Geschäftsführung haben Sie Zugriff auf **alle Module** des DRIVE-Portals. Dieses Handbuch fokussiert auf die für Sie relevantesten Funktionen.

---

## 1. Dashboard

**URL:** https://drive.auto-greiner.de/

Das Dashboard zeigt die wichtigsten KPIs auf einen Blick:
- Aktueller Kontostand (alle Banken)
- Offene Aufträge Werkstatt
- Verkaufszahlen Monat
- Urlaubsübersicht

---

## 2. TEK - Tägliche Erfolgskontrolle

**URL:** https://drive.auto-greiner.de/controlling/tek

### Was zeigt TEK?
- **Umsatz** nach Bereich (NW, GW, Teile, Werkstatt, Sonstige)
- **DB1** (Deckungsbeitrag 1) = Rohertrag
- **Marge %** = DB1/Umsatz
- **Breakeven-Abstand** = Wie weit über/unter Kostendeckung

### Filter
- **Standort:** Deggendorf, Landau, Gesamt
- **Zeitraum:** Tag, Monat, Jahr
- **Bereich:** NW, GW, Teile, Werkstatt, Sonstige

### Täglicher E-Mail Report
- Wird automatisch um **17:30 Uhr** versendet
- Empfänger konfigurierbar unter: Einstellungen → Report-Subscriptions

---

## 3. Bankenspiegel

**URL:** https://drive.auto-greiner.de/bankenspiegel/dashboard

### Funktionen
1. **Dashboard:** Gesamtübersicht aller Konten
2. **Konten:** Detailansicht pro Konto
3. **Transaktionen:** Alle Buchungen (filterbar)
4. **Einkaufsfinanzierung:** Fahrzeug-Finanzierungen

### KPI-Cards
- **Gesamtsaldo:** Summe aller Konten
- **Anzahl Konten:** Aktive Bankkonten
- **Transaktionen heute:** Neue Buchungen

### Einkaufsfinanzierung
Zeigt alle finanzierten Fahrzeuge:
- Stellantis Floorplan
- Santander
- Hyundai Capital

**Wichtig:** Zinsfreiheit beachten! Ampel-System:
- 🟢 Grün: > 30 Tage Zinsfreiheit
- 🟡 Gelb: 15-30 Tage
- 🔴 Rot: < 15 Tage oder überfällig

---

## 4. Controlling / BWA

**URL:** https://drive.auto-greiner.de/controlling/

### BWA-Struktur
- Umsatzerlöse
- Materialaufwand
- Rohertrag
- Personalkosten
- Sonstige Kosten
- Betriebsergebnis

### Vergleiche
- Vorjahr
- Plan
- Abweichung %

---

## 5. Verkauf

**URL:** https://drive.auto-greiner.de/verkauf/

### Auftragseingang
- Bestellte Fahrzeuge nach Verkäufer
- NW/GW/TV getrennt
- Monatsziel vs. Ist

### Auslieferungen
- Fakturierte Fahrzeuge
- Umsatz pro Verkäufer

### Lieferforecast
- Geplante Auslieferungen nächste Wochen
- Umsatzprognose

---

## 6. Werkstatt-Übersicht

**URL:** https://drive.auto-greiner.de/werkstatt/dashboard

### KPIs
- **Leistungsgrad:** Produktive Stunden / Anwesenheit
- **Auslastung:** Gebuchte AW / Verfügbare AW
- **Nachkalkulation:** Vorgabe vs. Ist-Zeit

### Cockpit (Ampel)
Schnelle Übersicht aller Aufträge:
- 🟢 Im Plan
- 🟡 Verzögert
- 🔴 Kritisch

### Liveboard
Monitor-Ansicht für TV in der Werkstatt (ohne Login).

---

## 7. Renner & Penner (Teile-Lager)

**URL:** https://drive.auto-greiner.de/werkstatt/renner-penner

### Kategorien
- **Renner:** Schnelldreher (hoher Umschlag)
- **Normal:** Durchschnittlicher Umschlag
- **Penner:** Langsame Dreher (> 6 Monate)
- **Leichen:** Keine Bewegung seit > 24 Monaten

### Verkaufschancen
Für Penner werden automatisch Marktpreise von eBay/Daparto abgerufen:
- Empfohlener VK-Preis
- Lagerkosten (10% p.a.)
- Marge nach Lagerkosten

---

## 8. Urlaubsplaner

**URL:** https://drive.auto-greiner.de/urlaubsplaner/v2

### Chef-Übersicht
- Alle Mitarbeiter mit Urlaubsanspruch
- Genehmigungs-Workflow
- Team-Kalender

### Admin-Panel
- Urlaubsansprüche pflegen
- Sonderurlaub erfassen
- Vertretungsregeln definieren

---

## 9. Report-Subscriptions

**URL:** https://drive.auto-greiner.de/admin/reports

### Verfügbare Reports
| Report | Zeitplan | Beschreibung |
|--------|----------|--------------|
| TEK Daily | 17:30 Mo-Fr | Tägliche Erfolgskontrolle |
| TEK Filiale | 17:30 Mo-Fr | TEK pro Standort |
| Auftragseingang | 17:15 Mo-Fr | Verkauf Stückzahlen |
| Werkstatt Tagesbericht | 18:00 Mo-Fr | Leistungsgrad, Nachkalk |
| Penner Weekly | Mo 7:00 | Wöchentliche Verkaufschancen |

### Empfänger verwalten
1. Report auswählen
2. E-Mail-Adresse hinzufügen/entfernen
3. Standort-Filter setzen (optional)

---

## 10. Rechteverwaltung

**URL:** https://drive.auto-greiner.de/admin/rechte

### Rollen
| Rolle | Beschreibung |
|-------|--------------|
| admin | Vollzugriff (GF, IT) |
| buchhaltung | Finanzen, Reports |
| verkauf_leitung | Verkauf + Team |
| werkstatt_leitung | Werkstatt + Team |
| service_leitung | Service + Team |
| serviceberater | Eigener Bereich |
| verkauf | Nur Verkaufs-Module |
| werkstatt | Nur Werkstatt-Module |

### User-Rollen zuweisen
1. User suchen
2. Rolle auswählen
3. Speichern

**Hinweis:** Rollen werden automatisch aus LDAP/AD übernommen. Manuelle Zuweisung überschreibt die AD-Rolle.

---

## 11. Celery Task Manager

**URL:** https://drive.auto-greiner.de/admin/celery/

### Übersicht
- Alle geplanten Hintergrund-Jobs
- Letzte Ausführung
- Status (Erfolg/Fehler)

### Manuelle Ausführung
Jobs können manuell getriggert werden (z.B. Daten-Sync).

### Flower Dashboard
Detaillierte Monitoring-Oberfläche: http://10.80.80.20:5555

---

## 12. Wichtige Kontakte

| Bereich | Ansprechpartner |
|---------|-----------------|
| IT / Entwicklung | Florian Greiner |
| Buchhaltung | [Name] |
| Verkaufsleitung DEG | [Name] |
| Verkaufsleitung LAN | Rolf Sterr |
| Werkstattleitung | [Name] |
| Serviceleitung | Matthias König |
| Teileleitung | Matthias König |

---

## Tipps & Tricks

### Schnellzugriff
- **Strg+K:** Suche öffnen (schneller Modul-Wechsel)
- **F5:** Seite aktualisieren (neue Daten laden)

### Mobile Nutzung
Das Portal ist responsive und funktioniert auf Tablets. Für Smartphones ist die Darstellung eingeschränkt.

### Datenaktualität
- **Bankenspiegel:** Täglicher Import (morgens)
- **Werkstatt Live:** Echtzeit aus Locosoft
- **Verkaufsdaten:** Nächtlicher Sync

---

*Bei Fragen oder Problemen: IT-Abteilung kontaktieren*
