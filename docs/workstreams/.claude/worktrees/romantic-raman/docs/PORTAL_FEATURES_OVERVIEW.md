# Greiner DRIVE - Portal Features Übersicht

**Stand:** 2025-12-19 (TAG 128)
**Zweck:** Dokumentation aller Features mit Datenquellen und SOAP-Potenzial

---

## Navigationsstruktur

```
DRIVE Portal
├── Dashboard (Startseite)
├── Controlling
│   ├── Dashboard
│   ├── BWA
│   ├── TEK (Tägliche Erfolgskontrolle)
│   ├── Zinsen-Analyse
│   ├── Einkaufsfinanzierung
│   ├── Jahresprämie
│   └── Bankenspiegel
│       ├── Dashboard
│       ├── Kontenübersicht
│       ├── Transaktionen
│       └── Fahrzeugfinanzierungen
├── Verkauf
│   ├── Auftragseingang
│   ├── Auslieferungen
│   ├── Leasys Programmfinder
│   └── Leasys Kalkulator
├── Urlaubsplaner
│   ├── Mein Urlaub (V2)
│   ├── Chef-Übersicht
│   └── Administration
└── After Sales
    ├── Controlling
    │   └── Serviceberater Controlling
    ├── Teile
    │   ├── Teile-Status
    │   ├── Teilebestellungen
    │   └── Preisradar
    ├── DRIVE
    │   ├── Morgen-Briefing
    │   ├── Kulanz-Monitor
    │   └── ML-Kapazität
    └── Werkstatt
        ├── Kapazitätsplanung
        ├── Cockpit
        ├── Aufträge & Prognose
        ├── Monitor (TV)
        ├── Leistungsübersicht
        ├── Stempeluhr
        └── Tagesbericht
```

---

## 1. CONTROLLING

### 1.1 Dashboard (`/controlling/dashboard`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `controlling/dashboard.html` |
| API | `controlling_api.py` |
| Datenquelle | SQLite (fibu_buchungen, konten) |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

**Beschreibung:** Übersicht über Finanzkennzahlen, Umsatz, Kosten.

---

### 1.2 BWA (`/controlling/bwa`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `controlling/bwa.html`, `controlling/bwa_dashboard.html` |
| API | `controlling_api.py` |
| Datenquelle | SQLite (fibu_buchungen), SKR51 Kontenrahmen |
| Locosoft | Indirekt (Buchungen aus Locosoft-Export) |
| **SOAP-Potenzial** | Keins |

**Beschreibung:** Betriebswirtschaftliche Auswertung nach SKR51.

---

### 1.3 TEK - Tägliche Erfolgskontrolle (`/controlling/tek`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `controlling/tek_dashboard.html` |
| API | `controlling_api.py` |
| Datenquelle | SQLite |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

---

### 1.4 Zinsen-Analyse (`/bankenspiegel/zinsen-analyse`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `zinsen_analyse.html` |
| API | `zins_optimierung_api.py` |
| Datenquelle | SQLite (fahrzeugfinanzierungen, ek_finanzierung_konditionen) |
| Locosoft | Nein (manuelle Konditionen) |
| **SOAP-Potenzial** | Keins |

**Beschreibung:** Analyse der Fahrzeugfinanzierungen und Zinsoptimierung.

---

### 1.5 Einkaufsfinanzierung (`/bankenspiegel/einkaufsfinanzierung`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `einkaufsfinanzierung.html` |
| API | - |
| Datenquelle | SQLite (fahrzeugfinanzierungen) |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

---

### 1.6 Jahresprämie (`/jahrespraemie/`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `jahrespraemie/index.html`, `neu.html`, `berechnung.html`, `mitarbeiter.html`, `kulanz.html`, `export.html` |
| API | `jahrespraemie_api.py` |
| Datenquelle | SQLite (praemien_*, lohnjournal CSV-Upload) |
| Locosoft | **Potenzial** - Lohnjournal könnte aus Locosoft kommen |
| **SOAP-Potenzial** | ⭐ Mittel - `readEmployeeDetails` für Stammdaten |

