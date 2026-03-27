# Gudat vs. Locosoft SOAP - Machbarkeitsanalyse

**Erstellt:** 2025-12-19 (TAG 129)
**Frage:** Kann DRIVE eine vollständige Terminplanung auf Basis Locosoft Programm 266 (SOAP) umsetzen und Gudat ersetzen?

---

## Executive Summary

**Kurze Antwort:** Nein, nicht vollständig. Aber ca. 70% der Gudat-Funktionen könnten mit SOAP + eigenem Frontend nachgebaut werden.

| Aspekt | Gudat | Locosoft SOAP | Lücke |
|--------|-------|---------------|-------|
| Termine lesen | ✅ | ✅ | - |
| Termine anlegen | ✅ | ✅ (v2.2) | - |
| Kapazitäten | ✅ | ✅ listAvailableTimes | - |
| Task-Disposition | ✅ | ❌ | **KRITISCH** |
| Real-time Status | ✅ | ❌ | **KRITISCH** |
| Drag & Drop UI | ✅ | ❌ (müsste gebaut werden) | Aufwand |
| Externe Teams | ✅ | ❌ | Nur intern |

---

## 1. Was Gudat "Digitales Autohaus" bietet

### 1.1 Kapazitätsplanung
```
GET /api/v1/workload_week_summary?date=YYYY-MM-DD&days=14

- 16 Teams mit Kapazitäten (AW = Arbeitswerte)
- base_workload: Grundkapazität
- planned_workload: Bereits geplant
- absence_workload: Abwesenheiten
- free_workload: Noch verfügbar
- Produktivitätsfaktoren pro Team
```

### 1.2 Team-Struktur
| ID | Kategorie | Name |
|----|-----------|------|
| 2 | Mechanik | Allgemeine Reparatur |
| 3 | Mechanik | Diagnosetechnik |
| 4 | Mechanik | Qualitätsmanagement |
| 5 | Mechanik | NW/GW |
| 6 | Mechanik | TÜV/AU (Dekra) |
| 11 | Mechanik | TÜV/AU |
| 16 | Mechanik | Hauptuntersuchung |
| 7-10, 12-15 | Externe | Aufbereitung, Smart Repair, etc. |

### 1.3 WorkshopTasks (Disposition)
```graphql
workshopTasks {
  id
  start_date          # Geplante Startzeit
  work_load           # AW-Vorgabe
  work_state          # NEW, IN_WORK, PAUSED, DONE
  description
  workshopService     # Service-Art
  resource {          # Zugewiesener Mechaniker
    id, name
  }
  dossier {
    vehicle { license_plate }
    orders { number }  # ← Locosoft-Verknüpfung!
  }
}
```

**Zentrale Funktion:** Wer arbeitet wann an welchem Fahrzeug.

### 1.4 Appointments (Termine)
```graphql
appointments {
  id
  start_date_time
  end_date_time
  type               # service, customer_bring, finish_pickup, other
  dossier {
    vehicle { license_plate }
    orders { number }
    states { name }   # Vorgangsstatus
  }
}
```

### 1.5 Dossiers (Vorgänge)
- Klammer um Fahrzeug + Kunde + Aufträge + Termine
- Stati-Management (Vorgangs-Workflow)
- Tags für Kategorisierung

### 1.6 UI-Features
- Drag & Drop Planungstafel
- Mechaniker-Kalender
- Echtzeit-Updates (WebSocket?)
- Farb-Coding nach Status
- Mobile-App für Mechaniker

---

## 2. Was Locosoft SOAP (Programm 266) bietet

