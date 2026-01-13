# DRIVE Portal - Feature-Übersicht

**Version:** 2.0  
**Datum:** 2026-01-09  
**Zielgruppe:** Leo - Feature-Übersicht für Entscheidung

---

## 📋 ÜBERSICHT

DRIVE Portal ist ein umfassendes Management-System für Autohäuser mit Locosoft-Integration. Das System bietet Dashboards, Reports und Workflows für alle wichtigen Bereiche eines Autohauses.

**Kernfunktionen:**
- ✅ Finanz-Controlling (BWA, TEK, Bankenspiegel)
- ✅ Verkaufs-Management (Auftragseingang, Budget, Planung)
- ✅ Werkstatt-Management (Live-Daten, Cockpit, Serviceberater)
- ✅ Urlaubsplaner (mit Genehmigungs-Workflows)
- ✅ Teile-Management (Lager, Bestände, Status)
- ✅ Automatisierte Reports (E-Mail-Versand)
- ✅ Multi-Standort-Unterstützung

---

## 💰 FINANZEN & CONTROLLING

### Bankenspiegel
- **Automatischer PDF-Import** von Kontoauszügen (Sparkasse, VR-Bank, HypoVereinsbank)
- **Transaktions-Verwaltung** mit Kategorisierung
- **Salden-Tracking** über mehrere Konten
- **Duplikats-Erkennung** verhindert doppelte Buchungen
- **IBAN-Extraktion** aus PDFs

### BWA (Betriebswirtschaftliche Auswertung)
- **Monatliche BWA** aus Locosoft-Daten
- **Vergleich Vorjahr** (YTD, Monat)
- **Standort-Filter** (mehrere Standorte)
- **Kostenstellen-Analyse** (0-7)
- **Umsatz vs. Einsatz** Darstellung
- **Variable vs. Fixe Kosten**

### TEK (Tägliche Erfolgskontrolle)
- **Tagesreport** mit DB1, Marge, Breakeven
- **Bereichs-Filter** (NW, GW, Teile, Werkstatt)
- **Standort-Filter** (mehrere Standorte)
- **Automatischer E-Mail-Versand** (täglich 17:30)
- **Abteilungsleiter-Reports** (Filiale, NW, GW, Teile)

### Kontenmapping
- **Konten-Struktur** aus Locosoft
- **Mapping-Übersicht** für BWA-Berechnung
- **Firma-Filter** (Stellantis, Hyundai)

### Unternehmensplan & KST-Ziele
- **1%-Ziel-Planung** (Unternehmensplan)
- **Kostenstellen-Ziele** mit Tagesstatus
- **Abteilungsleiter-Planung** (Bottom-Up)

### Finanzreporting Cube
- **OLAP-ähnlicher Cube** für flexible Analysen
- **Dimensionen:** Zeit, Standort, KST, Konto
- **Measures:** Betrag, Menge
- **Interaktive Visualisierungen** (Chart.js)

---

## 🚗 VERKAUF

### Auftragseingang
- **Live-Daten** aus Locosoft
- **Neuwagen & Gebrauchtwagen** Übersicht
- **Status-Tracking** (Bestellung, Lieferung, Verkauf)
- **Filter:** Standort, Zeitraum, Status

### Budget & Planung
- **Monatliche Budget-Planung** (NW, GW)
- **Ist vs. Plan** Vergleich
- **YTD-Analyse** (Year-to-Date)
- **Standort-spezifische Budgets**

### Leasys-Integration
- **Leasys-Programme** Abfrage
- **Finanzierungs-Konditionen**
- **Cache-System** für Performance

### Jahresprämie
- **Prämien-Berechnung** für Verkäufer
- **Regeln & Kulanz** Verwaltung
- **Export-Funktionen**

### Renner/Penner-Analyse
- **Verkaufs-Performance** Analyse
- **Top/Bottom Verkäufer**

---

## 🔧 WERKSTATT & AFTERSALES

### Werkstatt-Cockpit
- **Live-Daten** aus Locosoft
- **Auftrags-Status** (offen, in Arbeit, fertig)
- **Serviceberater-Übersicht**
- **Standort-Filter**

### Serviceberater-Dashboard
- **Persönliches Dashboard** für Serviceberater
- **Offene Aufträge** mit Badges
- **Kundenzentrale-Integration**
- **TEK-Integration** (tägliche Erfolgskontrolle)

