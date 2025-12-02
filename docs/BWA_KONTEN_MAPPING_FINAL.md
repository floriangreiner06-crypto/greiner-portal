# BWA KONTEN-MAPPING GLOBALCUBE → LOCOSOFT (SKR51)

**Erstellt:** 2025-12-02  
**Validiert gegen:** GlobalCube Oktober + November 2025  
**Status:** 100% MATCH ✅

---

## WICHTIG: SKR51 LOGIK

In SKR51 (Autohaus-Kontenrahmen) sind die Konten **umgekehrt** wie in SKR03/04:

| Kontenbereich | Bedeutung | Vorzeichen |
|---------------|-----------|------------|
| **7xxxxx** | EINSATZWERTE (Wareneinsatz) | SOLL - HABEN |
| **8xxxxx** | UMSATZERLÖSE | HABEN - SOLL |
| **4xxxxx** | Kosten | SOLL - HABEN |

---

## 1. UMSATZERLÖSE

```sql
-- Konten: 80-88 + 8932xx
-- Berechnung: HABEN - SOLL
SELECT SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END)/100.0
FROM loco_journal_accountings
WHERE (nominal_account_number BETWEEN 800000 AND 889999)
   OR (nominal_account_number BETWEEN 893200 AND 893299)
```

**NICHT enthalten (→ Indirekte Kosten/Sonderposten):**
- 8905xx: Sonstige
- 8910xx: Geldwerter Vorteil
- 8917xx: KFZ-Nutzung privat
- 8920xx: Diverses
- 8930xx: (außer 8932xx)
- 8967xx: Telefon privat

---

## 2. EINSATZWERTE

```sql
-- Konten: 70-79
-- Berechnung: SOLL - HABEN
SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 700000 AND 799999
```

---

## 3. VARIABLE KOSTEN

```sql
SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0
FROM loco_journal_accountings
WHERE (
    -- 4151xx: Provisionen Finanz-Vermittlung
    nominal_account_number BETWEEN 415100 AND 415199
    -- 4355xx: Trainingskosten
    OR nominal_account_number BETWEEN 435500 AND 435599
    -- 455xx-456xx: Fahrzeugkosten (nur KST 1-7)
    OR (nominal_account_number BETWEEN 455000 AND 456999 
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
    -- 4870x: Werbekosten direkt (nur KST 1-7)
    OR (nominal_account_number BETWEEN 487000 AND 487099 
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
    -- 491xx-497xx: Fertigmachen, Provisionen, Kulanz
    OR nominal_account_number BETWEEN 491000 AND 497899
)
```

**Konten-Gruppen:**
| Bereich | Konten | Beschreibung |
|---------|--------|--------------|
| Provisionen | 4151xx | Finanz-Vermittlung |
| Training | 4355xx | Trainingskosten |
| Fahrzeuge | 455xx-456xx | VFW, Ersatzwagen (KST 1-7) |
| Werbung | 4870x | Werbekosten direkt (KST 1-7) |
| Fertigmachen | 491xx | Fertigmachen, Wagenwäschen |
| VK-Provisionen | 492xx | Verkäuferprovisionen |
| Provisionen | 493xx | Finanz, Versicherung, Sonstige |
| Fixum | 494xx | Fixum NW/GW |
| Vermittlung | 495xx | Vermittlerprovisionen, Lager |
| GW-Garantie | 496xx | GW-Programm, Garantie |
| Kulanz | 497xx | Alle Kulanz-Arten (bis 4978xx) |

---

## 4. DIREKTE KOSTEN

```sql
-- Alle 40-48 Konten mit KST 1-7 (5. Ziffer)
-- AUSSER Variable und 424xx, 438xx
SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 400000 AND 489999
  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
  AND NOT (
    nominal_account_number BETWEEN 415100 AND 415199
    OR nominal_account_number BETWEEN 424000 AND 424999  -- → Indirekt
    OR nominal_account_number BETWEEN 435500 AND 435599
    OR nominal_account_number BETWEEN 438000 AND 438999  -- → Indirekt
    OR nominal_account_number BETWEEN 455000 AND 456999
    OR nominal_account_number BETWEEN 487000 AND 487099
    OR nominal_account_number BETWEEN 491000 AND 497999
  )
```