**Beschreibung:** Berechnung und Verwaltung der Jahresprämien für Mitarbeiter.

---

### 1.7 Bankenspiegel

#### 1.7.1 Dashboard (`/bankenspiegel/dashboard`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `bankenspiegel_dashboard.html` |
| API | `bankenspiegel_api.py` |
| Datenquelle | SQLite (konten, transaktionen, salden) |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

#### 1.7.2 Kontenübersicht (`/bankenspiegel/konten`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `bankenspiegel_konten.html` |
| Datenquelle | SQLite (konten, banken) |
| **SOAP-Potenzial** | Keins |

#### 1.7.3 Transaktionen (`/bankenspiegel/transaktionen`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `bankenspiegel_transaktionen.html` |
| Datenquelle | SQLite (transaktionen) - MT940/PDF Import |
| **SOAP-Potenzial** | Keins |

#### 1.7.4 Fahrzeugfinanzierungen (`/bankenspiegel/fahrzeugfinanzierungen`)
| Eigenschaft | Wert |
|-------------|------|
| Template | (in bankenspiegel integriert) |
| Datenquelle | SQLite (fahrzeugfinanzierungen, tilgungen) |
| Locosoft | **Potenzial** - Fahrzeugdaten aus Locosoft |
| **SOAP-Potenzial** | ⭐ Mittel - `readVehicle`, `listVehicles` |

---

## 2. VERKAUF

### 2.1 Auftragseingang (`/verkauf/auftragseingang`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `verkauf_auftragseingang.html`, `verkauf_auftragseingang_detail.html` |
| API | `verkauf_api.py` |
| Datenquelle | **PostgreSQL Locosoft** (sales, dealer_vehicles, orders) |
| Locosoft | **JA - LIVE** |
| **SOAP-Potenzial** | ⭐⭐ Hoch - Alternative zu PostgreSQL |

**Beschreibung:** Live-Übersicht der Fahrzeugverkäufe und Bestellungen.

**SOAP-Operationen:**
- `listOpenWorkOrders` - Offene Aufträge
- `readWorkOrderDetails` - Auftragsdetails
- `listCustomers` - Kundensuche
- `listVehicles` - Fahrzeugsuche

---

### 2.2 Auslieferungen (`/verkauf/auslieferung/detail`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `verkauf_auslieferung_detail.html` |
| API | `verkauf_api.py` |
| Datenquelle | **PostgreSQL Locosoft** |
| Locosoft | **JA - LIVE** |
| **SOAP-Potenzial** | ⭐⭐ Hoch |

---

### 2.3 Leasys Programmfinder (`/verkauf/leasys-programmfinder`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `leasys_programmfinder.html` |
| API | `leasys_api.py` |
| Datenquelle | Externe Leasys API + SQLite Cache |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

---

### 2.4 Leasys Kalkulator (`/verkauf/leasys-kalkulator`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `leasys_kalkulator.html` |
| API | `leasys_api.py` |
| Datenquelle | Externe Leasys API |
| Locosoft | Nein |
| **SOAP-Potenzial** | Keins |

---

## 3. URLAUBSPLANER

### 3.1 Mein Urlaub V2 (`/urlaubsplaner/v2`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `urlaubsplaner_v2.html` |
| API | `vacation_api.py` |
| Datenquelle | SQLite (vacation_bookings, vacation_entitlements) + **PostgreSQL Locosoft** (absence_calendar) |
| Locosoft | **JA - READ** (Abwesenheiten synchronisieren) |
| **SOAP-Potenzial** | ⭐ Gering - Hauptsächlich PostgreSQL |

**Beschreibung:** Mitarbeiter können Urlaub beantragen und Status sehen.

---

### 3.2 Chef-Übersicht (`/urlaubsplaner/chef`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `urlaubsplaner_chef.html` |
| API | `vacation_chef_api.py` |
| Datenquelle | SQLite + PostgreSQL Locosoft |
| Locosoft | **JA - READ** |
| **SOAP-Potenzial** | ⭐ Gering |