### 2.1 READ-Operationen (alle funktionieren)
```python
# Stammdaten
listWorkshops()          # 3 Werkstätten (ID 1, 2, 3)
listWorkGroups()         # 18 Arbeitsgruppen
listLaborRates()         # Stundensätze (119€, 125€, 140€...)
listSparePartTypes()     # Teilearten

# Kunden & Fahrzeuge
listCustomers(name/tel/nr/email)
listVehicles(kennzeichen/VIN)
listCustomerVehicles(customer_id)
readCustomer(nr)
readVehicle(nr)

# Aufträge & Termine
listOpenWorkOrders()     # Offene Aufträge
readWorkOrderDetails(nr)
readAppointment(nr)
listAvailableTimes(workGroupId, dateFrom, dateTo)  # Kapazitäten!
listCustomerInvoices()
```

### 2.2 WRITE-Operationen
```python
# Ohne v2.2 Header
writeWorkOrderDetails()  # Auftrag erstellen/ändern
writeWorkOrderTimes()    # Arbeitszeiten buchen
writeWorkTimes()         # Stempelzeiten
writeCustomerDetails()
writeVehicleDetails()
writePotential()

# MIT v2.2 Header (locosoftinterface: GENE-AUTO, locosoftinterfaceversion: 2.2)
writeAppointment()       # Termine anlegen/ändern ✅
writeAppointmentNotification()
```

### 2.3 Kapazitätsabfrage (entspricht Gudat-Workload)
```xml
<soap:listAvailableTimes>
  <workGroupId>MON</workGroupId>
  <dateFrom>2025-12-20</dateFrom>
  <dateTo>2025-12-27</dateTo>
</soap:listAvailableTimes>

Response:
- date: Datum
- timeShould: Soll-Kapazität
- timeCan: Kann-Kapazität
- timeAvailable: Noch frei
```

---

## 3. Feature-Matrix: Was fehlt für Gudat-Ersatz?

### ✅ Mit SOAP machbar

| Feature | SOAP-Operation | Kommentar |
|---------|----------------|-----------|
| Termine anlegen | writeAppointment (v2.2) | Funktioniert! |
| Termine lesen | readAppointment | ✅ |
| Kapazitäten abfragen | listAvailableTimes | Pro Arbeitsgruppe |
| Arbeitsgruppen | listWorkGroups | 18 Gruppen |
| Offene Aufträge | listOpenWorkOrders | Live-Liste |
| Auftrag anlegen | writeWorkOrderDetails | ✅ |
| Zeiten buchen | writeWorkOrderTimes | ✅ |
| Kunden suchen | listCustomers | Nach Name, Tel, Nr |
| Fahrzeuge suchen | listVehicles | Kennzeichen, VIN |

### ❌ Fehlt komplett in SOAP

| Feature | Gudat-Funktion | Alternative |
|---------|----------------|-------------|
| **Task-Disposition** | workshopTasks | ❌ KEINE |
| **Mechaniker-Zuweisung** | resource.name | Nur in Locosoft-UI |
| **Echtzeit-Status** | work_state | Müsste selbst gebaut werden |
| **Externe Teams** | Teams 7-15 | Nicht in Locosoft |
| **Drag & Drop** | UI | Müsste gebaut werden |
| **Produktivitätsfaktoren** | team_productivity_factor | Nicht verfügbar |
| **Abwesenheits-Integration** | absence_workload | Nur manuell |

### 🟡 Teilweise machbar

| Feature | Status | Aufwand |
|---------|--------|---------|
| Planungstafel | Kann gebaut werden | Hoch (Frontend) |
| Status-Tracking | In eigener DB | Mittel |
| Mechaniker-Liste | Aus PostgreSQL | Gering |

---

## 4. Der kritische Gap: WorkshopTask-Disposition

**Gudat's Kernfunktion:**
- Ein "WorkshopTask" ist die kleinste planbare Einheit
- Hat: Mechaniker-Zuweisung, Startzeit, AW-Vorgabe, Status
- Ermöglicht: "Herr Müller macht um 10:30 den Bremsenwechsel an DEG-AB-123"

**Locosoft SOAP kennt nur:**
- Auftrag (grob)
- Termin (Kunde bringt/holt)
- Arbeitsgruppe (z.B. "MON" = Montage)

