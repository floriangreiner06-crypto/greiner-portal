# DRIVE Werkstattplanung - Machbarkeitsstudie

**Erstellt:** 2025-12-19 (TAG 129)
**Ziel:** DRIVE als moderne GUI für Werkstattplanung mit Locosoft als Single Source of Truth

---

## Executive Summary

**Machbarkeit: JA - zu ca. 85%**

Locosoft SOAP API bietet mehr als ursprünglich angenommen:
- Termine mit Ersatzwagen-Zuweisung
- Mechaniker-Zuweisung in Arbeitsleistungen
- Status-Tracking (vehicleStatus, inProgress)
- Kapazitätsplanung pro Arbeitsgruppe
- Vollständige Auftrags-/Teile-/Arbeitsverwaltung

**Was fehlt (15%):**
- Echtzeit-Mechaniker-Disposition (Live-Zuweisung wer macht was JETZT)
- Drag & Drop muss selbst gebaut werden
- Produktivitätsfaktoren pro Team

---

## 1. Marktanalyse: Was bieten die Profis?

### 1.1 SoftNRG TKP (Marktführer)

| Feature | Beschreibung |
|---------|-------------|
| **Termin- & Kapazitätsplanung** | Check-in-Intervalle, Werkstattkapazitäten |
| **planning+** | Cloud-basiert, KI-unterstützt, Ressourcenoptimierung |
| **Automatische Planung** | Mitarbeiter nach Qualifikation & Werkzeug verrechnet |
| **Skalierbarkeit** | Cloud für beliebige Betriebsgröße |

