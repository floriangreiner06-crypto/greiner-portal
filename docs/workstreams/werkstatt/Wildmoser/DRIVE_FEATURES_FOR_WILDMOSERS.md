# DRIVE Portal - Feature-Uebersicht fuer Wildmosers

**Version:** 1.0  
**Datum:** 2026-03-23  
**Zielgruppe:** Wildmosers - Entscheidungsgrundlage fuer Pilot und Einfuehrung

---

## Ueberblick

DRIVE ist ein integriertes Management-Portal fuer Autohaeuser mit klarer Ausrichtung auf Transparenz, Geschwindigkeit und Umsetzungssteuerung.

**Wichtig fuer Wildmosers:**  
Die Fachdaten kommen aus eurer vorhandenen **Locosoft PostgreSQL** (read-only). DRIVE liest diese Daten aus, bereitet sie auf, kombiniert sie mit Portal-Logik (KPIs, Berechtigungen, Workflows) und zeigt sie role-basiert an.

---

## Was DRIVE bei Wildmosers konkret verbessert

- **Schnellere Entscheidungen:** Kennzahlen und operative Daten ohne manuelle Excel-Konsolidierung.
- **Weniger Medienbrueche:** Ein Portal statt verteilter Listen, Mails und Einzelabfragen.
- **Bessere Fuehrung im Tagesgeschaeft:** TEK, Werkstatt-Live und Auftragseingang als fruehe Steuerungsimpulse.
- **Saubere Verantwortlichkeiten:** Rollen- und Rechtekonzept je Bereich und Standort.
- **Automatisierung statt Handarbeit:** Geplante Reports und Hintergrundjobs mit Celery.

---

## Locosoft-Daten als Basis (PostgreSQL)

Wildmosers nutzen bereits Locosoft mit PostgreSQL. Genau darauf setzt DRIVE auf:

- **Anbindung:** Read-only Verbindung auf eure Locosoft PostgreSQL.
- **Nutzung in DRIVE:** Verkauf, Werkstatt, Teile, Mitarbeiter- und Bewegungsdaten fuer Dashboards, KPIs und Reports.
- **Sicherheit:** Keine Rueckschreibungen in Locosoft durch DRIVE.
- **Mehrwert:** Einmalige Datenquelle (SSOT pro KPI in DRIVE), wiederverwendbar fuer UI, Report, E-Mail und Auswertungen.

Typische Datendom aenen aus Locosoft, die DRIVE verarbeitet:

- Auftraege (Verkauf/Werkstatt)
- Fahrzeugbewegungen und Status
- Teile- und Lagerinformationen
- Mitarbeiter-/Leistungsbezug je Modul
- Buchhalterische Bewegungen fuer Controlling-Ansichten

---

## Kernmodule fuer einen Wildmoser-Pilot

### 1) Controlling (TEK, BWA, Liquiditaetsnahe Sicht)
- Tagesnahe KPI-Sicht mit DB1, Marge, Breakeven und Trend.
- Fruehes Erkennen von Abweichungen statt Monatsende-Ueberraschungen.
- Locosoft PostgreSQL liefert die operativen Rohdaten fuer die Kennzahlen.

### 2) Verkauf (Auftragseingang, Planung, Zielsteuerung)
- Aktuelle Auftragslage und Statusentwicklung.
- Vergleich Plan vs. Ist in nutzbarer Fuehrungsansicht.
- Locosoft PostgreSQL als Datenquelle fuer Auftrags- und Fahrzeugdaten.

### 3) Werkstatt (Live-Cockpit, Serviceberater, Auslastung)
- Laufende Sicht auf offene/in Arbeit/fertige Auftraege.
- Steuerung auf Tagesebene fuer Serviceleitung und Berater.
- Locosoft PostgreSQL als Basis fuer Werkstattvorgaenge und Status.

### 4) Optional frueh nutzbar: Urlaubsplaner
- Digitale Genehmigungslogik, weniger Abstimmungsaufwand.
- Kein Locosoft-Muss fuer Start, laeuft auf DRIVE-Portal-Datenbank.

---

## 45-Minuten Demo-Ablauf fuer Wildmosers

1. **Kontext (5 Min):** Heute genutzte Wege (Excel, Rueckfragen, Medienbrueche).  
2. **Controlling live (12 Min):** Tagessteuerung mit TEK und Abweichungen.  
3. **Verkauf live (10 Min):** Auftragseingang, Status, Plan-Ist.  
4. **Werkstatt live (10 Min):** Priorisierung und operative Fuehrung.  
5. **Einfuehrungsplan (8 Min):** Pilot, Abnahme, Schulung, Go-Live.

In jeder Demo-Station explizit hervorheben:  
**"Diese Ansicht basiert auf euren Locosoft PostgreSQL-Daten."**

---

## Einfuehrungsvorschlag fuer Wildmosers (4-8 Wochen)

### Phase 1 - Pilot (2-3 Wochen)
- Technische Basisinstallation
- Locosoft PostgreSQL read-only anbinden
- 2-3 Kernmodule aktivieren
- Key-User benennen

### Phase 2 - Stabilisierung (1-2 Wochen)
- KPI-Validierung mit Fachbereichen
- Rollen/Rechte finalisieren
- Report-Empfaenger und Taktung einstellen

### Phase 3 - Rollout (1-3 Wochen)
- Schulung je Bereich (Controlling, Verkauf, Werkstatt)
- Betriebsuebergabe und Supportkanal
- Erweiterungen priorisieren

---

## Abnahmekriterien fuer den Pilot

- Login und Rollenrechte funktionieren fuer definierte Benutzer.
- Verbindung zu Wildmoser Locosoft PostgreSQL ist stabil.
- Mindestens 3 Kernansichten zeigen fachlich plausible Daten.
- Ein geplanter Report laeuft automatisiert.
- Key-User bestaetigen Nutzbarkeit fuer Tagesarbeit.

---

## Management-Kurzfazit

DRIVE ist fuer Wildmosers besonders geeignet, weil die bestehende **Locosoft PostgreSQL** direkt als operative Datenbasis genutzt wird. Dadurch entsteht schnell Mehrwert ohne Systembruch: transparente Kennzahlen, bessere Tagessteuerung und ein kontrollierter Rollout mit klaren Abnahmekriterien.

