# TODO FOR CLAUDE - SESSION START TAG 153

**Letzte Session:** TAG 152 (2026-01-02)
**Ziel:** Werkstatt-Migration abschließen ODER teile_data.py starten

---

## KONTEXT

TAG 152 hat 2 DRIVE-Funktionen migriert:
- get_drive_briefing()
- get_drive_kapazitaet()

**Aktueller Stand:**
- werkstatt_data.py: 3,413 LOC (15 Funktionen)
- werkstatt_live_api.py: 2,711 LOC (Ziel: < 2,500)
- **Reduktion seit TAG 148: -51%**

---

## AUFGABEN TAG 153

### Option A: Werkstatt-Migration abschließen

Noch ~211 LOC zu reduzieren für Ziel < 2,500 LOC.

Verbleibende große Funktionen:
```
get_kapazitaets_forecast()  - ~560 LOC, Portal-DB Integration
get_auftraege_enriched()    - ~543 LOC, ML + Gudat (komplex!)
get_werkstatt_liveboard()   - ~560 LOC, Gantt-Ansicht
```

**Empfehlung:** get_werkstatt_liveboard() ist am isoliertesten.

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

---

## REFACTORING-PATTERN

```bash
# 1. Funktion zu werkstatt_data.py hinzufügen
# 2. Script aktualisieren: scripts/refactor_werkstatt_api.py
# 3. Deploy & Run:
ssh ag-admin@10.80.80.20
cp /mnt/greiner-portal-sync/api/werkstatt_data.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/scripts/refactor_werkstatt_api.py /opt/greiner-portal/scripts/
python3 /opt/greiner-portal/scripts/refactor_werkstatt_api.py
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal

# 4. Test:
curl -s 'http://localhost:5000/api/werkstatt/live/...' | jq '.source'
# Erwartetes Ergebnis: "LIVE_V2"
```

---

## WICHTIGE DATEIEN

```
api/werkstatt_data.py      - SSOT Werkstatt (3,413 LOC, 15 Funktionen)
api/werkstatt_live_api.py  - API-Endpoints (2,711 LOC, Ziel: <2,500)
scripts/refactor_werkstatt_api.py - Refactoring-Script
docs/DATENMODUL_PATTERN.md - Pattern-Dokumentation
```

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
- `order_number > 31` für echte Aufträge (31 = Leerlauf)

---

## MIGRIERTE FUNKTIONEN (15/~18)

| Funktion | TAG | Status |
|----------|-----|--------|
| get_mechaniker_leistung() | 148 | ✓ |
| get_offene_auftraege() | 149 | ✓ |
| get_dashboard_stats() | 149 | ✓ |
| get_stempeluhr() | 149 | ✓ |
| get_kapazitaetsplanung() | 149 | ✓ |
| get_tagesbericht() | 150 | ✓ |
| get_auftrag_detail() | 150 | ✓ |
| get_problemfaelle() | 150 | ✓ |
| get_nachkalkulation() | 151 | ✓ |
| get_anwesenheit() | 151 | ✓ |
| get_heute_live() | 151 | ✓ |
| get_anwesenheit_legacy() | 151 | ✓ |
| get_kulanz_monitoring() | 151 | ✓ |
| get_drive_briefing() | 152 | ✓ |
| get_drive_kapazitaet() | 152 | ✓ |
| get_kapazitaets_forecast() | - | TODO |
| get_auftraege_enriched() | - | TODO |
| get_werkstatt_liveboard() | - | TODO |

---

*Erstellt: 2026-01-02*
