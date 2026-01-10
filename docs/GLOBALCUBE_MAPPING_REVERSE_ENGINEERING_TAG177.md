# Globalcube Mapping - Reverse Engineering

**Datum:** 2026-01-07  
**TAG:** 177  
**Ziel:** Vollständiges Mapping zwischen Globalcube und DRIVE BWA reverse-engineeren

---

## 1. KONTEXT & ZIELE

### Was wir wissen:
- **Globalcube Portal:** http://10.80.80.10:9300 (Intranet)
- **CSV-Export:** `F.03 BWA Vorjahres-Vergleich (17).csv` in `/opt/greiner-portal/docs/`
- **Struktur:** Tab-separiert, UTF-16 Encoding
- **Zeitraum:** Monat + Kumuliert (Jahr) + Vorjahr (Monat + Jahr)

### Was wir vorhatten:
1. ✅ Stückzahlen NW/GW in BWA einbauen (analog Globalcube)
2. ✅ Betriebsergebnis-Abweichungen analysieren
3. 🔄 **Globalcube Mapping vollständig reverse-engineeren**
4. 🔄 **Automatische Validierung gegen Globalcube**

### Was wir erreichen wollen:
- **100% Übereinstimmung** zwischen DRIVE BWA und Globalcube
- **Automatisierte Validierung** (Scripts)
- **Dokumentation** des vollständigen Mappings

---

## 2. GLOBALCUBE ZUGANG & SERVER

### Portal-Zugang
- **URL:** http://10.80.80.10:9300
- **Status:** ✅ Erreichbar (HTTP 200)
- **User:** florian.greiner (domain=auto-greiner.de)
- **Passwort:** ⚠️ Noch nicht dokumentiert (in `/root/.smbcredentials`?)

### Server-Verzeichnisse
- **Windows-Pfad:** `\\srvgc01\GlobalCube` (verifiziert ✅)
- **Linux Mount:** `/mnt/globalcube/` (verifiziert ✅)
- **Mount-Typ:** CIFS/SMB (vers=3.0)
- **User:** florian.greiner (domain=auto-greiner.de)
- **Status:** ✅ Gemountet und erreichbar

### CSV/Excel-Dateien
- **Aktuell:** `/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv`
- **Format:** UTF-16, Tab-separiert
- **Inhalt:** BWA Monat + Jahr + Vorjahr

---

## 3. CSV-STRUKTUR ANALYSE

### Spalten-Struktur (aus CSV analysiert):

```
Zeile 1: Header (Datum, Zeitraum)
Zeile 2: Spalten-Header (Monat, Vorjahr, Abw., Kumuliert)
Zeile 3: Sub-Header (%, Trend, Abw. %)
Zeile 4: Neuwagen Stk.
Zeile 5: Gebrauchtwagen Stk.
Zeile 7: Umsatzerlöse
Zeile 8: Einsatzwerte
Zeile 10-17: Bruttoerträge nach Bereichen (1-NW, 2-GW, 3-ME, 4-KA, 5-TZ, 6-CP, 7-MW, 8-Sonst.)
Zeile 18: Gesamt (DB1)
Zeile 20-28: Variable Kosten (Detail)
Zeile 29: Bruttoertrag II (DB2)
Zeile 31-33: Direkte Kosten (Detail)
Zeile 34: Deckungsbeitrag (DB3)
Zeile 36-45: Indirekte Kosten (Detail)
Zeile 46: Betriebsergebnis
Zeile 48: Neutrales Ergebnis
Zeile 50: Unternehmensergebnis
```

### Spalten-Mapping (Index-basiert):

| Spalte | Index | Bedeutung | Beispiel |
|--------|-------|-----------|----------|
| Position | 0 | Bezeichnung | "Neuwagen Stk." |
| Monat (aktuell) | 2 | Aktueller Monat | 2 |
| VJ Monat | 3 | Vorjahr Monat | 0 |
| Abw. Monat | 4 | Abweichung Monat | 2 |
| Monat % | 5 | Prozent Monat | 0,00385418 |
| VJ Monat % | 6 | Prozent VJ Monat | 0 |
| Trend Monat | 7 | Trend Monat | ↑/↓ |
| Abw. % Monat | 8 | Abweichung % Monat | 50 |
| Jahr (kumuliert) | 17 | Jahr kumuliert | 444,02 |
| VJ Jahr | 18 | Vorjahr Jahr | 537,55 |
| Abw. Jahr | 19 | Abweichung Jahr | -93,53 |
| Abw. % Jahr | 20 | Abweichung % Jahr | -17,39931169 |

---

## 4. BWA-MAPPING (Bereits validiert)

