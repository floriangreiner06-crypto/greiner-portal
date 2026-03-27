# DRIVE Planung GJ 2025/26 — Anweisung für Claude Code

**Erstellt:** 2026-02-13
**Zweck:** Dieses Dokument enthält alle Daten und Anweisungen, damit Claude Code (Cursor) die DRIVE-Planungstabellen für GJ 2025/26 (Sep 2025 – Aug 2026) befüllen kann.
**Ziel:** Profitabilität — mindestens Break-Even, Ziel 1% Rendite.

---

## 1. KONTEXT & SYSTEMARCHITEKTUR

### 1.1 Projektpfade

```
Server:          10.80.80.20
Projekt:         /opt/greiner-portal/
DB (SQLite):     /opt/greiner-portal/data/greiner_controlling.db
DB (PostgreSQL): Locosoft (read-only, Verbindung via api/db_utils.py)
Venv:            /opt/greiner-portal/venv/bin/python3
Restart:         sudo systemctl restart greiner-portal
```

### 1.2 Relevante Dateien

| Zweck | Datei |
|-------|-------|
| Unternehmensplan SSOT | `api/unternehmensplan_data.py` |
| Abteilungsleiter-Planung Data | `api/abteilungsleiter_planung_data.py` |
| Abteilungsleiter-Planung API | `api/abteilungsleiter_planung_api.py` |
| Abteilungsleiter-Planung Validierung | `api/abteilungsleiter_planung_validierung.py` |
| KST Bottom-Up | `api/kst_planung_bottom_up.py` |
| GW Planung V2 Data | `api/gewinnplanung_v2_gw_data.py` |
| GW Planung V2 API | `api/gewinnplanung_v2_gw_api.py` |
| Planung Routes | `routes/planung_routes.py` |
| GW Planung Routes | `routes/gewinnplanung_v2_routes.py` |
| Migration: abteilungsleiter_planung | `migrations/create_abteilungsleiter_planung_tag165.sql` |
| Migration: kst_planung_parameter | `migrations/add_kst_planung_parameter_tag165.sql` |
| Migration: kst_ziele extend | `migrations/extend_kst_ziele_bottom_up_tag165.sql` |
| BWA Konten Mapping | `docs/BWA_KONTEN_MAPPING_FINAL.md` |
| Budget-Planungsmodul Konzept | `projects/budget_planungsmodul/KONZEPT_DRIVE_BUDGET_PLANUNG.md` |

### 1.3 Geschäftsjahr-Logik

- **GJ 2025/26** = September 2025 bis August 2026
- **GJ-Monat 1** = September, **GJ-Monat 12** = August
- Funktion: `get_current_geschaeftsjahr()` in `api/unternehmensplan_data.py`
- String-Format: `'2025/26'`

### 1.4 Standorte

| ID | Name | Marken | Firma |
|----|------|--------|-------|
| 0 | Konzern (Gesamt) | Alle | Konsolidiert |
| 1 | Deggendorf | Opel/Stellantis + Leapmotor | Autohaus Greiner GmbH & Co. KG |
| 2 | Deggendorf HYU | Hyundai | Auto Greiner GmbH & Co. KG |
| 3 | Landau | Opel/Stellantis | Autohaus Greiner GmbH & Co. KG |

**SSOT für Standort-Namen:** `api/standort_utils.py`

### 1.5 Bereiche (Kostenstellen)

| Bereich | BWA-Umsatzkonten | BWA-Einsatzkonten | KST-Nr |
|---------|------------------|-------------------|--------|
| NW | 810000-819999 | 710000-719999 | 1 |
| GW | 820000-829999 | 720000-729999 | 2 |
| Werkstatt (ME) | 840000-849999 | 740000-749999 | 3 |
| Karosserie (KA) | (in ME enthalten) | | 4 |
| Teile (TZ) | 830000-839999 | 730000-739999 | 5 |
| Clean Park (CP) | (in Sonstige) | | 6 |
| Mietwagen (MW) | (in Sonstige) | | 7 |
| Sonstige | 860000-869999 | 760000-769999 | 8 |