*Quelle: [soft-nrg.de](https://www.soft-nrg.de)*

### 1.2 WPS-Classic (HRF)

| Feature | Beschreibung |
|---------|-------------|
| **Termindisposition (TER)** | Grobplanung: Wann ist Kapazität frei? |
| **Auftragsdisposition (ARP)** | Feinplanung: Welcher Monteur macht was? |
| **Ersatzwagen-Planung** | Im TER-Modul integriert |
| **Qualifikations-Matching** | Stärken der Belegschaft einzelnen Aufträgen zuordnen |
| **SMS/Email-Benachrichtigung** | Kundenkommunikation |
| **Infoterminal** | Werkstatt-Display |

*Quelle: [hrf.de](https://hrf.de/produkt/wps-classic/)*

### 1.3 DA / Digitales Autohaus (Gudat)

| Feature | Beschreibung |
|---------|-------------|
| **Echtzeit-Status** | Live-Überwachung aller Aufträge |
| **Team-Zuweisung** | Aufträge an Teams/Mitarbeiter zuweisen |
| **Drag & Drop** | Intuitive Planungstafel |
| **Schichtplanung** | Termin- und Schichtplanung integriert |
| **Mobilität** | Ersatzwagen, Hol-/Bringservice |
| **Systemweite Sync** | Alle Mitarbeiter sehen gleichen Stand |

*Quelle: [digitalesautohaus.de](https://www.digitalesautohaus.de/funktionen/werkstattplanung/)*

### 1.4 Zeitmechanik

| Feature | Beschreibung |
|---------|-------------|
| **Monteur- & Bühnenplanung** | Hebebühnen-Belegung |
| **Direktannahme** | Digitale Checklisten |
| **Online-Terminbuchung** | Kundenportal |
| **Mietwagenverwaltung** | Ersatzwagen-Pool |
| **CRM** | SMS-Benachrichtigungen |
| **Ampel-Status** | Farbcodierung für Überblick |

*Quelle: [zeitmechanik.net](https://www.zeitmechanik.net/wissen/werkstattplaner-software/)*

### 1.5 Gemeinsame Kern-Features (Marktstandard)

| Feature | Priorität |
|---------|-----------|
| Terminplanung mit Kapazitätsprüfung | MUSS |
| Mechaniker-/Monteur-Zuweisung | MUSS |
| Ersatzwagen-Verwaltung | MUSS |
| Online-Terminbuchung (Kundenportal) | MUSS |
| Status-Tracking (Live) | MUSS |
| SMS/Email-Benachrichtigung | SOLL |
| Drag & Drop Planungstafel | SOLL |
| Hebebühnen-/Ressourcenplanung | KANN |
| Qualifikations-Matching | KANN |
| KI-Optimierung | ZUKUNFT |

---

## 2. Locosoft SOAP API - Vollständige Analyse

### 2.1 Alle verfügbaren Operationen

#### LIST-Operationen (Lesen)
```
listAppointmentsByDate      - Termine nach Datum
listAvailableTimes          - Freie Kapazitäten pro Arbeitsgruppe
listChanges                 - Änderungen seit Zeitstempel (für Sync!)
listCustomers               - Kundensuche (Name/Tel/Nr/Email)
listCustomerInvoices        - Rechnungen eines Kunden
listCustomerVehicles        - Fahrzeuge eines Kunden
listCustomersAndVehicles    - Kunde + alle Fahrzeuge
listLaborRates              - Stundensätze
listOpenWorkOrders          - Offene Aufträge (LIVE!)
listPackages                - Service-Pakete
listPackagesFromManufacturerByVin - Hersteller-Pakete für Fahrzeug
listCatalogDataByManufacturer    - Herstellerkatalog
listSparePartTypes          - Teilearten
listVehicles                - Fahrzeugsuche (VIN/Kennzeichen)
listVehicleCustomers        - Kunden zu Fahrzeug
listVehiclesAndCustomers    - Fahrzeug + alle Halter
listWorkGroups              - Arbeitsgruppen (18 Gruppen!)
listWorkshops               - Werkstätten (3 Betriebe)
```

#### READ-Operationen (Details)
```
readAppointment             - Termin-Details mit Ersatzwagen!
readCustomer                - Kunden-Stammdaten
readLaborInformation        - Arbeitswert-Info
readLaborAndPartInformation - Arbeit + Teile kombiniert
readPartInformation         - Teile-Info mit Lagerbestand
readPotential               - Verkaufspotential
readVehicle                 - Fahrzeug-Stammdaten
readWorkOrderDetails        - Auftrag mit allen Positionen
```

#### WRITE-Operationen (Schreiben)
```
writeAppointment            - Termin anlegen/ändern (v2.2!)
writeAppointmentNotification - Termin-Benachrichtigung (v2.2!)
writeCustomerDetails        - Kundendaten ändern
writeVehicleDetails         - Fahrzeugdaten ändern
writeWorkOrderDetails       - Auftrag anlegen/ändern
writeWorkOrderTimes         - Arbeitszeiten buchen
writeWorkTimes              - Stempelzeiten erfassen
writePotential              - Verkaufspotential speichern
```

### 2.2 Schlüssel-Datenstrukturen

#### DMSServiceAppointment (Termin)
```xml
<appointment>
  <number>123</number>
  <text>Inspektion + Reifenwechsel</text>
  <customer>...</customer>
  <vehicle>...</vehicle>

  <!-- Bringen -->
  <bringDateTime>2025-12-20T08:00:00</bringDateTime>
  <bringDurationMinutes>15</bringDurationMinutes>
  <bringServiceAdvisor>5001</bringServiceAdvisor>
  <bringServiceAdvisorName>Herr Müller</bringServiceAdvisorName>

  <!-- Abholen -->
  <returnDateTime>2025-12-20T17:00:00</returnDateTime>
  <returnDurationMinutes>15</returnDurationMinutes>
  <returnServiceAdvisor>5001</returnServiceAdvisor>

  <!-- Termin-Eigenschaften -->
  <type>fix|loose|indefinite|real</type>
  <urgency>1</urgency>
  <urgencyText>Dringend</urgencyText>

  <!-- Status -->
  <vehicleStatus>2</vehicleStatus>
  <vehicleStatusText>In Arbeit</vehicleStatusText>
  <inProgress>1</inProgress>
  <inProgressText>Wird bearbeitet</inProgressText>

  <!-- Verknüpfungen -->
  <workOrderNumber>39650</workOrderNumber>
  <rentalCar>                              <!-- ERSATZWAGEN! -->
    <number>12345</number>
    <licensePlate>DEG-EW 100</licensePlate>
    <brand>Opel</brand>
    <model>Corsa</model>
  </rentalCar>
</appointment>
```

#### DMSServiceWorkOrder (Auftrag)
```xml
<workOrder>
  <number>39650</number>
  <date>2025-12-20T08:30:00</date>
  <status>EMPTY|OPEN|INVOICED|INVOICED_EMPTY|INVOICED_OPEN</status>
  <serviceAdvisorNumber>5001</serviceAdvisorNumber>
  <customer>...</customer>
  <vehicle>...</vehicle>
  <line>
    <number>1</number>
    <labor>
      <number>AWN-001</number>
      <time>2.5</time>
      <description>Bremsenwechsel vorne</description>
      <mechanicId>5010</mechanicId>           <!-- MECHANIKER! -->
      <mechanicName>Herr Huber</mechanicName>
      <rate>1</rate>
      <rateValue>125.00</rateValue>
    </labor>
    <part>
      <number>1234567890</number>
      <description>Bremsbelag vorne</description>
      <quantity>2</quantity>
      <quantityStock>15</quantityStock>      <!-- LAGERBESTAND! -->
    </part>
  </line>
</workOrder>
```

#### DMSServiceWorkOrderTime (Stempelung)
```xml
<workOrderTime>
  <workOrderNumber>39650</workOrderNumber>
  <mechanicId>5010</mechanicId>
  <startTimestamp>2025-12-20T09:15:00</startTimestamp>
  <endTimestamp>2025-12-20T11:45:00</endTimestamp>
  <isFinished>true</isFinished>
  <workOrderLineNumber>1</workOrderLineNumber>
</workOrderTime>
```

#### DMSServiceAvailableTime (Kapazität)
```xml
<availableTime>
  <date>2025-12-20</date>
  <timeShould>480</timeShould>    <!-- Soll-Minuten -->
  <timeCan>450</timeCan>          <!-- Kann-Minuten (abzgl. Urlaub) -->
  <timeAvailable>120</timeAvailable> <!-- Noch frei -->
</availableTime>
```

### 2.3 Besondere Features im WSDL

| Feature | SOAP-Feld | Nutzbar für |
|---------|-----------|-------------|
| **Ersatzwagen** | `appointment.rentalCar` | Mietwagen-Zuweisung |
| **Serviceberater** | `appointment.bringServiceAdvisor` | Annahme-Planung |
| **Mechaniker** | `labor.mechanicId/Name` | Disposition |
| **Status** | `appointment.vehicleStatus/inProgress` | Live-Tracking |
| **Kapazität** | `listAvailableTimes` | Auslastungs-Dashboard |
| **Änderungs-Feed** | `listChanges` | Real-time Sync! |
| **Dringlichkeit** | `appointment.urgency` | Priorisierung |
| **Termin-Typ** | `fix/loose/indefinite/real` | Planungsflexibilität |

---

## 3. Feature-Matrix: DRIVE vs. Konkurrenz

| Feature | SoftNRG | WPS | Gudat | Locosoft SOAP | DRIVE möglich? |
|---------|---------|-----|-------|---------------|----------------|
| **Terminplanung** | ✅ | ✅ | ✅ | ✅ writeAppointment | ✅ JA |
| **Kapazitätsanzeige** | ✅ | ✅ | ✅ | ✅ listAvailableTimes | ✅ JA |
| **Ersatzwagen** | ✅ | ✅ | ✅ | ✅ rentalCar | ✅ JA |
| **Serviceberater-Zuweisung** | ✅ | ✅ | ✅ | ✅ bringServiceAdvisor | ✅ JA |
| **Mechaniker-Zuweisung** | ✅ | ✅ | ✅ | ✅ labor.mechanicId | ✅ JA |
| **Auftrags-Anlage** | ✅ | ✅ | ✅ | ✅ writeWorkOrderDetails | ✅ JA |
| **Teile-Verfügbarkeit** | ✅ | ✅ | - | ✅ quantityStock | ✅ JA |
| **Online-Buchung** | ✅ | ✅ | ✅ | ✅ writeAppointment | ✅ JA |
| **Status-Tracking** | ✅ | ✅ | ✅ | ✅ vehicleStatus/inProgress | ✅ JA |
| **Stempelzeiten** | ✅ | ✅ | ✅ | ✅ writeWorkOrderTimes | ✅ JA |
| **SMS/Email** | ✅ | ✅ | ✅ | ❌ | ✅ (eigene Impl.) |
| **Änderungs-Feed** | ? | ? | ? | ✅ listChanges | ✅ JA (Sync!) |
| **Drag & Drop** | ✅ | ✅ | ✅ | ❌ (nur Daten) | ✅ (eigene UI) |
| **Hebebühnen** | ✅ | ✅ | - | ❌ | 🟡 (eigene DB) |
| **Qualifikationen** | ✅ | ✅ | - | ❌ | 🟡 (eigene DB) |
| **KI-Optimierung** | ✅ | - | - | ❌ | 🔮 (Zukunft) |

**Legende:** ✅ Machbar | 🟡 Mit Zusatz-DB | ❌ Nicht möglich | 🔮 Zukunft

---

## 4. DRIVE Werkstattplanung - Konzept

### 4.1 Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    DRIVE Frontend                        │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ Terminplaner│ │ Planungstafel│ │ Online-Buchung   │  │
│  │ (Kalender)  │ │ (Drag&Drop)  │ │ (Kundenportal)   │  │
│  └──────┬──────┘ └──────┬───────┘ └────────┬─────────┘  │
│         │               │                   │            │
│  ┌──────┴───────────────┴───────────────────┴─────────┐ │
│  │              DRIVE API Layer (Flask)               │ │
│  │  /api/werkstatt/termine                            │ │
│  │  /api/werkstatt/kapazitaet                         │ │
│  │  /api/werkstatt/auftraege                          │ │
│  │  /api/werkstatt/ersatzwagen                        │ │
│  └──────────────────────┬────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │     Locosoft SOAP Client    │
           │   (Single Source of Truth)  │
           └──────────────┬──────────────┘
                          │
           ┌──────────────┴──────────────┐
           │     Locosoft DMS Server     │
           │     10.80.80.7:8086         │
           └─────────────────────────────┘
```

### 4.2 Module

#### Modul 1: Terminplaner (Kalenderansicht)
```
┌────────────────────────────────────────────────────────┐
│  Dezember 2025                        [<] [Heute] [>]  │
├────────┬────────┬────────┬────────┬────────┬─────────┬─┤
│   Mo   │   Di   │   Mi   │   Do   │   Fr   │   Sa    │ │
│   16   │   17   │   18   │   19   │   20   │   21    │ │
├────────┼────────┼────────┼────────┼────────┼─────────┼─┤
│ ████   │ █████  │ ████   │ ██     │ ███    │         │ │
│ 85%    │ 95%    │ 80%    │ 40%    │ 60%    │ Frei    │ │
├────────┴────────┴────────┴────────┴────────┴─────────┴─┤
│ Tagesansicht: Freitag, 20.12.2025                      │
├────────────────────────────────────────────────────────┤
│ 08:00 │ DEG-AB 123 │ Inspektion    │ Müller │ ⚪ Geplant│
│ 08:30 │ DEG-CD 456 │ Reifenwechsel │ Huber  │ 🔵 In Arb│
│ 09:00 │ DEG-EF 789 │ Bremsen       │ -      │ ⚪ Offen │
│ ...   │            │               │        │          │
└────────────────────────────────────────────────────────┘
```

**SOAP-Calls:**
- `listAppointmentsByDate` - Termine für Kalender
- `listAvailableTimes` - Auslastung pro Tag
- `writeAppointment` - Neuen Termin anlegen

#### Modul 2: Planungstafel (Mechaniker-Disposition)
```
┌────────────────────────────────────────────────────────┐
│  Disposition: Freitag, 20.12.2025                      │
├────────────────────────────────────────────────────────┤
│ Mechaniker │ 08:00 │ 09:00 │ 10:00 │ 11:00 │ 12:00    │
├────────────┼───────┴───────┼───────┴───────┼──────────┤
│ Huber      │ ██ DEG-AB 123 │ ██████████████ DEG-XY 999│
│            │   Inspektion  │     Getriebe (4h)        │
├────────────┼───────────────┼───────────────┼──────────┤
│ Schmidt    │ ████ DEG-CD   │ ████████ DEG-EF          │
│            │ Reifen (1.5h) │ Bremsen (2h)  │          │
├────────────┼───────────────┴───────────────┴──────────┤
│ Wagner     │ [URLAUB]                                 │
├────────────┼──────────────────────────────────────────┤
│ Unverplant │ 🚗 LAN-GH 111 (TÜV) - 1h                 │
│            │ 🚗 DEG-IJ 222 (Klima) - 2h               │
└────────────┴──────────────────────────────────────────┘
```

**SOAP-Calls:**
- `listOpenWorkOrders` - Offene Aufträge
- `readWorkOrderDetails` - Auftrag mit Arbeiten
- `writeWorkOrderDetails` mit `labor.mechanicId` - Zuweisung

#### Modul 3: Ersatzwagen-Verwaltung
```
┌────────────────────────────────────────────────────────┐
│  Ersatzwagen-Pool                                      │
├────────────────────────────────────────────────────────┤
│ Kennzeichen │ Modell      │ Status    │ Bis wann?     │
├─────────────┼─────────────┼───────────┼───────────────┤
│ DEG-EW 100  │ Opel Corsa  │ 🟢 Frei   │ -             │
│ DEG-EW 101  │ Opel Astra  │ 🔴 Vergeb.│ 20.12. 17:00  │
│ DEG-EW 102  │ Hyundai i30 │ 🔴 Vergeb.│ 21.12. 12:00  │
│ DEG-EW 103  │ Hyundai i20 │ 🟢 Frei   │ -             │
└─────────────┴─────────────┴───────────┴───────────────┘

[ Ersatzwagen zuweisen ] → Termin wählen → Auto wählen
```

**SOAP-Calls:**
- `listAppointmentsByDate` - Termine mit rentalCar
- `writeAppointment` mit `rentalCar.number` - Zuweisung

#### Modul 4: Online-Terminbuchung (Kundenportal)
```
┌────────────────────────────────────────────────────────┐
│  🔧 Werkstatt-Termin buchen                            │
├────────────────────────────────────────────────────────┤
│ Schritt 1: Fahrzeug                                    │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Kennzeichen: [DEG-AB 123    ]                      │ │
│ │ → Opel Corsa 1.2, 85.000 km, HU: 03/2026          │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ Schritt 2: Service wählen                              │
│ ┌────────────────────────────────────────────────────┐ │
│ │ [x] Inspektion (lt. Herstellervorgabe)            │ │
│ │ [ ] Reifenwechsel                                  │ │
│ │ [ ] HU/AU (TÜV)                                    │ │
│ │ [ ] Sonstiges: _______________                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ Schritt 3: Termin wählen                               │
│ ┌────────────────────────────────────────────────────┐ │
│ │     Mo 16.  Di 17.  Mi 18.  Do 19.  Fr 20.        │ │
│ │      🔴      🟡      🟢      🟢      🟡            │ │
│ │     voll    eng     frei    frei    eng           │ │
│ │                                                    │ │
│ │ Freie Zeiten am Mi 18.12.:                        │ │
│ │  ○ 08:00   ○ 09:30   ● 11:00   ○ 14:00           │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ Schritt 4: Ersatzwagen?                                │
│ ┌────────────────────────────────────────────────────┐ │
│ │ ● Ja, ich brauche einen Ersatzwagen               │ │
│ │ ○ Nein, ich warte / werde abgeholt                │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│                     [Termin buchen]                    │
└────────────────────────────────────────────────────────┘
```

**SOAP-Calls:**
- `listVehicles(LPL, "DEG-AB 123")` - Fahrzeug finden
- `listAvailableTimes` - Freie Termine
- `listPackagesFromManufacturerByVin` - Service-Pakete
- `writeAppointment` - Termin anlegen

#### Modul 5: Live-Dashboard (Management)
```
┌────────────────────────────────────────────────────────┐
│  📊 Werkstatt Live-Dashboard                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Heute: 8 Termine │ 6 in Arbeit │ 2 fertig            │
│                                                        │
│  ┌──────────────────┐ ┌──────────────────┐            │
│  │ Auslastung Heute │ │ Auslastung Woche │            │
│  │      ████████    │ │ Mo ████████      │            │
│  │        78%       │ │ Di ██████████    │            │
│  │                  │ │ Mi ██████        │            │
│  │  Frei: 2.5h      │ │ Do █████         │            │
│  └──────────────────┘ │ Fr ███████       │            │
│                       └──────────────────┘            │
│                                                        │
│  Aktive Aufträge:                                      │
│  ┌────────────────────────────────────────────────────┐│
│  │ #39650 │ DEG-AB 123 │ Huber  │ 🔵 45min │ Bremsen ││
│  │ #39651 │ DEG-CD 456 │ Schmidt│ 🔵 20min │ Insp.   ││
│  │ #39652 │ DEG-EF 789 │ -      │ ⚪ wartet│ TÜV     ││
│  └────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────┘
```

**SOAP-Calls:**
- `listOpenWorkOrders` - Aktive Aufträge
- `listAvailableTimes` - Kapazitäten
- `listChanges` - Real-time Updates (Polling)

### 4.3 Implementierungs-Roadmap

#### Phase 1: Fundament (2-3 Wochen)
- [ ] Locosoft SOAP Client Klasse (Python/Zeep)
- [ ] Basis-API-Endpunkte in Flask
- [ ] Authentifizierung & Caching
- [ ] listAvailableTimes, listOpenWorkOrders, listAppointmentsByDate

#### Phase 2: Terminplanung (2-3 Wochen)
- [ ] Kalender-UI (FullCalendar.js oder ähnlich)
- [ ] Termin-Anlage-Formular
- [ ] writeAppointment Integration
- [ ] Ersatzwagen-Zuweisung

#### Phase 3: Online-Buchung (2 Wochen)
- [ ] Kundenportal-UI
- [ ] Fahrzeug-Lookup
- [ ] Service-Auswahl
- [ ] Termin-Bestätigung per Email

#### Phase 4: Disposition (3-4 Wochen)
- [ ] Planungstafel-UI (Drag & Drop)
- [ ] Mechaniker-Zuweisung via writeWorkOrderDetails
- [ ] Status-Updates
- [ ] Live-Refresh via listChanges

#### Phase 5: Dashboard & Reporting (2 Wochen)
- [ ] Management-Dashboard
- [ ] Auslastungs-Charts
- [ ] Export-Funktionen

---

## 5. Technische Details

### 5.1 SOAP Client Beispiel

```python
from zeep import Client
from zeep.transports import Transport
from requests import Session

class LocosoftClient:
    def __init__(self):
        session = Session()
        session.auth = ('9001', 'Max2024')
        session.headers.update({
            'locosoftinterface': 'GENE-AUTO',
            'locosoftinterfaceversion': '2.2'
        })
        transport = Transport(session=session)
        self.client = Client('http://10.80.80.7:8086/?wsdl', transport=transport)

    def get_available_times(self, work_group: str, date_from, date_to):
        return self.client.service.listAvailableTimes(
            workGroupId=work_group,
            dateFrom=date_from,
            dateTo=date_to
        )

    def create_appointment(self, appointment_data: dict):
        return self.client.service.writeAppointment(
            appointment=appointment_data
        )

    def get_open_orders(self):
        return self.client.service.listOpenWorkOrders()

    def get_changes_since(self, timestamp, change_type='appointment'):
        return self.client.service.listChanges(
            listChangeType=change_type,
            listChangesSince=timestamp
        )
```

### 5.2 API-Endpunkte (Flask)

```python
@werkstatt_bp.route('/api/werkstatt/termine', methods=['GET'])
def get_termine():
    """Termine für Kalender"""
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    appointments = soap_client.list_appointments_by_date(date_from, date_to)
    return jsonify([format_appointment(a) for a in appointments])

@werkstatt_bp.route('/api/werkstatt/termine', methods=['POST'])
def create_termin():
    """Neuen Termin anlegen"""
    data = request.json
    result = soap_client.create_appointment(data)
    return jsonify({'success': True, 'appointment_number': result.number})

@werkstatt_bp.route('/api/werkstatt/kapazitaet', methods=['GET'])
def get_kapazitaet():
    """Kapazitäten pro Arbeitsgruppe"""
    work_group = request.args.get('group', 'MON')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    times = soap_client.get_available_times(work_group, date_from, date_to)
    return jsonify([format_available_time(t) for t in times])

@werkstatt_bp.route('/api/werkstatt/ersatzwagen', methods=['GET'])
def get_ersatzwagen():
    """Ersatzwagen-Status"""
    # Aus appointments mit rentalCar aggregieren
    today = datetime.now()
    appointments = soap_client.list_appointments_by_date(
        today, today + timedelta(days=7)
    )
    rental_cars = aggregate_rental_cars(appointments)
    return jsonify(rental_cars)
```

### 5.3 Real-time Sync mit listChanges

```python
import threading
import time

class LocosoftSyncService:
    def __init__(self, soap_client, callback):
        self.client = soap_client
        self.callback = callback
        self.last_sync = datetime.now()
        self.running = False

    def start(self, interval_seconds=10):
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, args=(interval_seconds,))
        self.thread.start()

    def _sync_loop(self, interval):
        while self.running:
            changes = self.client.get_changes_since(self.last_sync)
            if changes:
                for change in changes:
                    self.callback(change)
            self.last_sync = datetime.now()
            time.sleep(interval)

    def stop(self):
        self.running = False
```

---

## 6. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| SOAP-API nicht stabil | Gering | Hoch | Caching, Fallback auf PostgreSQL-Read |
| Performance bei vielen Requests | Mittel | Mittel | Aggressive Caching, Batch-Requests |
| Fehlende Features (Hebebühnen) | Sicher | Gering | Eigene Zusatz-DB in DRIVE |
| User-Akzeptanz | Mittel | Hoch | Schrittweise Einführung, Training |
| Locosoft-Upgrade bricht API | Gering | Hoch | API-Version pinnen, Tests |

---

## 7. Fazit & Empfehlung

### Machbar: JA

DRIVE kann eine vollwertige Werkstattplanung bieten mit:
- ✅ Terminplanung mit Kapazitätsprüfung
- ✅ Ersatzwagen-Verwaltung
- ✅ Online-Terminbuchung für Kunden
- ✅ Mechaniker-Zuweisung
- ✅ Status-Tracking
- ✅ Live-Dashboard
- ✅ Real-time Sync via listChanges

### Empfohlenes Vorgehen

1. **Phase 1 starten:** SOAP Client + Basis-APIs
2. **Gudat parallel weiterlaufen lassen** bis DRIVE stabil
3. **Feature-by-Feature migrieren**
4. **User-Feedback** früh einholen

### Geschätzter Gesamtaufwand

| Phase | Dauer |
|-------|-------|
| Phase 1: Fundament | 2-3 Wochen |
| Phase 2: Terminplanung | 2-3 Wochen |
| Phase 3: Online-Buchung | 2 Wochen |
| Phase 4: Disposition | 3-4 Wochen |
| Phase 5: Dashboard | 2 Wochen |
| **Gesamt** | **11-14 Wochen** |

---

## Quellen

- [soft-nrg.de - TKP Terminplanung](https://www.soft-nrg.de/en/soft-solutions/appointment-planning/soft-planning)
- [hrf.de - WPS Classic](https://hrf.de/produkt/wps-classic/)
- [digitalesautohaus.de - Werkstattplanung](https://www.digitalesautohaus.de/funktionen/werkstattplanung/)
- [zeitmechanik.net - Werkstattplaner](https://www.zeitmechanik.net/wissen/werkstattplaner-software/)
- [loco-soft.de - Terminplaner](https://loco-soft.de/produkte/programmumfang/auftragsabwicklung-werkstatt-terminplaner.html)
- [autohaus.de - Digitale Terminvereinbarung](https://www.autohaus.de/nachrichten/werkstatt/digitale-terminvereinbarung-von-der-online-plattform-ins-interne-buchungssystem-2983193)

---

## 8. Bestehende Locosoft PostgreSQL-Abfragen in DRIVE

### 8.1 Verfügbare PostgreSQL-Tabellen (loco_auswertung_db)

DRIVE nutzt bereits direkte PostgreSQL-Verbindung zu Locosoft für:

| Tabelle | Inhalt | Genutzt in |
|---------|--------|------------|
| `orders` | Aufträge | Verkauf, Werkstatt |
| `times` | Stempelungen | Live-Board, Leistung |
| `vehicles` | Fahrzeuge | Überall |
| `customers_suppliers` | Kunden | Verkauf, Controlling |
| `employees_history` | Mitarbeiter | Werkstatt |
| `invoices` | Rechnungen | Controlling |
| `parts_master` | Teilestamm (1.9M!) | Preisradar |
| `parts_stock` | Lagerbestand | Teile-Status |
| `absence_calendar` | Abwesenheiten | Urlaubsplaner |
| `labours` | Arbeitsleistungen | Werkstatt |
| `sales` | Verkäufe | Verkauf Dashboard |
| `dealer_vehicles` | Bestand | Verkauf |

### 8.2 Aktive Stempelungen (times) - Für Live-Board

```sql
-- Mechaniker mit offenen Stempelungen (aktuell arbeitend)
SELECT DISTINCT
    t.employee_number,
    eh.name as mechaniker_name,
    t.order_number,
    v.license_plate as kennzeichen,
    t.start_time,
    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as laufzeit_min
FROM times t
JOIN employees_history eh ON t.employee_number = eh.employee_number
    AND eh.is_latest_record = true
LEFT JOIN orders o ON t.order_number = o.number
LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
WHERE t.type = 2              -- Auftragsstempelung
  AND t.end_time IS NULL      -- Noch offen!
  AND t.order_number > 31     -- Keine internen
  AND DATE(t.start_time) = CURRENT_DATE
  AND eh.subsidiary IN (1, 2) -- Deggendorf
ORDER BY t.order_number;
```

**Vorteil PostgreSQL vs SOAP:** Echtzeit, keine API-Latenz!

### 8.3 Offene Aufträge (orders) - Für Dashboard

```sql
-- Offene Werkstattaufträge mit Fahrzeugdaten
SELECT
    o.number as auftrag_nr,
    o.order_date,
    o.order_mileage as km_stand,
    o.subsidiary as betrieb,
    v.license_plate as kennzeichen,
    v.brand as marke,
    v.model_name as modell,
    c.first_name || ' ' || c.family_name as kunde
FROM orders o
LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
LEFT JOIN customers_suppliers c ON o.order_customer = c.customer_number
WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
  AND o.invoice_number IS NULL  -- Noch nicht abgerechnet
ORDER BY o.order_date DESC;
```

### 8.4 Produktivität (times + labours) - Für Controlling

```sql
-- Produktivität pro Mechaniker
SELECT
    eh.name as mechaniker,
    SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time))/3600) as ist_stunden,
    SUM(l.time_should) as soll_stunden,
    ROUND(
        (SUM(l.time_should) / NULLIF(SUM(EXTRACT(EPOCH FROM (t.end_time - t.start_time))/3600), 0)) * 100,
        1
    ) as produktivitaet_pct
