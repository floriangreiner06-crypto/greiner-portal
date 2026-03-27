# TODO FOR CLAUDE - SESSION START TAG 152

**Letzte Session:** TAG 151 (2026-01-02)
**Ziel:** Werkstatt-Migration fortsetzen + teile_data.py

---

## KONTEXT

TAG 151 hat 3 weitere Funktionen migriert:
- get_nachkalkulation()
- get_anwesenheit()
- get_heute_live()

**Aktueller Stand:**
- werkstatt_data.py: 2,833 LOC (11 Funktionen)
- werkstatt_live_api.py: 3,267 LOC (-41% seit TAG 148)

---

## AUFGABEN TAG 152

### 1. Weitere Funktionen migrieren

Noch zu migrieren aus werkstatt_live_api.py:
- get_auftraege_enriched() (~550 LOC, komplex: ML + Gudat)
- get_gudat_kapazitaet() (~100 LOC)
- get_anwesenheit_report() (~140 LOC, Legacy V1)
- get_kulanz_monitoring() (~170 LOC)
- get_drive_briefing() (~180 LOC)
- get_drive_kapazitaet() (~220 LOC)
- get_werkstatt_liveboard() (~560 LOC)
- get_forecast() (~350 LOC, ML-basiert)

**Ziel:** werkstatt_live_api.py < 2,500 LOC

### 2. Refactoring-Pattern

```bash
# 1. Funktion zu werkstatt_data.py hinzufuegen
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

### 3. Optional: teile_data.py starten

Neues Datenmodul fuer Teile/Aftersales:
- get_lagerbestand()
- get_umschlaghaeufigkeit()
- get_renner_penner()

**Consumer:** parts_api.py, teile_api.py, controlling_data.py

---

## WICHTIGE DATEIEN

```
api/werkstatt_data.py      - SSOT Werkstatt (2,833 LOC)
api/werkstatt_live_api.py  - API-Endpoints (3,267 LOC, Ziel: <2,500)
scripts/refactor_werkstatt_api.py - Refactoring-Script
docs/DATENMODUL_PATTERN.md - Pattern-Dokumentation
```

---

## MIGRIERTE FUNKTIONEN (11/~23)

| Funktion | TAG | LOC gespart |
|----------|-----|-------------|
| get_mechaniker_leistung() | 148 | ~200 |
| get_offene_auftraege() | 149 | ~150 |
| get_dashboard_stats() | 149 | ~100 |
| get_stempeluhr() | 149 | ~510 |
| get_kapazitaetsplanung() | 149 | ~150 |
| get_tagesbericht() | 150 | ~185 |
| get_auftrag_detail() | 150 | ~135 |
| get_problemfaelle() | 150 | ~170 |
| get_nachkalkulation() | 151 | ~262 |
| get_anwesenheit() | 151 | ~125 |
| get_heute_live() | 151 | ~300 |
| **GESAMT** | | **~2,287** |

---

*Erstellt: 2026-01-02*
