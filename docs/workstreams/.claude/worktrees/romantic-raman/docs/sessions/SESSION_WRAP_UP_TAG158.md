# SESSION WRAP-UP TAG 158

**Datum:** 2026-01-02
**Fokus:** Gap-Analyse & Massnahmenplan für 1%-Renditeziel

---

## ERREICHT

### 1. Gap-Analyse erstellt

**Datei:** `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md`

Vollständige Analyse des Geschäftsjahres 2025/26 (Sep-Nov IST):

| Position | IST YTD | Prognose Jahr | Ziel (1%) |
|----------|---------|---------------|-----------|
| Umsatz | 8.413.000 EUR | 33.651.000 EUR | - |
| Unternehmensergebnis | -162.114 EUR | -648.456 EUR | +336.519 EUR |
| **GAP** | - | - | **+984.974 EUR** |

**Benötigt pro Monat:** +109.442 EUR zusätzliches Ergebnis

### 2. GW-Bestand analysiert (Locosoft LIVE)

**131 Gebrauchtwagen auf Lager:**

| Kategorie | Anzahl | Ø Standzeit | Aktion |
|-----------|--------|-------------|--------|
| 0-60 Tage (Frisch) | 62 | 27 Tage | OK |
| 61-90 Tage (OK) | 16 | 81 Tage | Verkauf pushen |
| 91-120 Tage (Risiko) | 16 | 108 Tage | Preis senken |
| 121-180 Tage (Penner) | 20 | 145 Tage | Rabatt-Aktion |
| >180 Tage (Leichen) | 17 | 417 Tage | Händler-VK |

**Standort-Problem:** DEG Opel mit Ø 164 Tagen Standzeit!

### 3. NW-Pipeline analysiert

**229 bestellte Neuwagen** (noch nicht fakturiert):
- DEG Opel: 175 Stk (VK: 5.67 Mio EUR)
- DEG Hyundai: 54 Stk (VK: 2.11 Mio EUR)
- Kalk. DB: ~778.000 EUR

### 4. Bereichs-Performance identifiziert

| Bereich | IST Marge | Ziel | Status |
|---------|-----------|------|--------|
| NW | 10.5% | 8% | ✅ Über Ziel |
| **GW** | **-3.7%** | 6% | 🔴 KRITISCH |
| Teile | 31.9% | 28% | ✅ Über Ziel |
| Werkstatt | 51.5% | 55% | ⚠️ Knapp |

**Hauptproblem: GW mit negativer Marge!**

### 5. Massnahmen-Plan erstellt

**Kurzfristig (Jan-Feb):** +60.000 EUR/Monat
- GW-Leichen verkaufen
- Penner Rabatt-Aktion
- DEG Opel GW-Fokus

**Mittelfristig (Mär-Aug):** +36.000 EUR/Monat
- GW-Einkauf optimieren
- Werkstatt-Marge auf 55%
- Teile-Umsatz +5%

**Potenzial gesamt:** +96.000 EUR/Monat (vs. 109k benötigt)

---

## DATENQUELLEN

### Locosoft (live via SSH)

```sql
-- GW-Bestand
SELECT * FROM dealer_vehicles WHERE out_invoice_date IS NULL AND dealer_vehicle_type = 'G'

-- NW-Pipeline
SELECT * FROM dealer_vehicles WHERE out_invoice_date IS NULL AND dealer_vehicle_type = 'N'
```

### DRIVE Portal

- `unternehmensplan_data.py` - GlobalCube-kompatible BWA
- `werkstatt_data.py::get_mechaniker_leistung()` - Mechaniker-Auswertung
- `controlling_data.py` - TEK-Daten

---

## DATEIEN ERSTELLT/GEÄNDERT

1. `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md` - Vollständiger Massnahmenplan
2. `docs/sessions/SESSION_WRAP_UP_TAG158.md` - Diese Datei
3. `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG159.md` - Nächste Aufgaben

---

## ERKENNTNISSE

### GW ist das Hauptproblem
- -3.7% Marge bedeutet: Jeder verkaufte GW kostet Geld
- 37 Fahrzeuge mit Standzeit >120 Tage binden Kapital
- DEG Opel hat das größte Problem (Ø 164 Tage)

### Swing-Potenzial GW
```
Von -3.7% auf +6% Marge = 9.7 Prozentpunkte
Bei 1.86 Mio EUR Umsatz/Quartal = 180.000 EUR/Quartal Swing
= 720.000 EUR/Jahr Potenzial allein durch GW-Bereinigung
```

### NW läuft gut
- 229 bestellte NW mit ~778k EUR kalkuliertem DB
- Keine Maßnahmen erforderlich

---

## NÄCHSTE SCHRITTE (TAG 159)

1. **GW-Standzeit Dashboard** implementieren
   - Automatische Warnungen für Penner/Leichen
   - Integration in DRIVE

2. **Gap-Tracker** als Endpoint
   - Monatlicher IST vs. SOLL Vergleich
   - Prognose-Berechnung

3. **Abteilungsleiter-Meeting vorbereiten**
   - Ziel-Verteilung präsentieren
   - Maßnahmen-Verantwortung festlegen

---

## PORTAL URLs

- **Unternehmensplan:** https://drive.auto-greiner.de/controlling/unternehmensplan
- **Gap-Analyse Doku:** `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md`

---

*Erstellt: TAG 158 | Autor: Claude AI*