FROM times t
JOIN employees_history eh ON t.employee_number = eh.employee_number
LEFT JOIN labours l ON t.order_number = l.order_number
WHERE t.type = 2
  AND t.end_time IS NOT NULL
  AND DATE(t.start_time) = CURRENT_DATE
GROUP BY eh.name
ORDER BY produktivitaet_pct DESC;
```

### 8.5 Abwesenheiten (absence_calendar) - Für Kapazität

```sql
-- Abwesenheiten für Kapazitätsberechnung
SELECT
    ac.employee_number,
    eh.name,
    ac.date_from,
    ac.date_to,
    ac.absence_type,
    ac.hours_per_day
FROM absence_calendar ac
JOIN employees_history eh ON ac.employee_number = eh.employee_number
WHERE ac.date_from <= CURRENT_DATE + INTERVAL '14 days'
  AND ac.date_to >= CURRENT_DATE;
```

### 8.6 Kombinationsstrategie: PostgreSQL + SOAP

| Anwendungsfall | Beste Quelle | Begründung |
|----------------|--------------|------------|
| **Aktive Stempelungen** | PostgreSQL | Echtzeit, < 100ms |
| **Auftragsliste (Bulk)** | PostgreSQL | Performant für viele Datensätze |
| **Teile-Stammdaten** | PostgreSQL | 1.9M Zeilen, SOAP zu langsam |
| **Termin anlegen** | SOAP | Schreiboperation |
| **Kapazitäten** | SOAP | listAvailableTimes optimiert |
| **Auftrag anlegen** | SOAP | writeWorkOrderDetails |
| **Einzelner Auftrag** | SOAP | readWorkOrderDetails für Details |
| **Ersatzwagen** | SOAP | rentalCar in Appointment |

### 8.7 Hybride Architektur für Werkstattplanung

```
┌─────────────────────────────────────────────────────────────┐
│                    DRIVE Werkstattplanung                    │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  PostgreSQL     │  │  SOAP API       │  │  SQLite         │
│  (READ-Heavy)   │  │  (WRITE + Read) │  │  (DRIVE-intern) │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • Stempelungen  │  │ • Termine       │  │ • Urlaubsplaner │
│ • Auftragsliste │  │ • Kapazitäten   │  │ • ML-Modelle    │
│ • Teile-Stamm   │  │ • Ersatzwagen   │  │ • Konfiguration │
│ • Abwesenheiten │  │ • Aufträge (CUD)│  │ • User-Prefs    │
│ • Rechnungen    │  │ • Kunden (CUD)  │  │                 │
│ • Mitarbeiter   │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
     ~10ms                ~200ms              ~1ms
