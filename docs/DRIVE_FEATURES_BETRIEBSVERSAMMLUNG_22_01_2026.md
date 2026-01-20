# DRIVE Portal - Feature-Übersicht für Betriebsversammlung
## 22. Januar 2026

**Status:** 🟡 **Testing & Bug-Fixing** (noch nicht produktiv)  
**Version:** 2.0  
**Standort:** 3 Standorte (Deggendorf Opel, Deggendorf Hyundai, Landau)

---

## 📋 ÜBERSICHT

**DRIVE Portal** ist ein internes Management-System für das Autohaus Greiner mit vollständiger Locosoft-Integration. Das System bietet zentrale Dashboards, Reports und Workflows für alle wichtigen Bereiche.

**Aktueller Status:**
- ✅ **Funktionsfähig:** Alle Kern-Module implementiert
- 🟡 **Testing:** Intensive Testphase mit Mitarbeitern
- 🔧 **Bug-Fixing:** Kontinuierliche Verbesserungen basierend auf Feedback
- ⏳ **Go-Live:** Geplant nach Abschluss der Testphase

---

## 💰 FINANZEN & CONTROLLING

### Bankenspiegel
- **Automatischer PDF-Import** von Kontoauszügen (Sparkasse, VR-Bank, HypoVereinsbank)
- **Transaktions-Verwaltung** mit Kategorisierung
- **Salden-Tracking** über mehrere Konten
- **Duplikats-Erkennung** verhindert doppelte Buchungen

### BWA (Betriebswirtschaftliche Auswertung)
- **Monatliche BWA** direkt aus Locosoft-Daten
- **Vergleich Vorjahr** (YTD, Monat)
- **Standort-Filter** für alle 3 Standorte
- **Kostenstellen-Analyse** (0-7)
- **Umsatz vs. Einsatz** Darstellung

### TEK (Tägliche Erfolgskontrolle)
- **Tagesreport** mit DB1, Marge, Breakeven
- **Bereichs-Filter** (Neuwagen, Gebrauchtwagen, Teile, Werkstatt)
- **Standort-Filter** (alle Standorte)
- **Automatischer E-Mail-Versand** (täglich 19:30 Uhr)
- **Abteilungsleiter-Reports** (Filiale, NW, GW, Teile)

### Unternehmensplan & KST-Ziele
- **1%-Ziel-Planung** (Unternehmensplan)
- **Kostenstellen-Ziele** mit Tagesstatus
- **Abteilungsleiter-Planung** (Bottom-Up)

---

## 🚗 VERKAUF

### Auftragseingang
- **Live-Daten** direkt aus Locosoft
- **Neuwagen & Gebrauchtwagen** Übersicht
- **Status-Tracking** (Bestellung, Lieferung, Verkauf)
- **Filter:** Standort, Zeitraum, Status

### Budget & Planung
- **Monatliche Budget-Planung** (NW, GW)
- **Ist vs. Plan** Vergleich
- **YTD-Analyse** (Year-to-Date)
- **Standort-spezifische Budgets**

### Jahresprämie
- **Prämien-Berechnung** für Verkäufer
- **Regeln & Kulanz** Verwaltung
- **Export-Funktionen**

### Renner/Penner-Analyse
- **Verkaufs-Performance** Analyse
- **Top/Bottom Verkäufer** Identifikation

---

## 🔧 WERKSTATT & AFTERSALES

### Werkstatt-Cockpit
- **Live-Daten** aus Locosoft
- **Auftrags-Status** (offen, in Arbeit, fertig)
- **Serviceberater-Übersicht**
- **Standort-Filter**

### Serviceberater-Dashboard
- **Persönliches Dashboard** für jeden Serviceberater
- **Offene Aufträge** mit Status-Badges
- **Kundenzentrale-Integration**
- **TEK-Integration** (tägliche Erfolgskontrolle)

### Werkstatt-KPIs
- **Leistungsgrad-Berechnung** (AW-Anteil / Stempelzeit)
- **Stempelzeit-Analyse** (inkl. Mittagspause)
- **Auftragsbetrieb-Anteil** Berechnung
- **Finanz-KPIs** (Umsatz, Marge, etc.)

### Arbeitskarten
- **PDF-Generierung** für Arbeitskarten
- **Vollständige Dokumentation**

### Reparaturpotenzial
- **Analyse** von Reparatur-Möglichkeiten
- **Kosten-Nutzen** Bewertung

---

## 📦 TEILE & LAGER