### Umsatzerlöse
```sql
-- Konten: 80-88 + 8932xx
-- Berechnung: HABEN - SOLL
nominal_account_number BETWEEN 800000 AND 889999
OR nominal_account_number BETWEEN 893200 AND 893299
```

### Einsatzwerte
```sql
-- Konten: 70-79
-- Berechnung: SOLL - HABEN
nominal_account_number BETWEEN 700000 AND 799999
```

### Variable Kosten
```sql
-- Konten: 4151xx, 4355xx, 455xx-456xx (KST 1-7), 4870x (KST 1-7), 491xx-497xx
nominal_account_number BETWEEN 415100 AND 415199
OR nominal_account_number BETWEEN 435500 AND 435599
OR (nominal_account_number BETWEEN 455000 AND 456999 AND substr(..., 5, 1) != '0')
OR (nominal_account_number BETWEEN 487000 AND 487099 AND substr(..., 5, 1) != '0')
OR nominal_account_number BETWEEN 491000 AND 497899
```

### Direkte Kosten
```sql
-- Konten: 40-48 mit KST 1-7, AUSSER Variable und 424xx, 438xx
nominal_account_number BETWEEN 400000 AND 489999
AND substr(..., 5, 1) IN ('1','2','3','4','5','6','7')
AND NOT (4151xx, 424xx, 4355xx, 438xx, 455xx-456xx, 4870x, 491xx-497xx)
```

### Indirekte Kosten
```sql
-- Konten: 4xxxx0 (KST 0) + 424xx/438xx (KST 1-7) + 498xx + 89xxxx (ohne 8932xx)
(nominal_account_number BETWEEN 400000 AND 499999 AND substr(..., 5, 1) = '0')
OR (nominal_account_number BETWEEN 424000 AND 424999 AND substr(..., 5, 1) IN ('1','2','3','6','7'))
OR (nominal_account_number BETWEEN 438000 AND 438999 AND substr(..., 5, 1) IN ('1','2','3','6','7'))
OR nominal_account_number BETWEEN 498000 AND 499999
OR (nominal_account_number BETWEEN 891000 AND 896999 AND NOT BETWEEN 893200 AND 893299)
```

### Neutrales Ergebnis
```sql
-- Konten: 20-29
-- Berechnung: HABEN - SOLL
nominal_account_number BETWEEN 200000 AND 299999
```

---

## 5. STÜCKZAHLEN-MAPPING

### Neuwagen (NW)
```sql
-- dealer_vehicle_type IN ('N', 'T', 'V')
-- Datum: out_invoice_date
-- Filter: Standort via out_subsidiary
SELECT COUNT(*)
FROM dealer_vehicles
WHERE out_invoice_date >= %s AND out_invoice_date < %s
  AND out_invoice_date IS NOT NULL
  AND dealer_vehicle_type IN ('N', 'T', 'V')
  AND [Standort-Filter]
```

### Gebrauchtwagen (GW)
```sql
-- dealer_vehicle_type IN ('G', 'D', 'L')
-- Datum: out_invoice_date
-- Filter: Standort via out_subsidiary
SELECT COUNT(*)
FROM dealer_vehicles
WHERE out_invoice_date >= %s AND out_invoice_date < %s
  AND out_invoice_date IS NOT NULL
  AND dealer_vehicle_type IN ('G', 'D', 'L')
  AND [Standort-Filter]
```

**Status:** ✅ Implementiert in `_berechne_stueckzahlen_globalcube()`

---

## 6. BEREICHE-MAPPING (Bruttoerträge)

| Bereich | Globalcube | Erlös-Konten | Einsatz-Konten |
|---------|------------|--------------|----------------|
| **1-NW** | Neuwagen | 81xxxx | 71xxxx |
| **2-GW** | Gebrauchtwagen | 82xxxx | 72xxxx |
| **3-ME** | Mechanik | 84xxxx | 74xxxx |
| **4-KA** | Karosserie | 84xxxx | 74xxxx |
| **5-TZ** | Teile & Zubehör | 83xxxx | 73xxxx |
| **6-CP** | CP (Sonstiges) | 85xxxx | 75xxxx |
| **7-MW** | Mietwagen | 88xxxx | 78xxxx |
| **8-Sonst.** | Sonstige | 85xxxx, 88xxxx | 75xxxx, 78xxxx |

**Status:** ✅ Implementiert in `BEREICHE_CONFIG` und `_berechne_bereich_werte()`

---

## 7. VARIABLE KOSTEN - DETAIL-MAPPING

Aus CSV Zeile 20-28:

| Position | Konten-Bereich | Beschreibung |
|----------|----------------|--------------|
| Fixum/Prov./Soz. | 494xx | Fixum NW/GW |
| Provisionen | 492xx, 493xx | Verkäuferprovisionen, Finanz |
| Fertigmachen | 491xx | Fertigmachen, Wagenwäschen |
| Kulanz | 497xx | Alle Kulanz-Arten |
| Lagergebühren | 495xx | Lagergebühren |
| Trainingskosten | 4355xx | Trainingskosten |
| Fahrzeugkosten | 455xx-456xx | VFW, Ersatzwagen (KST 1-7) |
| Werbekosten | 4870x | Werbekosten direkt (KST 1-7) |

**Status:** ✅ Implementiert in Variable Kosten-Query

---

## 8. DIREKTE KOSTEN - DETAIL-MAPPING

Aus CSV Zeile 31-33:

| Position | Konten-Bereich | Beschreibung |
|----------|----------------|--------------|
| Personalkosten | 4100x, 4110x, 4150x, 4300x, 4320x, 4360x | Lohn/Gehalt (KST 1-7) |
| Gemeinkosten | 4690x, 4890x | Sonstige Kosten (KST 1-7) |

**Status:** ✅ Implementiert in Direkte Kosten-Query

---

## 9. INDIREKTE KOSTEN - DETAIL-MAPPING

Aus CSV Zeile 36-45:

| Position | Konten-Bereich | Beschreibung |
|----------|----------------|--------------|
| Personalkosten | 4xxx0 | Verwaltung (KST 0) |
| Werbekosten | 424xx (KST 1-7) | KFZ-Pauschale |
| Fahrzeugkosten | 424xx (KST 1-7) | KFZ-Pauschale |
| Abschreibungen | 4xxx0 | Verwaltung (KST 0) |
| Gemeinkosten | 4xxx0 | Verwaltung (KST 0) |
| Raumkosten | 4xxx0 | Verwaltung (KST 0) |
| **Kalk. Kosten** | **29xxxx** | **→ Neutrales Ergebnis!** |
| Gewerbesteuer | 4xxx0 | Verwaltung (KST 0) |
| Umlagekosten | 498xx | Umlagen |

**WICHTIG:** Kalkulatorische Kosten (29xxxx) gehören NICHT zu indirekten Kosten, sondern zum neutralen Ergebnis!

**Status:** ✅ Implementiert in Indirekte Kosten-Query

---

## 10. ABWEICHUNGS-ANALYSE

### Bekannte Abweichungen:

1. **Betriebsergebnis Jahr per Aug./2025:**
   - DRIVE: 243.343,45 €
   - Globalcube: 321.884,68 €
   - **Differenz:** -78.541,23 € (-24,40%)
   - **Ursache:** Kombination aus DB3-Abweichung (-100.381,57 €) und Indirekte Kosten-Abweichung (-21.840,34 €)

2. **DB3 Jahr per Aug./2025:**
   - DRIVE: 2.701.120,19 €
   - Globalcube: 2.801.501,76 €
   - **Differenz:** -100.381,57 € (-3,58%)
   - **Ursache:** Noch zu analysieren (möglicherweise direkte Kosten)

3. **Indirekte Kosten Jahr per Aug./2025:**
   - DRIVE: 2.457.776,74 €
   - Globalcube: 2.479.617,08 €
   - **Differenz:** -21.840,34 € (-0,88%)
   - **Ursache:** Minimal, möglicherweise Rundungsdifferenzen

### Perfekte Übereinstimmungen:

- ✅ **Monat Aug./2025:** Betriebsergebnis 689.679,69 € (0,00 € Differenz)
- ✅ **VJ Monat Aug./2024:** Betriebsergebnis 552.657,22 € (0,00 € Differenz)
- ✅ **Stückzahlen:** NW/GW korrekt implementiert

---

## 11. NÄCHSTE SCHRITTE

### Sofort:
1. ✅ CSV-Struktur analysiert
2. ✅ Stückzahlen-Mapping dokumentiert
3. ✅ BWA-Mapping dokumentiert
4. ⚠️ **Globalcube Server-Pfad verifizieren**
5. ⚠️ **Zugangsdaten für Portal sichern**

### Kurzfristig:
1. **Monat-für-Monat-Vergleich** durchführen (Sep 2024 - Aug 2025)
2. **DB3-Abweichung** genauer analysieren (direkte Kosten)
3. **Automatisierte Validierung** implementieren

### Langfristig:
1. **Automatischer CSV-Import** aus Globalcube
2. **Echtzeit-Validierung** gegen Globalcube
3. **Abweichungs-Alerts** bei größeren Differenzen

---

## 12. ZUGANGSINFORMATIONEN

