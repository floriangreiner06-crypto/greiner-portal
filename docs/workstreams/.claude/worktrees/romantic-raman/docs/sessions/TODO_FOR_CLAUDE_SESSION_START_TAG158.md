# TODO FOR CLAUDE - SESSION START TAG 158

**Letzte Session:** TAG 157 (2026-01-02)
**Ziel:** Weitere Module mit GlobalCube-Logik validieren

---

## KONTEXT

TAG 157 hat das **Unternehmensplan-Modul GlobalCube-kompatibel** gemacht:

### Behoben:
- Zinsertraege (8932xx) jetzt im Umsatz
- Sonstige Erloese (88xxxx) jetzt in "Sonstige"
- Sonstiger Einsatz (79xxxx) jetzt in "Sonstige"
- **Ergebnis: 100% Match mit GlobalCube** (-162.114 EUR)

### GlobalCube BWA-Logik dokumentiert in:
- `docs/BWA_KONTEN_MAPPING_FINAL.md`
- `docs/KONTENPLAN_CONTROLLING.md`

---

## AUFGABEN TAG 158

### Option A: TEK-Dashboard Validierung

Pruefen ob TEK-Dashboard die gleiche Logik wie Unternehmensplan nutzt:

```python
# Vergleichen:
api/controlling_data.py  # TEK-Datenmodul
api/unternehmensplan_data.py  # Unternehmensplan (jetzt korrekt)
```

Fragen:
- Stimmen Umsatz/Einsatz/Kosten ueberein?
- Werden 8932xx, 88xxxx, 79xxxx korrekt behandelt?

### Option B: BWA v2 Validierung

Der BWA v2 Endpoint in `controlling_api.py` sollte bereits korrekt sein, aber validieren gegen GlobalCube.

### Option C: Budget-Modul erweitern

Das Budget-Planungsmodul (TAG 155-156) braucht evtl. Anpassungen:
- IST-Daten aus `unternehmensplan_data.py` nutzen?
- Konsistenz sicherstellen

### Option D: Neues Modul starten

- `teile_data.py` (SSOT fuer Teilelager)
- Locosoft SOAP Client (Gudat-Abloesung)

---

## WICHTIGE DATEIEN

```
api/unternehmensplan_data.py    - SSOT Unternehmensplan (GlobalCube-kompatibel)
api/controlling_data.py         - SSOT TEK
api/controlling_api.py          - BWA v2, TEK-Endpoints
docs/BWA_KONTEN_MAPPING_FINAL.md - GlobalCube Konten-Referenz
docs/KONTENPLAN_CONTROLLING.md   - Vollstaendige Doku
```

---

## VALIDIERTE WERTE (Sep-Nov 2025)

```
Umsatz:             8,412,969 EUR
Einsatz:            7,329,196 EUR
DB1:                1,083,773 EUR
Variable Kosten:      234,894 EUR
Direkte Kosten:       469,363 EUR
Indirekte Kosten:     639,174 EUR
Betriebsergebnis:    -259,657 EUR
Neutrales Ergebnis:    97,543 EUR
Unternehmensergebnis: -162,114 EUR
Rendite:                -1.93 %
```

---

## PORTAL URLs

- **Unternehmensplan:** https://drive.auto-greiner.de/controlling/unternehmensplan
- **TEK Dashboard:** https://drive.auto-greiner.de/controlling/tek
- **BWA:** https://drive.auto-greiner.de/controlling/bwa
