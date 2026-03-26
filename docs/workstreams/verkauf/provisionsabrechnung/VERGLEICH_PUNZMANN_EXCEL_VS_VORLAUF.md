# Vergleich Excel vs. DRIVE-Vorlauf – Edeltraud Punzmann (Feb 2026)

**Stand:** 2026-03-02

## Summen

| Kategorie        | Excel (Punzmann) | DRIVE Vorlauf 21 | Anmerkung |
|------------------|------------------|------------------|-----------|
| I. Neuwagen      | 0 €              | 523,53 €         | Excel: 0 Stück NW; DRIVE: IONIQ 5 N (2101200) als I_neuwagen mit 1 % Rg.Netto. Wenn Fahrzeug in Excel als GW geführt wird und P1 hat → DRIVE könnte es als P1 in II buchen (dann 300 € cap). |
| II. Testwagen/VFW| 1.254,45 €       | 1.306,24 €       | Nach Anpassung Max: II in Excel max **500 €**, in DRIVE war max 300 → auf **500** angeglichen. |
| III. Gebrauchtwagen | 1.497,60 €    | 1.198,37 €       | Excel: GW-Block max **300 €** (z. B. IONIQ 5 N 52.352 € → 300 € gedeckelt). DRIVE hatte III max 500 → auf **300** angeglichen. |
| IV. GW aus Bestand | 439,67 €       | 449,92 €         | Geringe Differenz (Rundung/Stück). |
| **Gesamt**       | ~3.191 €         | 3.478,06 €       | |

## Max-Grenzen (Excel vs. DRIVE vor/nach Fix)

| Block              | Excel (Formel)   | DRIVE vorher | DRIVE nach Migration |
|--------------------|------------------|--------------|----------------------|
| II Testwagen/VFW   | min 103, **max 500** | max 300  | **max 500**          |
| III Gebrauchtwagen | min 103, **max 300** | max 500  | **max 300**          |

- **Migration:** `migrations/fix_provision_max_ii_iii_excel.sql`  
- **provision-config:** Unter http://drive/admin/provision-config für **II_testwagen** Max € = **500**, für **III_gebrauchtwagen** Max € = **300** (wie Excel).

## Einzelposition IONIQ 5 N (Balazs-Komforthaus, Rg. 2101200)

- **Excel:** Im **Gebrauchtwagen**-Block, 52.352 € × 1 % = 523,52 € → **auf 300 € begrenzt**.
- **DRIVE (Vorlauf 21):** Als **I_neuwagen** mit 523,53 € (1 % Rg.Netto, keine Deckelung in Kat. I).  
- Wenn dieses Fahrzeug in Locosoft **Memo P1** hat: Nach P1-Logik gehört es in **II** (VFW/TW); dann wird es mit **max 500** (nach Fix) berechnet, also 523 €. Um 1:1 wie Excel (300 €) zu erhalten, müsste es in **III** laufen (max 300) – das entspricht der Excel-Zuordnung „Gebrauchtwagen“. Die fachliche Zuordnung (P1 → II vs. manuell GW in Excel) ggf. mit Dispo/HR klären.

Nach dem Fix (II max 500, III max 300) sollten neue Vorläufe für Februar 2026 in den Grenzen mit dem Excel übereinstimmen. Vorlauf 21 neu erzeugen (löschen + „Vorlauf erstellen“), um die angepassten Werte zu sehen.