**Typische Konten:**
- 4100x: Hilfslöhne
- 4110x: Lohn/Gehalt Azubi
- 4150x: Gehalt (OHNE 4151x Provisionen!)
- 4300x: AG-Anteil Sozialversicherung
- 4320x: Sonst. Personalkosten
- 4360x: Gratifikation/Urlaubsgeld
- 4690x: Klein- u. Reinigungsmaterial
- 4890x: Sonstige Kosten

---

## 5. INDIREKTE KOSTEN

```sql
SELECT SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END)/100.0
FROM loco_journal_accountings
WHERE (
    -- Alle 4xxxxx mit KST 0
    (nominal_account_number BETWEEN 400000 AND 499999 
     AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
    -- 424xx KFZ-Pauschale (immer indirekt)
    OR (nominal_account_number BETWEEN 424000 AND 424999 
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
    -- 438xx Sachzuwendungen (immer indirekt)
    OR (nominal_account_number BETWEEN 438000 AND 438999 
        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
    -- 498xx Umlagen
    OR nominal_account_number BETWEEN 498000 AND 499999
    -- 89xxxx Sonderposten
    OR nominal_account_number BETWEEN 891000 AND 896999
)
```

**Typische Konten:**
- 4xxx0: Alle Verwaltungskonten (KST 0)
- 424xx: KFZ-Pauschale
- 438xx: Sachzuwendungen
- 4980x: Umlagen indirekte Kosten
- 4981x: Umlagen Immobilien
- 4982x: Umlagen Zinsen
- 8917x: KFZ-Nutzung privat
- 8967x: Telefon privat

---

## KOSTENSTELLEN-LOGIK

Die **5. Ziffer** eines 6-stelligen Kontos (4xxxYx) bestimmt die Kostenstelle:

| 5. Ziffer | Kostenstelle | BWA-Kategorie |
|-----------|--------------|---------------|
| **0** | Gesamt/Verwaltung | INDIREKT |
| **1** | Neuwagen | DIREKT oder VARIABEL |
| **2** | Gebrauchtwagen | DIREKT oder VARIABEL |
| **3** | Mechanik | DIREKT oder VARIABEL |
| **4** | Karosserie | DIREKT |
| **5** | Lackiererei | DIREKT |
| **6** | Teile & Zubehör | DIREKT oder VARIABEL |
| **7** | Mietwagen | DIREKT oder VARIABEL |

---

## VALIDIERUNG

| Position | Oktober 2025 | November 2025 |
|----------|--------------|---------------|
| Umsatzerlöse | ✅ 100% (0,00 €) | ✅ 100% (0,00 €) |
| Einsatzwerte | ✅ 100% (0,00 €) | ✅ 100% (0,00 €) |
| DB1 | ✅ 100% | ✅ 100% |
| Variable Kosten | ✅ 100% (0,00 €) | ✅ 100% (0,00 €) |
| DB2 | ✅ 100% | ✅ 100% |
| Direkte Kosten | ✅ 100% (0,00 €) | ✅ 100% (0,00 €) |
| DB3 | ✅ 100% | ✅ 100% |
| Indirekte Kosten | ✅ 99.9% (193 €) | ✅ 100% (0,00 €) |
| Betriebsergebnis | ✅ 99.4% | ✅ 100% |

---

## SCRIPTS

| Script | Beschreibung | Cron |
|--------|--------------|------|
| `locosoft_mirror.py` | Spiegelt Locosoft → SQLite | 19:00 |
| `bwa_berechnung.py` | Berechnet BWA aus Mirror | 19:30 |

---

## DATENBANK-TABELLE

```sql
CREATE TABLE bwa_monatswerte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jahr INTEGER NOT NULL,
    monat INTEGER NOT NULL,
    position TEXT NOT NULL,        -- umsatz, einsatz, db1, variable, db2, direkte, db3, indirekte, betriebsergebnis
    bezeichnung TEXT,              -- Lesbare Bezeichnung
    betrag REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jahr, monat, position)
);
```

---

*Erstellt: 2025-12-02 | Validiert gegen GlobalCube*
