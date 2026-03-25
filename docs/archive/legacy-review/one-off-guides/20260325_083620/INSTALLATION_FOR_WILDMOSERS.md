# DRIVE Portal - Installations- und Rolloutleitfaden fuer Wildmosers

**Version:** 1.0  
**Datum:** 2026-03-23  
**Ziel:** Technische Installation und sauberer Pilotbetrieb auf Basis der Wildmoser-Locosoft-PostgreSQL

---

## Zielbild

DRIVE wird als zentrales Steuerungsportal eingefuehrt.  
Die Fachdaten werden aus der vorhandenen **Wildmoser Locosoft PostgreSQL** read-only gelesen und in DRIVE visualisiert, ausgewertet und in Rollen-Workflows nutzbar gemacht.

---

## Betriebsmodell (Empfehlung)

### Option A - On-Prem bei Wildmosers
- Betrieb auf Wildmoser-Server/VM
- Volle Daten- und Betriebskontrolle lokal
- Direkter Zugriff auf Locosoft PostgreSQL im internen Netz

### Option B - Managed Betrieb (falls gewuenscht)
- Betrieb durch Greiner-Team
- Definierte Wartungs- und Supportprozesse
- Netzwerk-/Security-Freigaben auf Locosoft PostgreSQL erforderlich

---

## Technische Voraussetzungen

- Linux-Server (Ubuntu/Debian), 8 GB RAM empfohlen
- Python 3.10+, PostgreSQL 13+, Redis
- Netzwerkzugriff von DRIVE-Server auf **Locosoft PostgreSQL** (Port 5432)
- Read-only Benutzer auf Locosoft PostgreSQL
- Optional: LDAP/AD fuer zentrale Benutzeranmeldung

---

## Datenanbindung Locosoft PostgreSQL (Pflicht fuer Kernmodule)

**Notwendige Parameter:**
- Host/IP
- Port
- Datenbankname
- Read-only User
- Passwort

**Technische Leitplanken:**
- Nur read-only auf Locosoft
- Kein Schreiben durch DRIVE in Locosoft
- Verbindungs- und Timeout-Checks vor Pilotstart

---

## Standard-Installpaket fuer Wildmosers

### Paketinhalt
- Basisinstallation (Flask, Gunicorn, PostgreSQL, Redis, Celery)
- DRIVE-Portal-Datenbank initialisieren
- Locosoft PostgreSQL read-only konfigurieren
- Rollen-/Rechtegrundstruktur einrichten
- 2-3 Pilotmodule aktivieren (Controlling, Verkauf, Werkstatt)

### Optional
- LDAP/AD Login
- Automatisierte E-Mail-Reports
- Erweiterte Dashboards pro Bereich

---

## Umsetzungsplan (4-8 Wochen)

### Woche 1 - Setup
- Server bereitstellen und Basisdienste installieren
- DRIVE deployen und Grundkonfiguration setzen
- Locosoft PostgreSQL Verbindung testen

### Woche 2-3 - Pilotbetrieb
- Kernmodule mit echten Locosoft-Daten aktivieren
- Fachliche Validierung mit Key-Usern
- Rollen/Rechte verfeinern

### Woche 4 - Abnahme und Go-Live
- Abnahmetest gegen definierte Kriterien
- Schulung (Admin + Fachbereiche)
- Produktivsetzung und Hypercare-Start

---

## Abnahmekriterien (verbindlich)

- DRIVE kann stabil auf Wildmoser Locosoft PostgreSQL zugreifen.
- Controlling-, Verkaufs- und Werkstattansichten sind fachlich plausibel.
- Rollen und Zugriffe entsprechen dem abgestimmten Rechtekonzept.
- Geplanter Report-/Joblauf funktioniert (falls gebucht).
- Key-User geben Pilotbetrieb frei.

---

## Go-Live-Checkliste

- Technischer Health-Check (Portal, DB, Redis, Celery)
- Locosoft-Datenabruf im Soll (Stichproben)
- Benutzer und Rollen angelegt
- Support- und Eskalationsweg kommuniziert
- Hypercare-Termine gesetzt

---

## Supportmodell (Vorschlag)

- **Hypercare:** 2 Wochen nach Go-Live
- **Reaktionszeiten:** nach Prioritaetsstufe (P1/P2/P3)
- **Change Requests:** gebuendelt pro Sprint/Fixfenster
- **Regelbetrieb:** Monitoring, Wartung, abgestimmte Updates

---

## Risiken und Gegenmassnahmen

- **Risk:** Netzwerkzugriff auf Locosoft PostgreSQL unvollstaendig  
  **Massnahme:** Frueher Connectivity-Test inkl. Credentials und Firewall.

- **Risk:** KPI-Interpretation uneinheitlich  
  **Massnahme:** Gemeinsame KPI-Abnahme mit Key-Usern vor Rollout.

- **Risk:** Zu breiter Initialscope  
  **Massnahme:** Pilot erst mit 2-3 Kernmodulen, dann Erweiterung.

---

## Naechste konkrete Schritte fuer heute

1. Pilotumfang freigeben (Controlling, Verkauf, Werkstatt).  
2. Wildmoser Locosoft PostgreSQL Zugangsdaten und Ansprechpartner benennen.  
3. Zieltermin fuer technischen Setup-Tag festlegen.  
4. Key-User fuer Abnahme benennen.  
5. Go-Live-Fenster und Hypercare abstimmen.

---

## Kurzfazit

Wildmosers koennen DRIVE zuegig und risikoarm einfuehren, weil die vorhandene **Locosoft PostgreSQL** bereits die passende Datenbasis liefert. Mit read-only Anbindung, klaren Abnahmekriterien und einem fokussierten Pilot entsteht schnell sichtbarer Nutzen.