**Beschreibung:** Vorgesetzte sehen Team-Abwesenheiten und genehmigen Anträge.

---

### 3.3 Administration (`/urlaubsplaner/admin`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `urlaubsplaner_admin.html` |
| API | `vacation_admin_api.py` |
| Datenquelle | SQLite (alle vacation_* Tabellen) |
| Locosoft | Indirekt (Mitarbeiter-Sync) |
| **SOAP-Potenzial** | ⭐ Gering |

**Beschreibung:** HR-Administration für Urlaubsansprüche und Einstellungen.

---

## 4. AFTER SALES

### 4.1 Serviceberater Controlling (`/aftersales/serviceberater/`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/serviceberater.html` |
| API | `serviceberater_api.py` |
| Datenquelle | ServiceBox Scraper + **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** Controlling-Dashboard für Serviceberater mit Auftrags- und Umsatzdaten.

**SOAP-Operationen:**
- `listCustomers` - Kundensuche
- `listVehicles` - Fahrzeugsuche
- `readWorkOrderDetails` - Auftragshistorie
- `readCustomer` - Kundendaten

---

### 4.2 Teile-Status (`/werkstatt/teile-status`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_teile_status.html` |
| API | `teile_status_api.py` |
| Datenquelle | SQLite (teile_lieferscheine) + ServiceBox |
| Locosoft | Indirekt |
| **SOAP-Potenzial** | ⭐⭐ Mittel - `readPartInformation` |

**Beschreibung:** Status offener Teilebestellungen und Lieferscheine.

---

### 4.3 Teilebestellungen (`/aftersales/teile/bestellungen`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/teilebestellungen.html`, `aftersales/bestellung_detail.html` |
| API | `parts_api.py`, `teile_api.py` |
| Datenquelle | **PostgreSQL Locosoft** (parts_master, parts_stock) |
| Locosoft | **JA - PostgreSQL** |
| **SOAP-Potenzial** | ⭐⭐ Mittel |

**SOAP-Operationen:**
- `readPartInformation` - Teileinfo
- `listSparePartTypes` - Teilearten

---

### 4.4 Preisradar (`/aftersales/teile/preisradar`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/preisradar.html` |
| API | `teile_api.py` |
| Datenquelle | **PostgreSQL Locosoft** (parts_master - 1.9M Zeilen!) + Schäferbarthold Scraper |
| Locosoft | **JA - PostgreSQL** |
| **SOAP-Potenzial** | ⭐ Gering (PostgreSQL ist hier besser für Bulk) |

**Beschreibung:** Preisvergleich zwischen Locosoft-Preisen und Wettbewerber.

---

### 4.5 Morgen-Briefing (`/werkstatt/drive/briefing`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/drive_briefing.html` |
| API | `werkstatt_live_api.py` |
| Datenquelle | **Gudat** (Selenium) + **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** Tägliche Übersicht für Werkstattleitung - Termine, Kapazitäten, Aufträge.

**SOAP-Operationen:**
- `listOpenWorkOrders` - Heutige Aufträge
- `listAvailableTimes` - Kapazitäten
- `listAppointmentsByDate` - Termine

---

### 4.6 Kulanz-Monitor (`/werkstatt/drive/kulanz`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/drive_kulanz.html` |
| API | `werkstatt_api.py` |
| Datenquelle | **PostgreSQL Locosoft** (labours, invoices) |
| Locosoft | **JA - PostgreSQL** |
| **SOAP-Potenzial** | ⭐⭐ Mittel |

**Beschreibung:** Überwachung von Kulanzfällen und Gewährleistungen.

---

### 4.7 ML-Kapazität (`/werkstatt/drive/kapazitaet`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/drive_kapazitaet.html` |
| API | `ml_prediction_api.py` |
| Datenquelle | SQLite (werkstatt_auftraege_abgerechnet) + ML-Modell |
| Locosoft | Indirekt (trainiert auf Locosoft-Daten) |
| **SOAP-Potenzial** | ⭐ Gering |

**Beschreibung:** Machine Learning Prognose für Werkstattauslastung.