```

**Strategie:**
- PostgreSQL für alles was LESEN & SCHNELL sein muss
- SOAP für alles was SCHREIBEN & LOCOSOFT-NATIVE sein muss
- SQLite für DRIVE-eigene Daten

---

## 9. Bestehende DRIVE-Module und Synergien

### 9.1 Aktuelle DRIVE-Modulstruktur

```
DRIVE Portal (Aktueller Stand)
├── 📊 CONTROLLING
│   ├── Dashboard - Finanzkennzahlen
│   ├── BWA - Betriebswirtschaftliche Auswertung (SKR51)
│   ├── TEK - Tägliche Erfolgskontrolle
│   ├── Zinsen-Analyse - Fahrzeugfinanzierungen
│   ├── Einkaufsfinanzierung
│   ├── Jahresprämie - Mitarbeiter-Prämien
│   └── Bankenspiegel
│       ├── Dashboard
│       ├── Kontenübersicht
│       ├── Transaktionen (MT940/PDF Import)
│       └── Fahrzeugfinanzierungen
│
├── 🚗 VERKAUF
│   ├── Auftragseingang (Locosoft PostgreSQL LIVE)
│   ├── Auslieferungen (Locosoft PostgreSQL LIVE)
│   ├── Leasys Programmfinder
│   └── Leasys Kalkulator
│
├── 🏖️ URLAUBSPLANER
│   ├── Mein Urlaub V2 - Antragsstellung
│   ├── Chef-Übersicht - Team-Abwesenheiten
│   └── Administration - HR-Einstellungen
│
└── 🔧 AFTER SALES
    ├── Controlling
    │   └── Serviceberater Controlling (SOAP!)
    ├── Teile
    │   ├── Teile-Status
    │   ├── Teilebestellungen (PostgreSQL)
    │   └── Preisradar (1.9M Teile!)
    ├── DRIVE Intelligence
    │   ├── Morgen-Briefing (Gudat + SOAP)
    │   ├── Kulanz-Monitor
    │   └── ML-Kapazität (Machine Learning Prognose!)
    └── Werkstatt
        ├── Kapazitätsplanung (SOAP!)
        ├── Cockpit (Gudat + SOAP)
        ├── Aufträge & Prognose
        ├── Monitor (TV-Display)
        ├── Leistungsübersicht
        ├── Stempeluhr
        ├── Tagesbericht
        └── Live-Board (TAG 125-127)