---

## 2. PLANUNGSDATEN GJ 2025/26

### 2.1 Ausgangslage — Vorjahresvergleich

#### GJ 2023/24 (Referenzjahr — profitabel)

| Kennzahl | Wert |
|----------|------|
| NW Stück | 544 |
| GW Stück | 736 |
| Umsatz gesamt | 31.894.244 € |
| Bruttoertrag gesamt | 6.036.542 € |
| NW DB1 gesamt | 1.693.113 € |
| GW DB1 gesamt | 1.104.085 € |
| NW Ø DB1/Fzg | 3.112 € |
| GW Ø DB1/Fzg | 1.500 € |
| Variable Kosten | 1.082.765 € |
| Direkte Kosten | 1.870.180 € |
| Indirekte Kosten | 2.397.435 € |
| Betriebsergebnis | 686.162 € |
| Neutrales Ergebnis | -385.429 € |
| **Unternehmensergebnis** | **+300.732 €** |

#### GJ 2024/25 (Vorjahr — knapp negativ)

| Kennzahl | Gesamt | Deggendorf (Stel) | Deggendorf (HYU) | Landau |
|----------|--------|-------------------|------------------|--------|
| NW Stück | 444 | 213 | 199 | 32 |
| GW Stück | 625 | 287 | 179 | 160 |
| Umsatz | 30.445.184 € | 14.699k | 11.116k | 4.630k |
| NW DB1 | 1.578.056 € | 1.097.188 | 446.020 | 34.848 |
| GW DB1 | 613.012 € | 206.675 | 332.257 | 74.080 |
| NW Ø DB1/Fzg | 3.554 € | 5.151 | 2.241 | 1.089 |
| GW Ø DB1/Fzg | 981 € | 720 | 1.856 | 463 |
| NW var.K/Fzg | 1.079 € | 1.394 | 765 | 927 |
| GW var.K/Fzg | 424 € | 561 | 377 | 232 |
| ME DB1 | 1.353.126 € | – | – | – |
| TZ DB1 | 1.355.153 € | – | – | – |
| CP DB1 | 296.309 € | – | – | – |
| MW DB1 | 236.817 € | – | – | – |
| KA DB1 | 84.295 € | – | – | – |
| Sonst DB1 | 11.611 € | – | – | – |
| Variable Kosten | 889.675 € | – | – | – |
| Direkte Kosten | 1.837.202 € | – | – | – |
| Indirekte Kosten | 2.479.617 € | – | – | – |
| Neutrales Ergebnis | -351.748 € | – | – | – |
| **Unternehmensergebnis** | **-29.864 €** | -224k | +163k | +31k |

### 2.2 NW-Plan GJ 2025/26 (VORGABE Geschäftsführung)

**Kalenderjahr 2026 Targets (12 Monate):**

| Marke | KJ 2026 | Standort |
|-------|---------|----------|
| Opel/Stellantis | 300 Stk | DEG (1) + Landau (3) |
| Leapmotor (NEU!) | 150 Stk | DEG (1) |
| Hyundai | 190 Stk | DEG HYU (2) |
| **GESAMT** | **640 Stk** | |

**Umrechnung auf GJ (Sep 2025 – Aug 2026):**

| Zeitraum | NW Stk | Quelle |
|----------|--------|--------|
| Sep 25 – Jan 26 (IST) | ~232 | BWA/Locosoft |
| Feb 26 – Aug 26 (PLAN, 7 Mon) | 374 | KJ × 7/12 |
| **GJ GESAMT** | **606** | |

**NW REST Feb–Aug aufgeteilt nach Standort:**

