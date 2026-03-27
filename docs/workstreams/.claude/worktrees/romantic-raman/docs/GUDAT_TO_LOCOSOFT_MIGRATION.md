# Gudat → Locosoft Migration Plan

**Erstellt:** 2026-01-02 (TAG 153)
**Ziel:** Gudat durch DRIVE Werkstattplaner ersetzen, Locosoft als Single Source of Truth

---

## Executive Summary

**Aktueller Stand:**
- Gudat ist Dispositionssystem für Werkstatt
- DRIVE nutzt Gudat + Locosoft parallel (Komplexität!)
- Name-Matching zwischen Systemen fehleranfällig

**Ziel-Architektur:**
- Locosoft SOAP API als einzige Datenquelle
- DRIVE als moderne UI mit Drag & Drop
- Kein Gudat mehr

**Zeitrahmen:** 11-14 Wochen (siehe Machbarkeitsstudie)

---

## Phase 0: Abstraktion (TAG 153) ✅

### Erledigt

1. **gudat_data.py erstellt** - Alle Gudat-Zugriffe gekapselt
   - `GudatData.get_disposition()` - Zentrale Funktion
   - `GudatData.match_mechaniker_name()` - Name-Mapping
   - `GudatData.merge_zeitbloecke()` - Zeitblock-Integration
   - `GudatData.create_mechaniker_mapping()` - Locosoft ↔ Gudat

2. **Architektur-Hinweise** in Code dokumentiert
   - Jede Methode hat MIGRATION-NOTE
   - Zeigt was bei Locosoft SOAP anders wird

### Nächste Schritte

- [ ] werkstatt_live_api.py refaktorieren (nutzt gudat_data.py)
- [ ] get_werkstatt_liveboard() vereinfachen
- [ ] Tests für GudatData schreiben

---

## Phase 1: Locosoft SOAP Client (2-3 Wochen)

### Aufgaben

1. **locosoft_soap_client.py erstellen**
   ```python
   class LocosoftSOAPClient:
       def list_appointments_by_date(self, date_from, date_to)
       def list_available_times(self, work_group, date_from, date_to)
       def list_open_work_orders(self)
       def read_work_order_details(self, order_number)
       def write_appointment(self, appointment_data)
       def write_work_order_details(self, order_data)
       def list_changes(self, since_timestamp)
   ```

2. **Credentials & Config**
   - SOAP URL: `http://10.80.80.7:8086/?wsdl`
   - Auth: `9001` / `Max2024`
   - Header: `locosoftinterface: GENE-AUTO`, `locosoftinterfaceversion: 2.2`

3. **Caching-Layer**
   - Redis oder Memory-Cache für häufige Abfragen
   - `list_changes` für Invalidierung

### Deliverables
- [ ] locosoft_soap_client.py
- [ ] Basis-Tests für alle Operationen
- [ ] Config in `/config/locosoft_soap.json`

---

## Phase 2: Disposition Migration (2-3 Wochen)

### Ziel
`GudatData.get_disposition()` durch Locosoft SOAP ersetzen.

### Mapping Gudat → Locosoft

| Gudat-Feld | Locosoft SOAP | Quelle |
|------------|---------------|--------|
| `resource.name` | `labor.mechanicId` + Name | `readWorkOrderDetails` |
| `start_date` | Berechnet aus `bringDateTime` | `readAppointment` |
| `work_load` | `labor.time` | `readWorkOrderDetails` |
| `work_state` | `inProgress`, `vehicleStatus` | `readAppointment` |
| `license_plate` | `vehicle.licensePlate` | `readAppointment` |
| `orders.number` | `workOrderNumber` | `readAppointment` |

### Implementierung

```python
# locosoft_disposition.py (ersetzt gudat_data.py)

class LocosoftDisposition:
    @classmethod
    def get_disposition(cls, target_date: date) -> Dict[int, List[Dict]]:
        """
        Holt Disposition direkt aus Locosoft.

        Returns:
            {employee_number: [tasks]}  # Kein Name-Matching mehr nötig!
        """
        # 1. Offene Aufträge holen
        orders = soap.list_open_work_orders()

        # 2. Details für jeden Auftrag
        disposition = {}
        for order in orders:
            details = soap.read_work_order_details(order.number)
            for labor in details.labors:
                mech_id = labor.mechanicId
                if mech_id:
                    if mech_id not in disposition:
                        disposition[mech_id] = []
                    disposition[mech_id].append({
                        'auftrag_nr': order.number,
                        'vorgabe_aw': labor.time,
                        'kennzeichen': order.vehicle.licensePlate,
                        # ... weitere Felder
                    })

        return disposition
```

