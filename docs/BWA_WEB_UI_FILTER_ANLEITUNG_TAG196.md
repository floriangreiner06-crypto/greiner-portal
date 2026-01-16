# BWA Web-UI Filter-Anleitung - TAG 196

**Datum:** 2026-01-16  
**Zweck:** Anleitung für YTD-Analyse in der Web-UI

---

## 📊 ZEITRAUM FÜR YTD BIS DEZEMBER 2025

### Wirtschaftsjahr-Logik

**Wichtig:** Das Wirtschaftsjahr startet am **1. September**!

**Für YTD bis Dezember 2025:**
- **Wirtschaftsjahr-Start:** 1. September 2024
- **Wirtschaftsjahr-Ende:** 31. August 2025
- **YTD bis Dezember 2025:** 1. September 2024 bis 31. Dezember 2025
- **Zeitraum:** 4 Monate (Sep, Okt, Nov, Dez 2025)

**Berechnung:**
- Dezember 2025 >= September → WJ-Start ist 1. September 2025
- Aber: YTD bis Dezember 2025 bedeutet: Sep 2024 - Dez 2025 (weil wir im WJ 2024/25 sind)

**Korrektur:** 
- Wenn wir im Dezember 2025 sind und YTD bis Dezember 2025 sehen wollen:
- WJ-Start: 1. September 2024 (weil Dezember 2025 im WJ 2024/25 liegt)
- YTD: 1. September 2024 bis 31. Dezember 2025

---

## 🖥️ WEB-UI FILTER EINSTELLUNGEN

### URL: `/controlling/bwa`

### Filter-Optionen:

1. **Monat:** `12` (Dezember)
2. **Jahr:** `2025`
3. **Standort:** 
   - `Alle` (für Gesamtsumme)
   - Oder spezifisch: `Deggendorf`, `Landau`, `Hyundai`
4. **Firma:**
   - `0` = Alle Firmen (Gesamt)
   - `1` = Autohaus Greiner (Opel/Stellantis)
   - `2` = Auto Greiner (Hyundai)
5. **Kostenstellen (KST):**
   - `Alle` (Standard)
   - Oder spezifisch: `KST 0`, `KST 1`, etc.

---

## 📋 KONKRETE EINSTELLUNGEN FÜR YTD-ANALYSE

### Für Gesamtsumme (Alle Firmen, Alle Standorte):

**Filter:**
- **Monat:** 12 (Dezember)
- **Jahr:** 2025
- **Standort:** Alle (kein Filter)
- **Firma:** 0 (Alle Firmen)
- **KST:** Alle

**Erwartete Werte (nach 498001-Korrektur):**
- Indirekte Kosten YTD: **638.937,55 €** (838.937,55 - 200.000)
- Betriebsergebnis YTD: **-205.863,59 €** (-405.863,59 + 200.000)
- GlobalCube Referenz: **-245.733,00 €**
- **Differenz:** **+39.869,41 €** (DRIVE zu positiv)

---

## 🔍 WAS WIRD ANGEZEIGT?

Die BWA v2 zeigt:
- **Monat:** Werte für Dezember 2025
- **Vorjahr:** Werte für Dezember 2024
- **YTD:** Kumulierte Werte vom Wirtschaftsjahr-Start (1. Sep 2024) bis Dezember 2025
- **YTD Vorjahr:** Kumulierte Werte vom Vorjahr (1. Sep 2023 bis Dez 2024)

---

## ⚠️ WICHTIGE HINWEISE

### 1. Wirtschaftsjahr-Start

**Regel:**
- Wenn Monat >= September: WJ-Start ist 1. September desselben Jahres
- Wenn Monat < September: WJ-Start ist 1. September des Vorjahres

**Beispiel für Dezember 2025:**
- Dezember >= September → WJ-Start: 1. September 2025
- **ABER:** YTD bis Dezember 2025 zeigt Sep 2024 - Dez 2025 (weil wir im WJ 2024/25 sind)

### 2. 498001-Korrektur

**Nach Service-Neustart (TAG 196):**
- 498001 wird aus indirekten Kosten ausgeschlossen
- Indirekte Kosten YTD sollten um 200.000 € niedriger sein
- Betriebsergebnis YTD sollte um 200.000 € besser sein

### 3. API-Endpoint

**Direkter API-Aufruf:**
```
GET /api/controlling/bwa/v2?monat=12&jahr=2025&firma=0&standort=0
```

**Response enthält:**
- `monat`: Werte für Dezember 2025
- `ytd`: Kumulierte Werte (Sep 2024 - Dez 2025)
- `vorjahr`: Werte für Dezember 2024
- `ytd_vorjahr`: Kumulierte Werte Vorjahr

---

## 📊 VERGLEICH MIT GLOBALCUBE

### YTD bis Dezember 2025

| Position | DRIVE (nach Korrektur) | GlobalCube | Differenz |
|----------|------------------------|------------|-----------|
| Direkte Kosten YTD | 659.134,64 € | 659.229,00 € | -94,36 € ✅ |
| Indirekte Kosten YTD | 638.937,55 € | 838.944,00 € | -200.006,45 € ⚠️ |
| Betriebsergebnis YTD | -205.863,59 € | -245.733,00 € | +39.869,41 € ⚠️ |

**Hinweis:** Die Indirekte Kosten-Differenz ist noch groß (-200.006,45 €). Das deutet darauf hin, dass 498001 möglicherweise doch nicht korrekt ausgeschlossen wird, oder es gibt weitere Probleme.

---

## 🔧 TROUBLESHOOTING

### Problem: Werte stimmen nicht überein

1. **Service-Neustart prüfen:**
   ```bash
   sudo systemctl status greiner-portal
   ```

2. **Browser-Cache leeren:**
   - Strg+F5 (Hard Refresh)
   - Oder: Inkognito-Modus verwenden

3. **API direkt testen:**
   ```bash
   curl "http://10.80.80.20:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma=0&standort=0"
   ```

### Problem: YTD zeigt falsche Werte

1. **Wirtschaftsjahr-Start prüfen:**
   - Sollte 1. September 2024 sein für Dezember 2025
   - Prüfen in API-Response: `ytd` Werte

2. **498001-Ausschluss prüfen:**
   - Indirekte Kosten YTD sollten 638.937,55 € sein (nicht 838.937,55 €)
   - Wenn 838.937,55 € → 498001 wird noch nicht ausgeschlossen!

---

*Erstellt: TAG 196 | Autor: Claude AI*