| Standort | Marke | Stk REST | Stk/Mon | Ø DB1/Fzg | Ø Var.K/Fzg | Ø Netto/Fzg |
|----------|-------|----------|---------|-----------|-------------|-------------|
| 1 (DEG) | Opel/Stellantis | 152 | 22 | 5.151 € | 1.395 € | 3.756 € |
| 1 (DEG) | Leapmotor | 88 | 13 | 2.000 € | 1.000 € | 1.000 € |
| 2 (HYU) | Hyundai | 111 | 16 | 2.241 € | 765 € | 1.476 € |
| 3 (LAN) | Opel/Stellantis | 23 | 3 | 1.089 € | 927 € | 162 € |
| | **SUMME** | **374** | **53** | | | |

**NW DB1-Annahmen:**
- Opel/Stellantis DEG: VJ-Niveau 5.151 €/Fzg (19,3% Marge — nachgewiesen)
- Leapmotor: 2.000 €/Fzg (konservativ, neue Marke, EV-Margen)
- Hyundai: VJ-Niveau 2.241 €/Fzg (7,7% Marge — nachgewiesen)
- Opel Landau: VJ-Niveau 1.089 €/Fzg (4,1% Marge — nachgewiesen)

**NW Netto-Beitrag Berechnung:**

| Phase | Beitrag |
|-------|---------|
| IST Sep–Jan (232 Stk × ~2.475 €) | 574.200 € |
| REST Feb–Aug (374 Stk, gewichtet) | 826.533 € |
| **NW NETTO GJ GESAMT** | **1.400.733 €** |

### 2.3 GW-Plan GJ 2025/26

**Kernaussage: GW ist der Profit-Hebel, nicht das Überleben.**

Mit 606 NW + Service/Teile +3% ist Break-Even bereits ohne GW erreicht (+19.795 € Überschuss). Jeder verkaufte GW mit positiver Marge steigert direkt das Unternehmensergebnis.

**GW Stückzahl-Empfehlung:**

| Zeitraum | Stk | Stk/Mon |
|----------|-----|---------|
| Sep–Jan IST | ~260 | ~52 |
| Feb–Aug PLAN | ~340 | ~49 |
| **GJ GESAMT** | **~600** | |

**GW DB1-Szenarien (Netto = DB1 – var. Kosten 424 €/Fzg):**

| Szenario | Ø DB1/Fzg | Ø Netto/Fzg | UE bei 600 GW |
|----------|-----------|-------------|---------------|
| VJ-Niveau (schlecht) | 981 € | 557 € | 354k € (1,2%) |
| Ziel 6% auf 18k | 1.080 € | 656 € | 413k € (1,4%) |
| Ziel 1.200 € DB1 | 1.200 € | 776 € | 486k € (1,6%) |
| VVJ-Niveau (gut) | 1.500 € | 1.076 € | 665k € (2,2%) |

**GW DB1-Annahme pro Standort (Plan):**

| Standort | Ø DB1 Plan | Begründung |
|----------|-----------|------------|
| 1 (DEG Stel) | 1.000 € | VJ war 720, Ziel Verbesserung Richtung VVJ |
| 2 (DEG HYU) | 1.500 € | VJ war 1.856 — beibehalten |
| 3 (Landau) | 700 € | VJ war 463, realistisch limitiert |

### 2.4 Service, Teile & Sonstige (Non-Vehicle)

**Plan: VJ +3% (minimal steigerbar lt. Geschäftsführung)**

| Segment | VJ DB1 | VJ Var.K | VJ Netto | Plan Netto (+3%) |
|---------|--------|----------|----------|-----------------|
| Mechanik/Service (ME) | 1.353.126 € | 99.071 € | 1.254.055 € | 1.291.677 € |
| Karosserie (KA) | 84.295 € | 0 € | 84.295 € | 86.824 € |
| Teile/Zubehör (TZ) | 1.355.153 € | 35.654 € | 1.319.499 € | 1.359.084 € |
| Clean Park (CP) | 296.309 € | 0 € | 296.309 € | 305.198 € |
| Mietwagen (MW) | 236.817 € | 10.713 € | 226.104 € | 232.887 € |
| Sonstige (SO) | 11.611 € | 0 € | 11.611 € | 11.959 € |
| **SUMME** | **3.337.311 €** | **145.438 €** | **3.191.873 €** | **3.287.629 €** |

