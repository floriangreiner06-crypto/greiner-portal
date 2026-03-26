# Provisionsabgleich PDF / Excel – Prüfung und Stellungnahme

**Stand:** 2026-02  
**Ziel:** Berechnung wie im PDF (aus Excel-Tool); Abweichungen identifizieren und beheben.

**Excel-Datei (analysiert):**  
`/mnt/greiner-portal-sync/docs/workstreams/verkauf/provisionsabrechnung/Provisionsabrechnung_V0.11.xlsm`  
(Windows: `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\verkauf\provisionsabrechnung\`)

---

## 1. BE2 / DB2 (GW aus Bestand) – VK-Kosten-Formel

### 1.1 Formel laut Excel (PROVISIONSLOGIK_AUS_EXCEL.md)

- **Kosten (BE II / VK-Kosten):**  
  `BE II = ROUND((DB × J60) + J61; 2)`  
  (J60 = Prozentsatz, J61 = Fixbetrag aus **Optionen** J60, J61.)
- **Umsatzprovision-Basis:** `DB - BE II`
- **Provision Kat. IV:** `Provision = (DB - BE II) × 0,12`

### 1.2 Umsetzung in DRIVE (api/provision_service.py)

```python
# calc_gw_bestand(db_betrag, config):
kosten = round((db_betrag * j60) + j61, 2)   # BE II / VK-Kosten
basis = db_betrag - kosten                    # DB - BE II
return round(basis * 0.12, 2)                 # 12 % auf Basis
```

**Bewertung:** Die **Formel** entspricht dem Excel (BE II = (DB×J60)+J61, gerundet; dann (DB − BE II) × 12 %).

### 1.3 Auswertung Excel Optionen (Provisionsabrechnung_V0.11.xlsm)

Aus dem Blatt **Optionen** (Zellen J52–J61) wurden ausgelesen:

| Zelle | Bezeichnung (I) | Wert |
|-------|------------------|------|
| J52   | (Prov. Neuwagen) | **0,12** (12 %) |
| J53   | V (Testwagen)    | 0,01 (1 %) |
| J54   | G                | 0,01 (1 %) |
| **J60** | Prov            | **0,01** (1 % für VK-Kosten) |
| **J61** | Fix            | **175** (€ Fixbetrag für VK-Kosten) |

**Formeln im Blatt „Fahrzeugverkaeufe“ (GW aus Bestand, Zeile 111):**
- **H** = DB (Deckungsbeitrag aus Import Spalte AF) = „BE I €“
- **I** = `ROUND((H*Optionen!$J$60)+Optionen!$J$61; 2)` = VK-Kosten
- **J** = `H - I` = DB − VK-Kosten = Basis für Provision („BE II €“ im Sinne der verbleibenden Basis)
- Provision = 12 % auf J (wie in Optionen J52).

**DRIVE:** Diese Werte wurden in **provision_config** übernommen: **param_j60 = 0.01**, **param_j61 = 175**. Die DB2-Berechnung (calc_gw_bestand) verwendet damit dieselbe Formel wie das Excel.

---

## 2. Umsatzprovisionen (Kat. II und III)

### 2.1 Excel-Regeln (aus PROVISIONSLOGIK_AUS_EXCEL.md)

| Kategorie | Maßgröße | Satz | Min | Max |
|-----------|----------|------|-----|-----|
| II. Testwagen/VFW | Rg.Netto | 1 % (J53) | 103 € | **500 €** (im Sheet; VFW-Block teils 300 €) |
| III. Gebrauchtwagen | Rg.Netto | 1 % (J53) | 103 € | 500 € |

- Formel: `WENN(Erlös*Satz < 103; 103; WENN(Erlös*Satz > 500; 500; Erlös*Satz))`.
- Vorführwagen (T/V) im Excel: 1 % (J54), **min 103 €, max 300 €**.

### 2.2 Aktuelle DRIVE-Konfiguration (provision_config)

| Kategorie | min_betrag | max_betrag |
|-----------|------------|------------|
| II_testwagen | 103 | **300** |
| III_gebrauchtwagen | 103 | 500 |

**Abweichung:**  
- **Kat. II:** DRIVE verwendet **max 300 €**, Excel (Hauptformel) **500 €**. Im Excel gibt es einen separaten „Vorführwagen-Block“ mit max 300 €. Wenn im PDF für Testwagen/VFW ein **max 500 €** genutzt wird, muss in DRIVE für **II_testwagen** ggf. **max_betrag = 500** gesetzt werden (oder fachlich klären: nur VFW 300 €, „Testwagen“ 500 €).

### 2.3 Bemessungsgrundlage „Rg.Netto“

- **Excel:** Maßgröße = **Rg.Netto** (Erlös; Import-Spalte R).
- **DRIVE:** Verwendet **netto_vk_preis** aus der Tabelle **sales** (berechnet im Sync: `out_sale_price - mwst`).

Falls im Locosoft-Export „Rg.Netto“ anders definiert ist (z. B. anderes Feld oder andere MwSt-Berechnung), entstehen Abweichungen pro Position. **Empfehlung:** Eine Stichprobe (z. B. 3–5 Rechnungen) PDF vs. DRIVE vergleichen (Rg.Nr., Netto, berechnete Provision); bei Abweichung Herkunft von „Rg.Netto“ im Export prüfen und ggf. Sync/Formel anpassen.

---

## 3. Kat. I (Neuwagen)

- Excel: DB × 12 % + 50 €/Stück (max 15 Stück).
- DRIVE: Nutzt teils **Zielprämie** (use_zielpraemie) statt fester 50 €/Stück. Wenn das PDF mit dem alten Excel (50 €/Stück) erstellt wird, entstehen Abweichungen, sobald in DRIVE die Zielprämie aktiv ist.

---

## 4. Zusammenfassung und nächste Schritte

| Punkt | Status | Aktion |
|-------|--------|--------|
| **BE2/VK-Kosten-Formel** | Formel in DRIVE = Excel | Keine Code-Änderung nötig. |
| **J60, J61** | **Erledigt** | In **provision_config** (IV_gw_bestand) gesetzt: param_j60 = 0.01, param_j61 = 175 (aus Excel Optionen). |
| **Kat. II max** | DRIVE 300, Excel 500 (bzw. 300 nur VFW) | Fachlich klären; ggf. max_betrag für II auf 500 setzen. |
| **Rg.Netto vs. netto_vk_preis** | Unklar ob identisch | Stichprobe PDF vs. DRIVE; ggf. Datenherkunft anpassen. |
| **Kat. I (Zielprämie vs. 50 €/Stück)** | Unterschied möglich | Bei Abgleich Neuwagen prüfen, ob Zielprämie oder 50 €/Stück gewünscht. |

Sobald **J60** und **J61** aus dem Excel (Optionen) in **provision_config** stehen und ggf. **max_betrag** für Kat. II geklärt ist, sollten die Berechnungen (insbesondere DB2 und Umsatzprovisionen) dem PDF deutlich näher kommen. Eine Stichprobe mit dem Roland-Januar-PDF wird empfohlen.
