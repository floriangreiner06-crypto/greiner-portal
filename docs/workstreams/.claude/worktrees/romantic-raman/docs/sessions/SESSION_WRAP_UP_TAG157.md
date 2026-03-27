# SESSION WRAP-UP TAG 157

**Datum:** 2026-01-02
**Fokus:** Unternehmensplan GlobalCube-Kompatibilitat - 100% Match erreicht!

---

## ERREICHT

### 1. Unternehmensplan API - GlobalCube-kompatible Berechnung

**Datei:** `api/unternehmensplan_data.py`

Problem: DRIVE zeigte -145.214 EUR, GlobalCube zeigte -162.114 EUR (Differenz: ~17k EUR)

**Ursachen gefunden und behoben:**

1. **Zinsertraege (8932xx) fehlten im Umsatz**
   - SQL erweitert: `OR (nominal_account_number BETWEEN 893200 AND 893299)`
   - Diese 193 EUR Zinsertraege gehoeren laut GlobalCube-Logik zum Umsatz

2. **Sonstige Erloese (88xxxx) wurden ignoriert**
   - CASE-Statement korrigiert: `WHEN nominal_account_number BETWEEN 860000 AND 889999 THEN 'Sonstige'`
   - Vorher: Nur 86xxxx, jetzt: 86xxxx-88xxxx
   - Betroffen: 2.823 EUR

3. **Sonstiger Einsatz (79xxxx) wurde ignoriert**
   - CASE-Statement korrigiert: `WHEN nominal_account_number BETWEEN 760000 AND 799999 THEN 'Sonstige'`
   - Vorher: Nur 76xxxx, jetzt: 76xxxx-79xxxx
   - Betroffen: 19.916 EUR

### 2. Validierung gegen GlobalCube - 100% Match!

```
=== GESAMT Sep-Nov 2025 (GJ 2025/26) ===
Umsatz:             8,412,969.47 EUR
Einsatz:            7,329,196.15 EUR
DB1:                1,083,773.32 EUR

Variable Kosten:      234,893.99 EUR
Direkte Kosten:       469,362.70 EUR
Indirekte Kosten:     639,173.68 EUR
Kosten gesamt:      1,343,430.37 EUR

Betriebsergebnis:    -259,657.05 EUR
Neutrales Ergebnis:    97,543.21 EUR
=================================
UNTERNEHMENSERGEBNIS: -162,113.84 EUR  (GlobalCube: -162,114 EUR)
IST-Rendite:               -1.93 %
```

**Differenz: 0.16 EUR** - Rundungsdifferenz, akzeptabel!

---

## GLOBALCUBE BWA-LOGIK (REFERENZ)

Die vollstaendige GlobalCube-kompatible Kontenlogik ist dokumentiert in:
- `docs/BWA_KONTEN_MAPPING_FINAL.md` (100% validiert)
- `docs/KONTENPLAN_CONTROLLING.md`

### Kurzuebersicht:

| Position | Konten | Vorzeichen |
|----------|--------|------------|
| **Umsatz** | 800000-889999 + 893200-893299 | HABEN - SOLL |
| **Einsatz** | 700000-799999 | SOLL - HABEN |
| **Variable Kosten** | 415xxx, 435xxx, 455-456xxx (KST!=0), 487xxx (KST!=0), 491-497xxx | SOLL - HABEN |
| **Direkte Kosten** | 400000-489999 KST 1-7 (ohne Variable, ohne 424xxx, 438xxx) | SOLL - HABEN |
| **Indirekte Kosten** | 4xxxxx KST 0 + 424xxx + 438xxx + 498-499xxx + 891-896xxx (ohne 8932xx) | SOLL - HABEN |
| **Neutrales Ergebnis** | 200000-299999 | HABEN - SOLL |

### Berechnung:
```
DB1 = Umsatz - Einsatz
DB2 = DB1 - Variable Kosten
DB3 = DB2 - Direkte Kosten
Betriebsergebnis = DB3 - Indirekte Kosten
Unternehmensergebnis = Betriebsergebnis + Neutrales Ergebnis
Rendite = Unternehmensergebnis / Umsatz * 100
```

---

## BEREICHS-ZUORDNUNG

### Umsatz (8xxxxx):
| Bereich | Konten |
|---------|--------|
| NW | 810000-819999 |
| GW | 820000-829999 |
| Teile | 830000-839999 |
| Werkstatt | 840000-849999 |
| Sonstige | 860000-889999 + 893200-893299 |

### Einsatz (7xxxxx):
| Bereich | Konten |
|---------|--------|
| NW | 710000-719999 |
| GW | 720000-729999 |
| Teile | 730000-739999 |
| Werkstatt | 740000-749999 |
| Sonstige | 760000-799999 |

---

## DATEIEN GEAENDERT

1. `api/unternehmensplan_data.py`
   - Umsatz-Query: +8932xx, 86xxxx erweitert auf 86-88xxxx
   - Einsatz-Query: 76xxxx erweitert auf 76-79xxxx
   - Docstring aktualisiert mit GlobalCube-Referenz

---

## ARCHITEKTUR-ERKENNTNISSE

Die GlobalCube-Logik ist jetzt als "Source of Truth" in DRIVE implementiert:

1. **Einheitliche Datenbasis**: `docs/BWA_KONTEN_MAPPING_FINAL.md` als zentrale Referenz
2. **SSOT-Pattern**: `unternehmensplan_data.py` nutzt die gleiche Logik wie `controlling_api.py`
3. **Validierung**: Jederzeit vergleichbar mit GlobalCube

---

## NAECHSTE SCHRITTE (TAG 158)

1. **Template aktualisieren**: Unternehmensplan UI zeigt jetzt korrekte Werte
2. **TEK-Dashboard pruefen**: Verwendet gleiche Logik?
3. **Weitere Module validieren**: Budget, BWA v2

---

## API-ENDPOINTS

```
GET /api/unternehmensplan/health
GET /api/unternehmensplan/dashboard?gj=2025/26&standort=0
GET /api/unternehmensplan/ist?gj=2025/26&standort=0
GET /api/unternehmensplan/gap?gj=2025/26&standort=0
GET /api/unternehmensplan/bereiche
```

---

## PORTAL URLs

- **Unternehmensplan Dashboard:** https://drive.auto-greiner.de/controlling/unternehmensplan