**Es gibt KEINE SOAP-Operation für:**
- Mechaniker einem Auftrag zuweisen
- Task-Status setzen (IN_WORK, PAUSED, DONE)
- Feinplanung (Startzeit innerhalb Tag)

**Das ist in Locosoft Programm 266 die UI-Funktion!**

---

## 5. Was wäre der Aufwand für einen Gudat-Ersatz?

### 5.1 Minimum Viable Product (MVP)

**Nur mit SOAP machbar:**
1. ✅ Termin-Buchung für Kunden
2. ✅ Kapazitäts-Anzeige pro Arbeitsgruppe
3. ✅ Auftrags-Anlage
4. ✅ Übersicht offener Aufträge

**Geschätzter Aufwand:** 2-3 Wochen

### 5.2 Vollständige Terminplanung (wie Gudat)

**Zusätzlich nötig:**
1. ❌ Eigene Disposition-Datenbank
2. ❌ Mechaniker-Zuweisungs-Logik
3. ❌ Drag & Drop Planungstafel (React/Vue)
4. ❌ WebSocket für Echtzeit-Updates
5. ❌ Status-Workflow-Engine
6. ❌ Integration externe Teams

**Geschätzter Aufwand:** 3-6 Monate Vollzeit-Entwicklung

### 5.3 Hybrid-Ansatz (Empfehlung)

**Gudat für:**
- Disposition (wer macht was wann)
- Mechaniker-Kalender
- Status-Tracking
- Externe Teams

**DRIVE + SOAP für:**
- Kundenseitige Termin-Buchung (Online-Terminbuchung)
- Kapazitäts-Dashboard für Management
- Auftrags-Anlage aus Portal
- Direkter Datenabgleich Locosoft ↔ Portal

---

## 6. Empfehlung

### Gudat NICHT ersetzen, sondern:

1. **SOAP für Read-Operationen nutzen**
   - Kapazitäten in DRIVE anzeigen (listAvailableTimes)
   - Offene Aufträge live (listOpenWorkOrders)
   - Termindetails (readAppointment)

2. **SOAP für Write-Operationen nutzen**
   - Online-Terminbuchung (writeAppointment v2.2)
   - Auftrag aus Portal anlegen (writeWorkOrderDetails)
   - Zeiten aus Portal buchen (writeWorkOrderTimes)

3. **Gudat für Disposition behalten**
   - WorkshopTask-Management
   - Mechaniker-Zuweisung
   - Echtzeit-Status

4. **Sync Locosoft ↔ Gudat verbessern**
   - POC existiert bereits (poc_locosoft_gudat_sync_v2.py)
   - Status-Abgleich automatisieren
   - Stempelungen → Gudat-Status

---

## 7. Quick Wins mit SOAP (Sofort umsetzbar)

| Feature | Nutzen | Aufwand |
|---------|--------|---------|
| Online-Terminbuchung | Kunden buchen selbst | 1 Woche |
| Kapazitäts-Widget | Management sieht Auslastung | 2 Tage |
| Auftrags-Anlage aus Portal | Service-Berater spart Zeit | 1 Woche |
| Live-Auftragsstatus im Portal | Kunde sieht Fortschritt | 3 Tage |

---

## 8. Fazit

**Gudat ersetzen = Vermessen** ✅ (User hat recht)

Gudat ist ein spezialisiertes Werkstattplanungs-System mit:
- 10+ Jahren Entwicklung
- Komplexer Disposition
- Mobile Apps
- Integration externer Dienstleister

**DRIVE + SOAP kann ergänzen**, aber nicht ersetzen:
- Online-Terminbuchung (Kundenportal)
- Management-Dashboards
- Automatische Auftrags-Anlage
- Daten-Brücke zu anderen Systemen

**Die Stärke liegt in der Kombination:**
- Gudat für Werkstatt-intern
- DRIVE für Kunden-extern & Management
- SOAP als Daten-Brücke

---

*Analyse erstellt: 2025-12-19*