```

### 9.2 Synergie-Matrix: Neue Werkstattplanung + Bestehende Module

| Bestehendes Modul | Synergie mit Werkstattplanung | Datenfluss |
|-------------------|-------------------------------|------------|
| **Urlaubsplaner** | ⭐⭐⭐ HOCH | Abwesenheiten → Kapazitätsberechnung |
| **ML-Kapazität** | ⭐⭐⭐ HOCH | ML-Prognose → Terminvorschläge |
| **Morgen-Briefing** | ⭐⭐⭐ HOCH | Termine/Aufträge → Tagesbericht |
| **Serviceberater Controlling** | ⭐⭐ MITTEL | Aufträge → Performance-KPIs |
| **Teile-Status** | ⭐⭐ MITTEL | Teileverfügbarkeit → Terminplanung |
| **Live-Board** | ⭐⭐⭐ HOCH | Disposition → Echtzeit-Anzeige |
| **Stempeluhr** | ⭐⭐⭐ HOCH | Stempelungen → Auftragsstatus |
| **Kulanz-Monitor** | ⭐ GERING | Kulanz-Aufträge als Spezialfall |
| **Verkauf** | ⭐⭐ MITTEL | Auslieferungstermine koordinieren |

### 9.3 Integrationskonzept: DRIVE als Zentrale

```
                    ┌─────────────────────────────────┐
                    │       DRIVE PORTAL              │
                    │   (Zentrale Werkstatt-GUI)      │
                    └─────────────┬───────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌───────────────┐
