# TODO FOR CLAUDE - SESSION START TAG 150

**Letzte Session:** TAG 149 (2026-01-02)
**Ziel:** Werkstatt-Modularisierung abschließen + teile_data.py

---

## KONTEXT

TAG 149 hat 4 weitere Funktionen nach `werkstatt_data.py` migriert:
- get_offene_auftraege()
- get_dashboard_stats()
- get_stempeluhr() (komplexeste: 570 → 60 LOC)
- get_kapazitaetsplanung()

**Aktueller Stand:**
- werkstatt_live_api.py: 4,423 LOC (vorher 5,532)
- werkstatt_data.py: 1,457 LOC (vorher 509)
- Alle Tests erfolgreich (`source: LIVE_V2`)

---

## AUFGABEN TAG 150

### 1. Restliche werkstatt_live_api.py Funktionen (~17)

Noch zu migrieren:
- get_tagesbericht()
- get_auftrag_detail()
- get_problemfaelle()
- get_gudat_kapazitaet()
- get_forecast() (ML-basiert, komplex)
- ... und weitere

**Ziel:** werkstatt_live_api.py < 2,000 LOC

### 2. teile_data.py erstellen

Neues Datenmodul für Teile/Aftersales:
- get_lagerbestand()
- get_umschlaghaeufigkeit()
- get_renner_penner()
- get_teile_kpis()

**Consumer:** parts_api.py, teile_api.py, controlling_data.py

### 3. Tests durchführen

Nach jeder Migration:
```bash
ssh ag-admin@10.80.80.20 "curl -s 'http://localhost:5000/api/...' | jq '.source'"
```

Erwartetes Ergebnis: `"LIVE_V2"`

---

## WICHTIGE DATEIEN

```
api/werkstatt_data.py     - Single Source of Truth Werkstatt (1,457 LOC)
api/werkstatt_live_api.py - API-Endpoints (4,423 LOC, Ziel: <2,000)
api/teile_data.py         - NEU ERSTELLEN
docs/DATENMODUL_PATTERN.md - Pattern-Dokumentation
```

---

## DEPLOYMENT

Nach Code-Änderungen:
```bash
ssh ag-admin@10.80.80.20
cp /mnt/greiner-portal-sync/api/werkstatt_data.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/
sudo systemctl restart greiner-portal
```

---

## NÄCHSTE SESSIONS

- **TAG 150:** Restliche Werkstatt + teile_data.py
- **TAG 151:** TEK-Integration (controlling_data.py nutzt werkstatt_data.py)
- **TAG 152:** Finale TEK-Migration + Validierung

---

*Erstellt: 2026-01-02*
