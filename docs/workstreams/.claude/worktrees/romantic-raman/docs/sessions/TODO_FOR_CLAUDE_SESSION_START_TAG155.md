# TODO FOR CLAUDE - SESSION START TAG 155

**Letzte Session:** TAG 154 (2026-01-02)
**Ziel:** Werkstatt-Migration final abschließen ODER neues Modul starten

---

## KONTEXT

TAG 154 hat die Gudat-Kapazität migriert:
- get_gudat_kapazitaet() → GudatData.get_kapazitaet()
- werkstatt_live_api.py auf 2,535 LOC reduziert (-54% seit TAG 148)
- gudat_data.py auf 599 LOC erweitert

**Aktueller Stand:**
- werkstatt_live_api.py: 2,535 LOC (Ziel: < 2,500, noch -35 LOC)
- werkstatt_data.py: 3,413 LOC (15 Funktionen)
- gudat_data.py: 599 LOC (7 Methoden)
- **Reduktion seit TAG 148: -54%**

---

## AUFGABEN TAG 155

### Option A: Die letzten 35 LOC reduzieren

Kandidaten für weitere Reduktion:
```
match_gudat_name()           - ~35 LOC, schon in gudat_data.py vorhanden
Kleinere Helper-Funktionen   - konsolidieren
```

**Empfehlung:** match_gudat_name() durch GudatData.match_mechaniker_name() ersetzen.

### Option B: teile_data.py starten

Neues SSOT-Modul für Teile/Lager:
```python
class TeileData:
    @staticmethod
    def get_lagerbestand(...)
    @staticmethod
    def get_umschlaghaeufigkeit(...)
    @staticmethod
    def get_renner_penner(...)
```

**Consumer:** parts_api.py, teile_api.py, controlling_data.py

### Option C: Locosoft SOAP Client starten

Phase 1 der Gudat-Ablösung (siehe GUDAT_TO_LOCOSOFT_MIGRATION.md):

```python
# locosoft_soap_client.py
from zeep import Client

class LocosoftSOAPClient:
    WSDL_URL = 'http://10.80.80.7:8086/?wsdl'
    AUTH = ('9001', 'Max2024')

    def list_appointments_by_date(self, date_from, date_to)
    def list_available_times(self, work_group, date_from, date_to)
    def list_open_work_orders(self)
    def read_work_order_details(self, order_number)
```

---

## WICHTIGE DATEIEN

```
api/gudat_data.py           - Gudat-Abstraktionsschicht (599 LOC)
api/werkstatt_data.py       - SSOT Werkstatt (3,413 LOC, 15 Funktionen)
api/werkstatt_live_api.py   - API-Endpoints (2,535 LOC, Ziel: <2,500)

docs/GUDAT_TO_LOCOSOFT_MIGRATION.md - Migrationsplan
docs/DRIVE_WERKSTATTPLANUNG_MACHBARKEITSSTUDIE.md - Analyse
```

---

## GUDAT → LOCOSOFT MIGRATION

**Phase 0: Abstraktion** ✅ (TAG 153-154)
- gudat_data.py erstellt und erweitert
- Alle Gudat-Zugriffe gekapselt

**Phase 1: SOAP Client** (nächster Schritt)
- locosoft_soap_client.py erstellen
- Zeep-Bibliothek für SOAP

**Phase 2-4:** Disposition Migration, UI, Ablösung

---

## PORTAL URLs

Korrekte Domains:
- **https://portal.auto-greiner.de**
- **https://drive.auto-greiner.de**

NICHT `auto-greiner.de` direkt!

---

## LOCOSOFT-TABELLEN (WICHTIG!)

Korrekte Tabellennamen für Locosoft-DB:
- `times` (nicht workshop_times)
- `orders` (nicht jobs)
- `labours` (nicht labour_positions)
- `employees_history` (für Betrieb-Filter via JOIN)

Spalten in times:
- `start_time` (nicht work_start)
- `duration_minutes` (nicht duration)
- `order_number > 31` für echte Aufträge

---

*Erstellt: 2026-01-02*