│   LOCOSOFT    │       │     DRIVE       │       │   EXTERNE     │
│   (Backend)   │       │  Intelligence   │       │   SYSTEME     │
├───────────────┤       ├─────────────────┤       ├───────────────┤
│ • SOAP API    │       │ • ML-Kapazität  │       │ • Leasys API  │
│ • PostgreSQL  │       │ • Urlaubsplaner │       │ • ServiceBox  │
│               │       │ • Stempeluhr    │       │ • Schäferbarth│
│ Termine       │       │                 │       │               │
│ Aufträge      │       │ Prognosen       │       │ Externe Daten │
│ Kunden        │       │ Abwesenheiten   │       │               │
│ Fahrzeuge     │       │ Produktivität   │       │               │
│ Ersatzwagen   │       │                 │       │               │
└───────┬───────┘       └────────┬────────┘       └───────────────┘
        │                        │
        └────────────┬───────────┘
                     ▼
            ┌────────────────────┐
            │  Werkstattplanung  │
            │   (Neue Module)    │
            ├────────────────────┤
            │ • Terminplaner     │
            │ • Planungstafel    │
            │ • Online-Buchung   │
            │ • Ersatzwagen-UI   │
            │ • Live-Dashboard   │
            └────────────────────┘
```

### 9.4 Konkrete Synergien im Detail

#### 🏖️ Urlaubsplaner → Kapazitätsplanung

**Aktuell:**
- Urlaubsplaner speichert Abwesenheiten in SQLite
- Locosoft hat eigenen Abwesenheitskalender (PostgreSQL)

**Mit Werkstattplanung:**
```python
def berechne_kapazitaet(datum, arbeitsgruppe):
    # 1. Basis-Kapazität aus SOAP
    basis = soap.listAvailableTimes(arbeitsgruppe, datum, datum)

    # 2. DRIVE-Abwesenheiten dazurechnen
    drive_urlaub = db.query("""
        SELECT SUM(hours) FROM vacation_bookings
        WHERE date = ? AND department = ?
    """, [datum, arbeitsgruppe])

    # 3. Korrigierte Kapazität
    return basis.timeAvailable - drive_urlaub