---

### 4.8 Kapazitätsplanung (`/aftersales/kapazitaet`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/kapazitaetsplanung.html` |
| API | `werkstatt_live_api.py` |
| Datenquelle | **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** Planung der Werkstattkapazitäten pro Tag und Arbeitsgruppe.

**SOAP-Operationen:**
- `listAvailableTimes` - Verfügbare Zeiten pro Arbeitsgruppe
- `listWorkGroups` - Arbeitsgruppen (MON, SB, etc.)
- `writeAppointment` - Termine anlegen (v2.2!)

---

### 4.9 Werkstatt Cockpit (`/werkstatt/cockpit`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_cockpit.html` |
| API | `werkstatt_api.py`, `werkstatt_live_api.py` |
| Datenquelle | SQLite + **Gudat** + **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** Echtzeit-Dashboard für Werkstattleitung.

**SOAP-Operationen:**
- `listOpenWorkOrders` - Aktuelle Aufträge
- `readWorkOrderDetails` - Auftragsdetails

---

### 4.10 Aufträge & Prognose (`/werkstatt/auftraege`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_auftraege.html` |
| API | `werkstatt_api.py` |
| Datenquelle | SQLite (werkstatt_auftraege_abgerechnet) |
| Locosoft | Indirekt (Sync) |
| **SOAP-Potenzial** | ⭐⭐ Mittel |

---

### 4.11 Monitor TV (`/werkstatt/stempeluhr/monitor`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_stempeluhr_monitor.html` |
| API | `werkstatt_live_api.py` |
| Datenquelle | **Gudat** + **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** TV-Anzeige für Werkstatt mit Live-Aufträgen.

---

### 4.12 Leistungsübersicht (`/werkstatt/uebersicht`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_uebersicht.html` |
| API | `werkstatt_api.py` |
| Datenquelle | SQLite (werkstatt_leistung_daily) |
| Locosoft | Indirekt (täglicher Sync) |
| **SOAP-Potenzial** | ⭐ Gering |

---

### 4.13 Stempeluhr (`/werkstatt/stempeluhr`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_stempeluhr.html` |
| API | `werkstatt_live_api.py` |
| Datenquelle | **Gudat** (Selenium) + **Locosoft SOAP** |
| Locosoft | **JA - SOAP** |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH |

**Beschreibung:** Zeiterfassung für Mechaniker auf Aufträge.

**SOAP-Operationen:**
- `writeWorkOrderTimes` - Arbeitszeiten buchen
- `writeWorkTimes` - Stempelzeiten
- `readWorkOrderDetails` - Auftragsinfo

---

### 4.14 Tagesbericht (`/werkstatt/tagesbericht`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_tagesbericht.html` |
| API | `werkstatt_api.py` |
| Datenquelle | SQLite |
| Locosoft | Indirekt |
| **SOAP-Potenzial** | ⭐ Gering |

---

### 4.15 Liveboard (`/werkstatt/liveboard`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_liveboard.html`, `werkstatt_liveboard_gantt.html`, `werkstatt_live.html` |
| API | `werkstatt_live_api.py` |
| Datenquelle | **Gudat** (Selenium WebDriver) |
| Locosoft | **Potenzial** - Könnte SOAP ersetzen |
| **SOAP-Potenzial** | ⭐⭐⭐ SEHR HOCH - Gudat ersetzen! |

**Beschreibung:** Live-Ansicht aller Werkstattaufträge mit Karten-UI.

**SOAP ersetzt Gudat:**
- `listOpenWorkOrders` - Statt Gudat-Scraping
- `listAppointmentsByDate` - Termine
- `writeAppointment` - Termine anlegen (v2.2!)

---

### 4.16 Reparaturpotenzial (`/werkstatt/reparaturpotenzial`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `aftersales/werkstatt_reparaturpotenzial.html` |
| API | `reparaturpotenzial_api.py` |
| Datenquelle | **PostgreSQL Locosoft** (labours_master, labour_types) |
| Locosoft | **JA - PostgreSQL** |
| **SOAP-Potenzial** | ⭐ Gering (PostgreSQL ist besser für Analyse) |