### 2.5 Kostenblock (UNVERÄNDERT — kein Hebel)

| Position | Betrag |
|----------|--------|
| Direkte Kosten (Personal segmentiert) | 1.837.202 € |
| Indirekte Kosten (Overhead) | 2.479.617 € |
| Neutrales Ergebnis | -351.748 € |
| **TOTAL zu decken** | **4.668.567 €** |

### 2.6 Gesamtrechnung — Ergebnisprognose

```
Deckung:
  NW Netto (606 Stk):                1.400.733 €
  Non-Vehicle Netto (+3%):           3.287.629 €
  ────────────────────────────────────────────────
  SUMME ohne GW:                     4.688.362 €
  Kosten zu decken:                  4.668.567 €
  ────────────────────────────────────────────────
  ÜBERSCHUSS ohne GW:                  +19.795 €  ✅ BREAK-EVEN!

  + GW Beitrag (600 Stk):
    bei Ø 981€ DB1 (VJ):             + 334.200 €  → UE  354k€ (1,2%)
    bei Ø 1.200€ DB1 (Ziel):         + 465.600 €  → UE  486k€ (1,6%)
    bei Ø 1.500€ DB1 (VVJ):          + 645.600 €  → UE  665k€ (2,2%)
```

---

## 3. SAISONALISIERUNG

Basierend auf GJ 2023/24 Aktualwerte (aus GlobalCube Saisonalisierungs-Sheet):

### NW Verteilung (% pro Monat)

| Mon | Sep | Okt | Nov | Dez | Jan | Feb | Mär | Apr | Mai | Jun | Jul | Aug |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| NW % | 6,5 | 8,0 | 7,5 | 6,5 | 7,0 | 7,5 | 11,0 | 8,5 | 8,0 | 8,0 | 11,5 | 10,0 |

### GW Verteilung (% pro Monat)

| Mon | Sep | Okt | Nov | Dez | Jan | Feb | Mär | Apr | Mai | Jun | Jul | Aug |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| GW % | 7,0 | 8,5 | 7,5 | 6,0 | 7,0 | 8,0 | 11,0 | 8,5 | 8,5 | 8,0 | 10,5 | 9,5 |

**Hinweis:** Die Saisonalisierung wird als JSON im Feld `plan_saisonalisierung` gespeichert.

---

## 4. DATENBANK-OPERATIONEN

### 4.1 Tabellen prüfen

```sql
-- PostgreSQL (Planung liegt in PostgreSQL!)
-- Verbindung: api/db_utils.py → db_session()

SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('abteilungsleiter_planung', 'kst_planung_parameter', 'kst_ziele');
```

**ACHTUNG:** Die Planungstabellen liegen in **PostgreSQL** (nicht SQLite!). Zugriff über:
```python
from api.db_utils import db_session
with db_session() as cursor:
    cursor.execute("SELECT * FROM abteilungsleiter_planung LIMIT 5")
```

### 4.2 Alte Plandaten löschen (falls vorhanden)

```sql
DELETE FROM abteilungsleiter_planung WHERE geschaeftsjahr = '2025/26';
DELETE FROM kst_planung_parameter WHERE geschaeftsjahr = '2025/26';
```

### 4.3 KST Planungsparameter befüllen