### Arbeitskarten
- **PDF-Generierung** für Arbeitskarten
- **Vollständige Dokumentation**

### Reparaturpotenzial
- **Analyse** von Reparatur-Möglichkeiten
- **Kosten-Nutzen** Bewertung

### Stundensatz-Kalkulation
- **Kalkulation** von Stundensätzen
- **Marge-Analyse**

---

## 📦 TEILE & LAGER

### Teile-Status
- **Lagerbestände** aus Locosoft
- **Bestellstatus** Tracking
- **Lieferanten-Informationen**

### Teile-Bestände
- **Stock-Übersicht** über alle Standorte
- **Bestandsbewegungen**
- **Lagerwert-Berechnung**

### Mobis-Teilebezug
- **Mobis-Integration** für Teile-Bestellung
- **API-Anbindung**

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

---

## 📊 REPORTS & AUTOMATISIERUNG

### Automatische Reports
- **TEK Tagesreport** (täglich 17:30)
- **TEK Filiale** (für Filialleiter)
- **TEK Neuwagen** (für Verkaufsleiter NW)
- **TEK Gebrauchtwagen** (für Verkaufsleiter GW)
- **TEK Teile** (für Teile-Leitung)

### E-Mail-Versand
- **Automatischer Versand** via Celery
- **PDF-Anhänge** (Reports)
- **HTML-Formatierung**

### Celery-Tasks
- **Background-Jobs** für schwere Operationen
- **Scheduled Tasks** (täglich, wöchentlich)
- **Web-UI** für Task-Management (`/admin/celery/`)

---

## 🔐 AUTHENTIFIZIERUNG & BERECHTIGUNGEN

### LDAP/Active Directory
- **Single Sign-On** via AD
- **OU-basierte Rollen** (Geschäftsleitung → admin, Verkauf → verkauf, etc.)
- **Automatische Rollen-Zuweisung**

### Rollen-System
- **Admin** - Vollzugriff auf alle Features
- **Controlling** - Finanz-Dashboards
- **Verkauf** - Verkaufs-Module
- **Werkstatt** - Werkstatt-Module
- **Serviceberater** - Persönliches Dashboard
- **Mitarbeiter** - Basis-Zugriff

### Feature-basierte Berechtigungen
- **Granulare Berechtigungen** pro Feature
- **Standort-basierte Filter** (nur eigene Standorte)

---

## 🏢 MULTI-STANDORT

### Standort-Management
- **Mehrere Standorte** unterstützt
- **Standort-Filter** in allen Dashboards
- **Standort-spezifische Daten** (BWA, Budget, etc.)

### Standort-Konfiguration
- **Flexible Standort-Struktur** (1, 2, 3, ...)
- **Standort-Namen & Kürzel** konfigurierbar
- **Subsidiary-Mapping** für Locosoft

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

## 🛠️ TECHNISCHE FEATURES

### Performance
- **Caching** für häufige Abfragen
- **Lazy Loading** für große Datensätze
- **PostgreSQL** für schnelle Queries

### Skalierbarkeit
- **Gunicorn** mit mehreren Workers
- **Celery** für Background-Tasks
- **Redis** als Message Broker

### Monitoring
- **Logging** (strukturiert)
- **Error-Tracking**
- **Task-Monitoring** (Flower Dashboard)

---

## 📋 ZUSAMMENFASSUNG

**DRIVE Portal bietet:**

✅ **Vollständige Finanz-Übersicht** (BWA, TEK, Bankenspiegel)  
✅ **Verkaufs-Management** (Aufträge, Budget, Planung)  
✅ **Werkstatt-Integration** (Live-Daten, Serviceberater)  
✅ **Urlaubsplaner** (mit Workflows)  
✅ **Multi-Standort** Unterstützung  
✅ **Automatisierte Reports** (E-Mail)  
✅ **LDAP-Integration** (Single Sign-On)  
✅ **Rollen-basierte Berechtigungen**  
✅ **Locosoft-Integration** (read-only)  
✅ **Moderne UI** (Bootstrap 5, Chart.js)  

---

## 🚀 NÄCHSTE SCHRITTE

1. **Installation** → Siehe `INSTALLATION_FOR_LEO.md`
2. **Konfiguration** → Siehe `CONFIGURATION_CHECKLIST.md`
3. **Anpassung** → Standorte, Serviceberater, E-Mails
4. **Go-Live** → Erster Admin-User, Test-Daten

---

**Stand:** 2026-01-09  
**Version:** 2.0