---

## 5. ADMINISTRATION

### 5.1 Task Manager (`/admin/celery/`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `admin/celery_tasks.html` |
| Datenquelle | Celery/Redis |
| **SOAP-Potenzial** | Keins |

### 5.2 Organigramm (`/admin/organigramm`)
| Eigenschaft | Wert |
|-------------|------|
| Template | `organigramm.html` |
| API | `organization_api.py` |
| Datenquelle | SQLite (employees, manager_assignments) |
| Locosoft | Indirekt (LDAP-Sync) |
| **SOAP-Potenzial** | ⭐ Gering |

---

## SOAP-POTENZIAL ZUSAMMENFASSUNG

### ⭐⭐⭐ SEHR HOCH (Gudat ersetzen, Live-Daten)
| Feature | Route | Aktuell | Mit SOAP |
|---------|-------|---------|----------|
| Werkstatt Liveboard | `/werkstatt/liveboard` | Gudat Selenium | `listOpenWorkOrders` |
| Kapazitätsplanung | `/aftersales/kapazitaet` | Gudat | `listAvailableTimes` |
| Stempeluhr | `/werkstatt/stempeluhr` | Gudat | `writeWorkOrderTimes` |
| Werkstatt Cockpit | `/werkstatt/cockpit` | Mix | SOAP direkt |
| Morgen-Briefing | `/werkstatt/drive/briefing` | Gudat | SOAP direkt |
| Monitor TV | `/werkstatt/stempeluhr/monitor` | Gudat | SOAP direkt |
| Serviceberater | `/aftersales/serviceberater/` | Scraper | SOAP direkt |

### ⭐⭐ MITTEL (Vereinfachung möglich)
| Feature | Route | Aktuell | Mit SOAP |
|---------|-------|---------|----------|
| Auftragseingang | `/verkauf/auftragseingang` | PostgreSQL | SOAP alternative |
| Teile-Status | `/werkstatt/teile-status` | ServiceBox | `readPartInformation` |
| Teilebestellungen | `/aftersales/teile/bestellungen` | PostgreSQL | SOAP für Einzelabfragen |
| Kulanz-Monitor | `/werkstatt/drive/kulanz` | PostgreSQL | SOAP für Details |

### ⭐ GERING (PostgreSQL/SQLite besser)
| Feature | Grund |
|---------|-------|
| Preisradar | Bulk-Daten (1.9M Teile) - PostgreSQL schneller |
| BWA/Controlling | Kein Locosoft-Bezug |
| Bankenspiegel | Externe Daten (MT940) |
| Urlaubsplaner | PostgreSQL für Sync ausreichend |

---

## Datenquellen-Matrix

| Quelle | Features | SOAP ersetzbar? |
|--------|----------|-----------------|
| **SQLite** | Bankenspiegel, Urlaub, Prämien, Cache | Nein |
| **PostgreSQL Locosoft** | Verkauf, Teile, Analyse | Teilweise |
| **Gudat (Selenium)** | Liveboard, Stempeluhr, Termine | **JA - SOAP!** |
| **ServiceBox Scraper** | Serviceberater, Teile-Status | **JA - SOAP!** |
| **Externe APIs** | Leasys, Schäferbarthold | Nein |

---

## Empfehlung: SOAP-Integration Priorität

1. **Phase 1: Gudat ersetzen** (höchste Priorität)
   - Liveboard → `listOpenWorkOrders`
   - Stempeluhr → `writeWorkOrderTimes`
   - Termine → `writeAppointment` (v2.2)

2. **Phase 2: Serviceberater verbessern**
   - Kundendaten → `readCustomer`
   - Fahrzeugdaten → `readVehicle`
   - Aufträge → `readWorkOrderDetails`

3. **Phase 3: Kapazitätsplanung**
   - `listAvailableTimes` für Planung
   - `writeAppointment` für Terminanlage

---

*Dokumentation erstellt: 2025-12-19 (TAG 128)*