### Teile-Status
- **Lagerbestände** direkt aus Locosoft
- **Bestellstatus** Tracking
- **Lieferanten-Informationen**

### Teile-Bestände
- **Stock-Übersicht** über alle Standorte
- **Bestandsbewegungen**
- **Lagerwert-Berechnung**

---

## 👥 URLAUBSPLANER

### Mitarbeiter-Verwaltung
- **Urlaubsanspruch** Verwaltung
- **Abteilungs-Zuordnung**
- **Vorgesetzten-Hierarchie**

### Urlaubsbuchungen
- **Kalender-Ansicht** (Monat/Jahr)
- **Buchungs-Formular**
- **Konflikt-Erkennung** (mehrere Mitarbeiter gleichzeitig)

### Genehmigungs-Workflows
- **Mehrstufige Genehmigung** (Vorgesetzter → Chef)
- **E-Mail-Benachrichtigungen**
- **Abteilungsleiter-Regeln**

### Admin-Funktionen
- **Urlaubs-Verwaltung** für alle Mitarbeiter
- **Anpassungen** (Krankheit, Sonderurlaub)
- **Reports & Export**

**Status:** ✅ **Vollständig implementiert** (TAG 198)

---

## 📊 REPORTS & AUTOMATISIERUNG

### Automatische Reports
- **TEK Tagesreport** (täglich 19:30 Uhr - nach Locosoft Mirror)
- **TEK Filiale** (für Filialleiter)
- **TEK Neuwagen** (für Verkaufsleiter NW)
- **TEK Gebrauchtwagen** (für Verkaufsleiter GW)
- **TEK Teile** (für Teile-Leitung)

### E-Mail-Versand
- **Automatischer Versand** via Celery
- **PDF-Anhänge** (Reports)
- **HTML-Formatierung**

---

## 🔐 AUTHENTIFIZIERUNG & BERECHTIGUNGEN

### LDAP/Active Directory
- **Single Sign-On** via Active Directory
- **OU-basierte Rollen** (Geschäftsleitung → admin, Verkauf → verkauf, etc.)
- **Automatische Rollen-Zuweisung**

### Rollen-System
- **Admin** - Vollzugriff auf alle Features
- **Controlling** - Finanz-Dashboards
- **Verkauf** - Verkaufs-Module
- **Werkstatt** - Werkstatt-Module
- **Serviceberater** - Persönliches Dashboard
- **Mitarbeiter** - Basis-Zugriff

---

## 🏢 MULTI-STANDORT

### Standort-Management
- **3 Standorte** unterstützt:
  - **DEG** - Deggendorf Opel
  - **HYU** - Deggendorf Hyundai
  - **LAN** - Landau
- **Standort-Filter** in allen Dashboards
- **Standort-spezifische Daten** (BWA, Budget, etc.)

---

## 🔄 LOCOSOFT-INTEGRATION

### Daten-Synchronisation
- **Read-only Zugriff** auf Locosoft PostgreSQL
- **Live-Daten** für Werkstatt, Verkauf
- **Gespiegelte Tabellen** für BWA-Berechnung

### Unterstützte Locosoft-Daten
- **Aufträge** (Werkstatt, Verkauf)
- **Fahrzeuge**
- **Mitarbeiter**
- **Teile & Lager**
- **Journal Accountings** (für BWA)

---

## 📈 VISUALISIERUNGEN

### Chart.js Integration
- **Bar-Charts** (BWA, Budget)
- **Line-Charts** (Trends)
- **Pie-Charts** (Verteilung)
- **Dual-Axis Charts** (Betrag + Menge)

### Responsive Design
- **Bootstrap 5** für Mobile-Ansicht
- **Responsive Tabellen**
- **Touch-optimiert**

---

## 🛠️ TECHNISCHE ARCHITEKTUR

### Backend
- **Flask 3.0** + Gunicorn (4 workers)
- **PostgreSQL** (drive_portal DB)
- **Locosoft DB** (read-only)

### Frontend
- **Jinja2** Templates
- **Bootstrap 5** UI-Framework
- **Chart.js** für Visualisierungen

### Automatisierung
- **Celery** für Background-Tasks
- **Redis** als Message Broker
- **Flower** für Task-Monitoring

---

## 📊 AKTUELLER STATUS (Januar 2026)