```sql
-- NW Deggendorf Stellantis (Opel + Leapmotor kombiniert)
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES ('2025/26', 'NW', 1, NULL, 27676, 12.8, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    durchschnittspreis = EXCLUDED.durchschnittspreis,
    marge_ziel = EXCLUDED.marge_ziel,
    geaendert_am = NOW();

-- NW Hyundai
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES ('2025/26', 'NW', 2, NULL, 29022, 7.7, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    durchschnittspreis = EXCLUDED.durchschnittspreis,
    marge_ziel = EXCLUDED.marge_ziel,
    geaendert_am = NOW();

-- NW Landau
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES ('2025/26', 'NW', 3, NULL, 26262, 4.1, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    durchschnittspreis = EXCLUDED.durchschnittspreis,
    marge_ziel = EXCLUDED.marge_ziel,
    geaendert_am = NOW();

-- GW alle Standorte
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, stueck_pro_vk, durchschnittspreis, marge_ziel, erstellt_von)
VALUES 
    ('2025/26', 'GW', 1, NULL, 16818, 6.0, 'planung_script'),
    ('2025/26', 'GW', 2, NULL, 17503, 8.5, 'planung_script'),
    ('2025/26', 'GW', 3, NULL, 15344, 4.5, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    durchschnittspreis = EXCLUDED.durchschnittspreis,
    marge_ziel = EXCLUDED.marge_ziel,
    geaendert_am = NOW();

-- Werkstatt
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, stunden_pro_sb, stundensatz, auslastung_ziel, erstellt_von)
VALUES 
    ('2025/26', 'Werkstatt', 1, 120, 150, 85, 'planung_script'),
    ('2025/26', 'Werkstatt', 2, 120, 150, 85, 'planung_script'),
    ('2025/26', 'Werkstatt', 3, 120, 140, 80, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    stunden_pro_sb = EXCLUDED.stunden_pro_sb,
    stundensatz = EXCLUDED.stundensatz,
    auslastung_ziel = EXCLUDED.auslastung_ziel,
    geaendert_am = NOW();

-- Teile + Sonstige
INSERT INTO kst_planung_parameter 
(geschaeftsjahr, bereich, standort, wachstumsfaktor, erstellt_von)
VALUES 
    ('2025/26', 'Teile', 1, 1.03, 'planung_script'),
    ('2025/26', 'Teile', 2, 1.03, 'planung_script'),
    ('2025/26', 'Teile', 3, 1.03, 'planung_script'),
    ('2025/26', 'Sonstige', 1, 1.03, 'planung_script'),
    ('2025/26', 'Sonstige', 2, 1.03, 'planung_script'),
    ('2025/26', 'Sonstige', 3, 1.03, 'planung_script')
ON CONFLICT (geschaeftsjahr, bereich, standort) DO UPDATE SET
    wachstumsfaktor = EXCLUDED.wachstumsfaktor,
    geaendert_am = NOW();
```

### 4.4 Abteilungsleiter-Planung befüllen

Erstelle Script: `scripts/planung_gj2025_26_befuellen.py`

Das Script muss für jeden **Monat (1-12) × Bereich (NW/GW) × Standort (1/2/3)** einen Eintrag in `abteilungsleiter_planung` erstellen. Siehe Abschnitt 2 für die konkreten Zahlen. Die monatliche Verteilung ergibt sich aus der Saisonalisierung (Abschnitt 3) multipliziert mit der Jahres-Stückzahl.

**Stückzahlen pro Standort GJ-gesamt:**

| Bereich | Standort 1 | Standort 2 | Standort 3 | TOTAL |
|---------|-----------|-----------|-----------|-------|
| NW | 350 (Opel 262 + Leap 88) | 191 | 65 | 606 |
| GW | 260 | 190 | 150 | 600 |

**DB1 pro Fzg:**

| Bereich | Standort 1 | Standort 2 | Standort 3 |
|---------|-----------|-----------|-----------|
| NW | 4.200 € (gewichtet) | 2.241 € | 1.089 € |
| GW | 1.000 € | 1.500 € | 700 € |

### 4.5 Validierung nach Befüllung

```sql
-- Prüfe Gesamtstückzahlen
SELECT bereich, standort, SUM(plan_stueck) as gj_gesamt
FROM abteilungsleiter_planung
WHERE geschaeftsjahr = '2025/26'
GROUP BY bereich, standort
ORDER BY bereich, standort;

-- Erwartete Werte:
-- NW, 1: ~350 | NW, 2: ~191 | NW, 3: ~65 | TOTAL: ~606
-- GW, 1: ~260 | GW, 2: ~190 | GW, 3: ~150 | TOTAL: ~600

-- Prüfe Monatsverteilung
SELECT monat, bereich, SUM(plan_stueck) as stk, 
       SUM(plan_stueck * plan_bruttoertrag_pro_fzg) as db1
FROM abteilungsleiter_planung
WHERE geschaeftsjahr = '2025/26'
GROUP BY monat, bereich
ORDER BY monat, bereich;
```