```

**Vorteil:** Urlaub in DRIVE beantragt → sofort in Kapazitätsplanung sichtbar!

---

#### 🤖 ML-Kapazität → Intelligente Terminvorschläge

**Aktuell:**
- ML-Modell prognostiziert Auslastung basierend auf historischen Daten
- Modell trainiert auf `werkstatt_auftraege_abgerechnet`

**Mit Werkstattplanung:**
```python
def empfehle_termin(service_art, dauer_aw):
    # ML-Prognose für nächste 14 Tage
    prognosen = ml_model.predict_auslastung(days=14)

    # Finde Tage mit < 80% Auslastung
    gute_tage = [p for p in prognosen if p.auslastung < 0.8]

    # SOAP: Verfügbare Slots an diesen Tagen
    for tag in gute_tage:
        slots = soap.listAvailableTimes(tag)
        if slots.timeAvailable >= dauer_aw:
            return tag, slots
```

**Vorteil:** Kunde bekommt automatisch den optimalen Termin vorgeschlagen!

---

#### 📋 Morgen-Briefing → Tagesplanung

**Aktuell:**
- Morgen-Briefing zeigt heutige Termine aus Gudat
- Kapazitäten aus Gudat-API

**Mit Werkstattplanung:**
```python
def morgen_briefing(datum):
    # Direkt aus SOAP statt Gudat
    termine = soap.listAppointmentsByDate(datum, datum + 1 Tag)
    auftraege = soap.listOpenWorkOrders()
    kapazitaet = soap.listAvailableTimes(datum, datum + 7 Tage)

    # Plus DRIVE-Intelligence
    ml_prognose = ml_model.predict(datum)
    abwesenheiten = urlaubsplaner.get_abwesenheiten(datum)

    return {
        'termine': termine,
        'auftraege': auftraege,
        'kapazitaet': kapazitaet,
        'prognose': ml_prognose,
        'abwesenheiten': abwesenheiten
    }
