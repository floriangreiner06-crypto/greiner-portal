# TODO FOR CLAUDE - SESSION START TAG 151

**Letzte Session:** TAG 150 (2026-01-02)
**Ziel:** API-Endpoints refaktorieren + weitere Migration

---

## KONTEXT

TAG 150 hat 3 neue Funktionen zu `werkstatt_data.py` hinzugefuegt:
- get_tagesbericht()
- get_auftrag_detail()
- get_problemfaelle()

**Problem:** Die API-Endpoints in werkstatt_live_api.py nutzen noch den alten Code.
Die Refaktorierung war aufgrund von Dateisperren nicht moeglich.

**Aktueller Stand:**
- werkstatt_data.py: 2,093 LOC (8 Funktionen)
- werkstatt_live_api.py: 4,423 LOC (noch nicht refaktoriert)

---

## AUFGABEN TAG 151

### 1. API-Endpoints refaktorieren

Diese 3 Endpoints muessen WerkstattData nutzen:

```python
# /tagesbericht -> WerkstattData.get_tagesbericht()
# /auftrag/<nr> -> WerkstattData.get_auftrag_detail()
# /problemfaelle -> WerkstattData.get_problemfaelle()
```

**Muster (siehe bereits migrierte Endpoints):**
```python
@werkstatt_live_bp.route('/tagesbericht', methods=['GET'])
def get_tagesbericht():
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')
        datum = datetime.strptime(datum_str, '%Y-%m-%d').date() if datum_str else None

        data = WerkstattData.get_tagesbericht(datum=datum, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })
    except Exception as e:
        ...
```

### 2. Weitere Funktionen migrieren

Noch zu migrieren aus werkstatt_live_api.py:
- get_nachkalkulation() (~300 LOC)
- get_gudat_kapazitaet() (~100 LOC)
- get_heute_live() (~350 LOC)
- get_auftraege_enriched() (~550 LOC)
- get_anwesenheit_v2() (~170 LOC)
- get_anwesenheit_report() (~140 LOC)
- get_kulanz_monitoring() (~170 LOC)
- get_drive_briefing() (~180 LOC)
- get_drive_kapazitaet() (~220 LOC)
- get_werkstatt_liveboard() (~560 LOC)

**Ziel:** werkstatt_live_api.py < 2,000 LOC

### 3. Tests durchfuehren

Nach jeder Migration:
```bash
ssh ag-admin@10.80.80.20 "curl -s 'http://localhost:5000/api/...' | jq '.source'"
```

Erwartetes Ergebnis: `"LIVE_V2"`

---

## WICHTIGE DATEIEN

```
api/werkstatt_data.py     - Single Source of Truth (2,093 LOC)
api/werkstatt_live_api.py - API-Endpoints (4,423 LOC, Ziel: <2,000)
docs/DATENMODUL_PATTERN.md - Pattern-Dokumentation
```

---

## DEPLOYMENT

Nach Code-Aenderungen:
```bash
ssh ag-admin@10.80.80.20
cp /mnt/greiner-portal-sync/api/werkstatt_data.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal
```

---

## NAECHSTE SESSIONS

- **TAG 151:** API-Refaktorierung + weitere Migrationen
- **TAG 152:** TEK-Integration (controlling_data.py nutzt werkstatt_data.py)
- **TAG 153:** teile_data.py erstellen (Lager, Renner/Penner)
- **TAG 154:** sales_data.py erstellen (NW, GW, Finanzierung)

---

*Erstellt: 2026-01-02*
