# TODO FOR CLAUDE - SESSION START TAG 154

**Letzte Session:** TAG 153 (2026-01-02)
**Ziel:** Werkstatt-Migration abschließen ODER Locosoft SOAP starten

---

## KONTEXT

TAG 153 hat die Gudat-Abstraktionsschicht erstellt:
- gudat_data.py (481 LOC) mit GudatData-Klasse
- Migrations-Dokumentation erstellt
- werkstatt_live_api.py auf 2,609 LOC reduziert (-53% seit TAG 148)

**Aktueller Stand:**
- werkstatt_live_api.py: 2,609 LOC (Ziel: < 2,500)
- gudat_data.py: 481 LOC (NEU)
- **Reduktion seit TAG 148: -53%**

---

## AUFGABEN TAG 154

### Option A: Werkstatt-Migration abschließen

Noch ~109 LOC für Ziel < 2,500 LOC.

Kandidaten für weitere Auslagerung:
```
match_gudat_name()           - ~35 LOC, schon in gudat_data.py vorhanden
Gudat-Merge-Logik im Liveboard - ~80 LOC, schon in gudat_data.py vorhanden
```

**Empfehlung:** Liveboard-Gudat-Logik durch GudatData ersetzen.

### Option B: Locosoft SOAP Client starten

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

### Option C: teile_data.py starten

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

---

## WICHTIGE DATEIEN

```
api/gudat_data.py           - Gudat-Abstraktionsschicht (481 LOC)
api/werkstatt_data.py       - SSOT Werkstatt (3,413 LOC, 15 Funktionen)
api/werkstatt_live_api.py   - API-Endpoints (2,609 LOC, Ziel: <2,500)

docs/GUDAT_TO_LOCOSOFT_MIGRATION.md - Migrationsplan
docs/DRIVE_WERKSTATTPLANUNG_MACHBARKEITSSTUDIE.md - Analyse
```

---

## GUDAT → LOCOSOFT MIGRATION

**Phase 0: Abstraktion** ✅ (TAG 153)
- gudat_data.py erstellt
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
