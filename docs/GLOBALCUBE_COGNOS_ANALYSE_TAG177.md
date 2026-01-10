# Globalcube Cognos Framework Manager Analyse - TAG 177

## Datum
2025-01-09

## Ziel
Reverse Engineering des Globalcube-Systems (IBM Cognos) zur Identifikation der Filter-Logik für BWA-Berechnungen, insbesondere direkte Kosten.

## Erkenntnisse

### 1. Datenquellen-Struktur

#### LOC_Belege View (`locosoft.LOC_Belege.sql`)
Globalcube verwendet eine View, die `journal_accountings` mit `nominal_accounts` und `accounts_characteristics` verbindet:

```sql
CREATE VIEW locosoft.LOC_Belege AS
SELECT 
    ...
    T1."skr51_cost_center" as "Skr51 Cost Center",
    ...
    { fn CONCAT(
        { fn RTRIM(CAST(CAST(T1."skr51_cost_center" AS INTEGER) AS CHAR(254))) },
        ' - '
    ) },
    T3."skr51_cost_center_name"
    ) } as "KST",
    ...
FROM "dbo"."journal_accountings" T1
    INNER JOIN "dbo"."nominal_accounts" T2 ON ...
    LEFT OUTER JOIN "dbo"."accounts_characteristics" T3 ON ...
WHERE 
    T2."is_profit_loss_account" = 'J'
```

**WICHTIG**: Die View filtert bereits auf `is_profit_loss_account = 'J'` (GuV-Konten)!

### 2. Kostenstellen-Filterung

#### Globalcube (Cognos Framework Manager)
- **Verwendet**: `skr51_cost_center` Feld aus `journal_accountings`
- **KST-Feld**: Wird aus `skr51_cost_center` + Name erstellt
- **Filter**: `left(KST, 1)` oder `left(KST, 2)` für die erste/erste zwei Stellen

#### DRIVE (aktuell)
- **Verwendet**: `substr(CAST(nominal_account_number AS TEXT), 5, 1)` - die 5. Stelle des Kontos
- **Filter**: `IN ('1','2','3','4','5','6','7')` auf der 5. Stelle

### 3. KRITISCHER UNTERSCHIED

**DRIVE filtert nach der 5. Stelle des Kontos, Globalcube filtert nach `skr51_cost_center`!**

Dies könnte die 100k€ Differenz bei direkten Kosten erklären, wenn:
- Konten mit KST 1-7 in der 5. Stelle existieren, aber `skr51_cost_center = 0` oder andere Werte haben
- Konten mit `skr51_cost_center` 1-7 existieren, aber die 5. Stelle des Kontos ist nicht 1-7

### 4. Cognos Framework Manager Model

Das `model.xml` zeigt:
- Query Subjects: `LOC_Belege_NW_GW_VK_Stk_FIBU`, `LOC_Belege_Bilanz`
- Query Items: `KST`, `Kostenstelle`, `Acct Nr`
- Filter-Logik: `left(KST, 1) = '1'` für Kostenstelle 1

### 5. Empfohlene Änderungen

#### Option 1: Filter auf `skr51_cost_center` umstellen
```sql
-- Statt:
AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')

-- Verwenden:
AND skr51_cost_center BETWEEN 1 AND 7
```

#### Option 2: Hybrid-Ansatz
- Primär: `skr51_cost_center BETWEEN 1 AND 7`
- Fallback: Wenn `skr51_cost_center = 0`, dann `substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')`

### 6. Nächste Schritte

1. ✅ Analyse der `skr51_cost_center` Verteilung in `loco_journal_accountings`
2. ✅ Vergleich: Konten mit KST 1-7 in 5. Stelle vs. `skr51_cost_center` 1-7
3. ✅ Identifikation der Differenz-Konten (100k€)
4. ⏳ Anpassung der Filter-Logik in `api/controlling_api.py`
5. ⏳ Validierung gegen Globalcube

## Dateien

- `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql` - Haupt-View
- `/mnt/globalcube/System/LOCOSOFT/Package/model.xml` - Cognos Framework Manager Model
- `/mnt/globalcube/System/LOCOSOFT/Report/` - Cognos Reports (BWA)

## Referenzen

- `docs/GLOBALCUBE_MAPPING_REVERSE_ENGINEERING_TAG177.md` - Vorherige Mapping-Analyse
- `docs/ANALYSE_DB3_ABWEICHUNG_TAG177.md` - DB3-Abweichungsanalyse