### Vorteile
- **Kein Name-Matching** mehr (employee_number = mechanicId)
- **Echte Zuweisung** statt Gudat-Planung
- **Single Source of Truth**

---

## Phase 3: UI-Komponenten (3-4 Wochen)

### Planungstafel (Drag & Drop)

```
┌────────────────────────────────────────────────────────────┐
│  DRIVE Werkstatt-Disposition                                │
├────────────────────────────────────────────────────────────┤
│ Mechaniker │ 08:00 │ 09:00 │ 10:00 │ 11:00 │ 12:00       │
├────────────┼───────┴───────┼───────┴───────┼──────────────┤
│ Huber      │ ██ DEG-AB 123 │ ██████████████ DEG-XY 999   │
│            │   Inspektion  │     Getriebe (4h)           │
├────────────┼───────────────┼───────────────┼──────────────┤
│ Schmidt    │ ████ DEG-CD   │ ████████ DEG-EF             │
│            │ Reifen (1.5h) │ Bremsen (2h)  │             │
├────────────┼───────────────┴───────────────┴──────────────┤
│ Unverplant │ 🚗 LAN-GH 111 (TÜV) - 1h                    │
│            │ 🚗 DEG-IJ 222 (Klima) - 2h                   │
└────────────┴──────────────────────────────────────────────┘
```

### Technologien
- **Frontend:** FullCalendar.js oder ähnlich für Drag & Drop
- **Backend:** Flask + WebSocket für Live-Updates
- **Sync:** `listChanges` alle 10 Sekunden

### API-Endpunkte

```python
# werkstatt_disposition_api.py (NEU)

@bp.route('/api/werkstatt/disposition', methods=['GET'])
def get_disposition():
    """Aktuelle Disposition für Planungstafel"""

@bp.route('/api/werkstatt/disposition/assign', methods=['POST'])
def assign_mechaniker():
    """Mechaniker einem Auftrag zuweisen"""
    # -> writeWorkOrderDetails mit labor.mechanicId

@bp.route('/api/werkstatt/disposition/move', methods=['POST'])
def move_termin():
    """Termin verschieben (Drag & Drop)"""
    # -> writeAppointment mit neuem bringDateTime
```

---

## Phase 4: Gudat Ablösung (2 Wochen)

### Schritte

1. **Feature-Parity prüfen**
   - [ ] Alle Gudat-Features in DRIVE vorhanden?
   - [ ] User-Akzeptanz-Tests

2. **Parallelbetrieb**
   - DRIVE zeigt beide Quellen (Toggle)
   - Daten-Vergleich für Validation

3. **Gudat abschalten**
   - `GUDAT_AVAILABLE = False` setzen
   - GudatClient entfernen
   - gudat_data.py durch locosoft_disposition.py ersetzen

4. **Cleanup**
   - Alten Gudat-Code entfernen
   - Dokumentation aktualisieren

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| SOAP-Performance | Mittel | Aggressive Caching, Batch-Requests |
| User-Widerstand | Mittel | Frühe Einbindung, Training |
| Feature-Lücken | Gering | Detaillierte Analyse vorab |
| Locosoft-API-Änderung | Gering | API-Version pinnen |

---

## Dateien-Übersicht

### Aktuell (Phase 0)

```
api/
├── gudat_data.py          # NEU - Abstraktionsschicht
├── werkstatt_live_api.py  # Nutzt gudat_data.py (TODO: refactor)
├── werkstatt_data.py      # SSOT Werkstatt (15 Funktionen)
└── gudat_client.py        # Bestehendes Gudat-Login
```

### Ziel (Phase 4)

```
api/
├── locosoft_soap_client.py    # NEU - SOAP Client
├── locosoft_disposition.py    # Ersetzt gudat_data.py
├── werkstatt_live_api.py      # Nutzt locosoft_disposition.py
├── werkstatt_data.py          # SSOT Werkstatt
└── werkstatt_disposition_api.py # NEU - Disposition UI-API
```

---

## Referenzen

- [DRIVE_WERKSTATTPLANUNG_MACHBARKEITSSTUDIE.md](DRIVE_WERKSTATTPLANUNG_MACHBARKEITSSTUDIE.md)
- [GUDAT_VS_LOCOSOFT_SOAP_ANALYSE.md](GUDAT_VS_LOCOSOFT_SOAP_ANALYSE.md)
- [DATENMODUL_PATTERN.md](DATENMODUL_PATTERN.md)

---

*Erstellt: 2026-01-02 (TAG 153)*
*Nächstes Review: Nach Phase 1 Abschluss*