---

## 5. ZUSAMMENFASSUNG — ERGEBNISPROGNOSE

```
┌─────────────────────────────────────────────────────────────────┐
│  PLANUNG GJ 2025/26 — ERGEBNISPROGNOSE                        │
├─────────────────────────────────────────────────────────────────┤
│  NW:  606 Stk — Netto-Beitrag: ~1.401k €                      │
│  GW:  ~600 Stk — Netto-Beitrag: 334k–646k € (je nach Marge)  │
│  Service/Teile (+3%): 3.288k € Netto-Beitrag                  │
│  Kosten (fix): 4.669k €                                        │
│  ═══════════════════════════════════════════════════════════     │
│  UE KONSERVATIV (Ø 981€ GW-DB1):     354k € (1,2%)  ✅       │
│  UE REALISTISCH (Ø 1.200€ GW-DB1):   486k € (1,6%)  ✅       │
│  UE OPTIMISTISCH (Ø 1.500€ GW-DB1):  665k € (2,2%)  ✅       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. MONATSZIELE REST (Feb–Aug 2026)

| Marke/Bereich | Stk/Mon | Feb | Mär | Apr | Mai | Jun | Jul | Aug |
|---------------|---------|-----|-----|-----|-----|-----|-----|-----|
| Opel DEG | 22 | 22 | 22 | 22 | 22 | 22 | 21 | 21 |
| Opel Landau | 3 | 3 | 4 | 3 | 3 | 3 | 4 | 3 |
| Leapmotor | 13 | 10 | 11 | 12 | 13 | 14 | 14 | 14 |
| Hyundai | 16 | 15 | 16 | 16 | 16 | 16 | 16 | 16 |
| **NW TOTAL** | **53** | **50** | **53** | **53** | **54** | **55** | **55** | **54** |
| GW | 49 | 47 | 53 | 49 | 49 | 49 | 50 | 43 |
| **GESAMT** | **102** | **97** | **106** | **102** | **103** | **104** | **105** | **97** |

---

## 7. CHECKLISTE FÜR CLAUDE CODE

1. [ ] `CLAUDE.md` lesen für System-Kontext
2. [ ] Migration prüfen: Existieren `abteilungsleiter_planung`, `kst_planung_parameter`?
3. [ ] Alte GJ 2025/26 Plandaten löschen (falls vorhanden)
4. [ ] `kst_planung_parameter` befüllen (Abschnitt 4.3)
5. [ ] `abteilungsleiter_planung` befüllen (Abschnitt 4.4 — Script erstellen)
6. [ ] Validierungs-Queries ausführen (Abschnitt 4.5)
7. [ ] Prüfen ob Frontend die Daten anzeigt: `/planung/abteilungsleiter`
8. [ ] Prüfen ob Gesamtplanung funktioniert: `/planung/gesamtplanung`
9. [ ] Git commit mit TAG-Nummer

---

## 8. WICHTIGE HINWEISE

- **Leapmotor ist NEU** — es gibt keine VJ-Referenzdaten. DB1 von 2.000€/Fzg ist eine konservative Annahme.
- **Umlage beachten**: Hyundai zahlt 50.000 €/Monat Umlage an Stellantis (Konten 498001 / 817051+827051+837051+847051). Bei Konzernansicht (standort=0) neutralisieren sich diese.
- **Neutrales Ergebnis**: -352k€ enthält Zinsen, AfA auf Finanzanlagen etc. — separat zu betrachten, nicht direkt planbar.
- **IST-Werte Sep–Jan**: Die oben genannten IST-Werte (~232 NW, ~260 GW) sind Schätzungen basierend auf BWA-Trend. Für exakte Werte: Query auf `sales` Tabelle mit `out_invoice_date` im Zeitraum Sep 2025 – Jan 2026.