### ✅ Implementiert & Funktionsfähig
- **Finanz-Controlling** (BWA, TEK, Bankenspiegel)
- **Verkaufs-Management** (Aufträge, Budget, Planung)
- **Werkstatt-Integration** (Live-Daten, Cockpit, Serviceberater)
- **Urlaubsplaner** (mit Genehmigungs-Workflows)
- **Teile-Management** (Lager, Bestände, Status)
- **Automatisierte Reports** (E-Mail-Versand)
- **Multi-Standort** Unterstützung
- **LDAP-Integration** (Single Sign-On)

### 🟡 In Testing & Bug-Fixing
- **Werkstatt-KPIs** (Leistungsgrad, AW-Anteil, Stempelzeit)
  - Aktuell: Abweichungen zu Locosoft werden analysiert
  - Status: Kontinuierliche Verbesserungen
- **Daten-Validierung** (Vergleich DRIVE vs. Locosoft)
- **Performance-Optimierung** (große Datensätze)
- **UI/UX-Verbesserungen** (basierend auf User-Feedback)

### ⏳ Geplant für Go-Live
- **Finale Daten-Validierung** (100% Übereinstimmung mit Locosoft)
- **User-Training** für alle Abteilungen
- **Dokumentation** für End-User
- **Go-Live-Planung** (schrittweise Rollout)

---

## 🚀 ZUKUNFTS-PERSPEKTIVE

### Kurzfristig (Q1 2026)
- ✅ **Abschluss der Testphase** mit allen Abteilungen
- ✅ **Bug-Fixes** basierend auf Feedback
- ✅ **Daten-Validierung** (100% Übereinstimmung mit Locosoft)
- ✅ **Go-Live** für alle Module

### Mittelfristig (Q2-Q3 2026)
- 🔄 **Erweiterte Analytics** (Trend-Analysen, Prognosen)
- 🔄 **Mobile App** (iOS/Android) für Serviceberater
- 🔄 **Erweiterte Automatisierung** (mehr Reports, Workflows)
- 🔄 **Integration weiterer Systeme** (falls benötigt)

### Langfristig (Q4 2026+)
- 🔮 **KI-gestützte Analysen** (Vorhersagen, Empfehlungen)
- 🔮 **Erweiterte Dashboards** (Custom Dashboards pro Rolle)
- 🔮 **API-Integration** für externe Tools
- 🔮 **Skalierung** auf weitere Standorte (falls geplant)

### Vorteile für das Unternehmen
- ✅ **Zentrale Daten-Übersicht** (alle Standorte, alle Bereiche)
- ✅ **Automatisierte Reports** (weniger manuelle Arbeit)
- ✅ **Echtzeit-Daten** (keine Verzögerungen)
- ✅ **Bessere Entscheidungsgrundlage** (datengetrieben)
- ✅ **Zeitersparnis** (weniger manuelle Auswertungen)
- ✅ **Konsistenz** (einheitliche Datenbasis)

### Herausforderungen
- ⚠️ **Daten-Validierung** (100% Übereinstimmung mit Locosoft)
- ⚠️ **User-Akzeptanz** (Gewöhnung an neues System)
- ⚠️ **Schulungsbedarf** (alle Mitarbeiter)
- ⚠️ **Wartung & Support** (kontinuierliche Verbesserungen)

---

## 📋 ZUSAMMENFASSUNG

**DRIVE Portal bietet:**

✅ **Vollständige Finanz-Übersicht** (BWA, TEK, Bankenspiegel)  
✅ **Verkaufs-Management** (Aufträge, Budget, Planung)  
✅ **Werkstatt-Integration** (Live-Daten, Serviceberater)  
✅ **Urlaubsplaner** (mit Workflows)  
✅ **Multi-Standort** Unterstützung (3 Standorte)  
✅ **Automatisierte Reports** (E-Mail)  
✅ **LDAP-Integration** (Single Sign-On)  
✅ **Rollen-basierte Berechtigungen**  
✅ **Locosoft-Integration** (read-only)  
✅ **Moderne UI** (Bootstrap 5, Chart.js)  

**Aktueller Status:**
- 🟡 **Testing & Bug-Fixing** (noch nicht produktiv)
- ✅ **Alle Kern-Module funktionsfähig**
- 🔧 **Kontinuierliche Verbesserungen**
- ⏳ **Go-Live geplant nach Testphase**

**Zukunft:**
- 🚀 **Go-Live Q1 2026** (geplant)
- 🔄 **Erweiterte Features** (Q2-Q3 2026)
- 🔮 **KI-Integration** (langfristig)

---

**Erstellt:** 2026-01-XX  
**Version:** 2.0  
**Zielgruppe:** Betriebsversammlung 22.01.2026