```

**Vorteil:** Alles aus einer Quelle, keine Gudat-Abhängigkeit mehr!

---

#### 🔧 Live-Board → Echtzeit-Disposition

**Aktuell (TAG 125-127):**
- Live-Board zeigt Mechaniker-Karten
- Gudat für Disposition, Locosoft für Stempelungen

**Mit Werkstattplanung:**
```python
def live_board_daten():
    # Aktive Stempelungen aus PostgreSQL (schnell!)
    aktive = locosoft_pg.query("""
        SELECT mechaniker, auftrag, kennzeichen, start_time
        FROM times WHERE end_time IS NULL
    """)

    # Geplante Aufträge aus SOAP
    geplant = soap.listOpenWorkOrders()

    # Mechaniker-Zuweisung aus Aufträgen
    for auftrag in geplant:
        details = soap.readWorkOrderDetails(auftrag.number)
        for labor in details.line.labor:
            if labor.mechanicId:
                # Dieser Mechaniker ist diesem Auftrag zugewiesen
                pass
```

**Vorteil:** Komplette Disposition in DRIVE, kein Gudat nötig!

---

#### ⏱️ Stempeluhr → Automatisches Status-Update

**Aktuell:**
- Stempeluhr bucht Zeiten via `writeWorkOrderTimes`
- Status-Update manuell

**Mit Werkstattplanung:**
```python
def stempel_ein(mechaniker_id, auftrag_nr):
    # 1. Stempelung in Locosoft
    soap.writeWorkOrderTimes({
        'workOrderNumber': auftrag_nr,
        'mechanicId': mechaniker_id,
        'startTimestamp': datetime.now()
    })

    # 2. Automatisch Status auf "In Arbeit"
    soap.writeAppointment({
        'workOrderNumber': auftrag_nr,
        'inProgress': 1,
        'vehicleStatus': 2  # "In Bearbeitung"
    })

    # 3. Live-Board aktualisieren (WebSocket)
    notify_live_board('auftrag_gestartet', auftrag_nr)
```

**Vorteil:** Stempeln → Status überall sofort aktuell!

---

#### 🛒 Teile-Status → Terminverschiebung

**Mit Werkstattplanung:**
```python
def pruefe_teile_fuer_termin(termin_id):
    termin = soap.readAppointment(termin_id)
    auftrag = soap.readWorkOrderDetails(termin.workOrderNumber)

    for line in auftrag.line:
        for teil in line.part:
            verfuegbar = soap.readPartInformation(teil.number)
            if verfuegbar.quantityStock < teil.quantity:
                return {
                    'status': 'TEILE_FEHLEN',
                    'teil': teil.number,
                    'benoetigt': teil.quantity,
                    'lager': verfuegbar.quantityStock,
                    'empfehlung': 'Termin verschieben oder Teile bestellen'
                }

    return {'status': 'OK'}
```

**Vorteil:** Bei Terminanlage automatisch Teile-Check!

---

### 9.5 Erweiterte Roadmap mit Modul-Integration

| Phase | Modul | Integration mit |
|-------|-------|-----------------|
| **1** | SOAP Client Basis | - |
| **2** | Terminplaner | Urlaubsplaner (Abwesenheiten) |
| **3** | Online-Buchung | ML-Kapazität (Terminvorschläge) |
| **4** | Planungstafel | Live-Board, Stempeluhr |
| **5** | Dashboard | Morgen-Briefing, alle Module |
| **6** | Ersatzwagen | Teile-Status (wenn relevant) |

### 9.6 Vision: DRIVE als zentrales Werkstatt-Cockpit

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DRIVE WERKSTATT-COCKPIT                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │
│  │ 📅 TERMINE     │ │ 👥 DISPOSITION │ │ 📊 AUSLASTUNG  │            │
│  │ Kalender       │ │ Drag & Drop    │ │ ML-Prognose    │            │
│  │ Online-Buchung │ │ Mechaniker     │ │ Kapazitäten    │            │
│  └────────────────┘ └────────────────┘ └────────────────┘            │
│                                                                       │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │
│  │ 🚗 ERSATZWAGEN │ │ ⏱️ STEMPELUHR  │ │ 📦 TEILE       │            │
│  │ Pool-Verwaltung│ │ Ein/Aus        │ │ Verfügbarkeit  │            │
│  │ Zuweisung      │ │ Auto-Status    │ │ Bestellung     │            │
│  └────────────────┘ └────────────────┘ └────────────────┘            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 📺 LIVE-BOARD (Werkstatt-TV)                                   │  │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │  │
│  │ │ Huber  │ │ Schmidt│ │ Wagner │ │ Müller │ │ Unverpl│        │  │
│  │ │DEG-AB  │ │DEG-CD  │ │[URLAUB]│ │DEG-GH  │ │2 Auftr.│        │  │
│  │ │🔵 45min│ │🔵 20min│ │        │ │⚪ wartet│ │        │        │  │
│  │ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────┐ ┌─────────────────────────────────┐ │
│  │ 🏖️ ABWESENHEITEN HEUTE     │ │ 📈 KPIs                         │ │
│  │ • Wagner: Urlaub           │ │ Produktivität: 87%              │ │
│  │ • Suttner: Schulung        │ │ Auslastung: 78%                 │ │
│  └─────────────────────────────┘ │ Durchlaufzeit: 4.2h            │ │
│                                  └─────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10. Zusammenfassung: Was macht DRIVE besser als Gudat?

| Aspekt | Gudat | DRIVE (mit SOAP) |
|--------|-------|------------------|
| **Single Source of Truth** | Nein (eigene DB + Locosoft) | ✅ Ja (alles aus Locosoft) |
| **Urlaubsintegration** | Nein | ✅ Ja (Urlaubsplaner-Modul) |
| **ML-Prognosen** | Nein | ✅ Ja (ML-Kapazität) |
| **Controlling-Integration** | Nein | ✅ Ja (Serviceberater, TEK) |
| **Teile-Verfügbarkeit** | Nein | ✅ Ja (SOAP readPartInformation) |
| **Stempeluhr-Sync** | Extern | ✅ Integriert |
| **Bankenspiegel-Link** | Nein | ✅ Möglich (Aufträge → Umsatz) |
| **Customizing** | Begrenzt | ✅ Voll (eigene Entwicklung) |

---

*Analyse erstellt: 2025-12-19 (TAG 129)*