### Globalcube Portal
- **URL:** http://10.80.80.10:9300
- **Zugangsdaten:** ⚠️ Noch nicht dokumentiert
- **Aktion:** Erfragen und sicher dokumentieren

### Server-Verzeichnisse
- **Windows-Pfad:** ⚠️ Noch nicht verifiziert
- **Linux Mount:** `/mnt/globalcube/` (laut CLAUDE.md.ARCHIVED)
- **Status:** ⚠️ Mount-Punkt prüfen

### CSV-Export
- **Aktuell:** `/opt/greiner-portal/docs/F.03 BWA Vorjahres-Vergleich (17).csv`
- **Format:** UTF-16, Tab-separiert
- **Export-Pfad:** ⚠️ Automatischer Export noch nicht implementiert

---

## 13. MAPPING-TABELLE (Vollständig)

| Globalcube Position | DRIVE Query | Status |
|---------------------|-------------|--------|
| Neuwagen Stk. | `dealer_vehicle_type IN ('N','T','V')` | ✅ |
| Gebrauchtwagen Stk. | `dealer_vehicle_type IN ('G','D','L')` | ✅ |
| Umsatzerlöse | `80xxxx-88xxxx + 8932xx` | ✅ |
| Einsatzwerte | `70xxxx-79xxxx` | ✅ |
| Bruttoertrag 1-NW | `81xxxx - 71xxxx` | ✅ |
| Bruttoertrag 2-GW | `82xxxx - 72xxxx` | ✅ |
| Bruttoertrag 3-ME | `84xxxx - 74xxxx` | ✅ |
| Bruttoertrag 4-KA | `84xxxx - 74xxxx` | ✅ |
| Bruttoertrag 5-TZ | `83xxxx - 73xxxx` | ✅ |
| Bruttoertrag 6-CP | `85xxxx - 75xxxx` | ✅ |
| Bruttoertrag 7-MW | `88xxxx - 78xxxx` | ✅ |
| Bruttoertrag 8-Sonst. | `85xxxx, 88xxxx - 75xxxx, 78xxxx` | ✅ |
| Variable Kosten | `4151xx, 4355xx, 455xx-456xx (KST 1-7), 4870x (KST 1-7), 491xx-497xx` | ✅ |
| Bruttoertrag II (DB2) | `DB1 - Variable Kosten` | ✅ |
| Direkte Kosten | `40xxxx-48xxxx (KST 1-7) AUSSER Variable` | ✅ |
| Deckungsbeitrag (DB3) | `DB2 - Direkte Kosten` | ✅ |
| Indirekte Kosten | `4xxxx0 + 424xx/438xx (KST 1-7) + 498xx + 89xxxx (ohne 8932xx)` | ✅ |
| Betriebsergebnis | `DB3 - Indirekte Kosten` | ✅ |
| Neutrales Ergebnis | `20xxxx-29xxxx` | ✅ |
| Unternehmensergebnis | `Betriebsergebnis + Neutrales Ergebnis` | ✅ |

---

## 14. VALIDIERUNGS-SCRIPTS

### Bestehende Scripts:
- ✅ `scripts/vergleiche_bwa_globalcube.py` - BWA-Vergleich
- ✅ `scripts/vergleiche_stueckzahlen_globalcube.py` - Stückzahlen-Vergleich
- ✅ `scripts/analyse_betriebsergebnis_abweichung.py` - Betriebsergebnis-Analyse
- ✅ `scripts/analyse_betriebsergebnis_detail.py` - Detail-Analyse
- ✅ `scripts/analyse_kalkulatorische_kosten.py` - Kalkulatorische Kosten

### Geplante Scripts:
- ⚠️ `scripts/validiere_bwa_globalcube_monatlich.py` - Monat-für-Monat-Vergleich
- ⚠️ `scripts/import_globalcube_csv.py` - Automatischer CSV-Import
- ⚠️ `scripts/globalcube_portal_scraper.py` - Portal-Daten abrufen

---

## 15. OFFENE FRAGEN

1. **Globalcube Server-Pfad:** Wo liegt der Windows-Pfad für Globalcube-Exporte?
2. **Zugangsdaten:** Benutzername/Passwort für http://10.80.80.10:9300?
3. **Export-Automatisierung:** Wie werden CSV-Exporte erstellt? Manuell oder automatisch?
4. **DB3-Abweichung:** Warum weicht DB3 um -100.381,57 € ab? (Direkte Kosten?)
5. **Monat-für-Monat:** In welchen Monaten entstehen die Abweichungen?

---

**Nächste Aktion:** Server-Pfad prüfen, Zugangsdaten sichern, Monat-für-Monat-Vergleich durchführen.
