# SESSION WRAP-UP TAG 162

**Datum:** 2026-01-02
**Fokus:** KST-Ziele Dashboard, YTD-Tracking Fixes, Umlage-Neutralisierung

---

## ERLEDIGTE AUFGABEN

### 1. KST-Ziele Dashboard UI

**Neues Template:** `templates/controlling/kst_ziele.html`

- Ampel-Anzeige pro Bereich (Daumen hoch/runter/warnung)
- Progress-Balken mit Zielerreichung
- Tagesziel-Anzeige (Monatsziel / 22 Werktage)
- IST vs. Prognose vs. Ziel pro Bereich
- Handlungsempfehlungen-Panel
- Standort-Filter (Alle/DEG/HYU/LAN)

**Route hinzugefuegt:** `/controlling/kst-ziele`

### 2. Navigation Controlling Dropdown

**base.html** erweitert um kategorisierte Navigation:

```
Controlling
├── Uebersichten
│   ├── Dashboard
│   ├── BWA
│   └── TEK
├── Zielplanung
│   ├── 1%-Ziel (Unternehmensplan)
│   └── KST-Ziele (Tagesstatus)
├── Analysen
│   ├── Zinsen-Analyse
│   ├── Einkaufsfinanzierung
│   └── Jahrespraemie
├── Bankenspiegel
│   ├── Dashboard
│   ├── Kontenuebersicht
│   ├── Transaktionen
│   └── Fahrzeugfinanzierungen
└── Archiv
    └── TEK v1
```

### 3. YTD-Tracking Dezember-Fix

**Problem:** Dezember fehlte im 1%-Ziel YTD-Tracking

**Ursache:** `nur_abgeschlossene=True` schloss Dezember aus (nur 2 Werktage im Januar)

**Loesung:**
- `unternehmensplan_api.py`: `nur_abgeschlossene=False` fuer Dashboard
- `unternehmensplan_data.py`: `get_gap_analyse()` mit `nur_abgeschlossene=False`
- YTD-Kumulierung schliesst laufenden Kalendermonat aus

### 4. Umlage-Neutralisierung (Konzern)

**Problem:** Am Monatsanfang sind KST-Ziele Werte verzerrt wegen fehlender Umlage-Buchung

**Firmenstruktur:**
- **Autohaus Greiner** (Stellantis = Opel + Leapmotor): Hat Personal, erhaelt Umlage
- **Auto Greiner** (Hyundai): Kein Personal, zahlt Umlage

**Umlage-Konten (50.000 EUR/Monat):**
- Erloese bei Autohaus Greiner: 817051, 827051, 837051, 847051
- Kosten bei Auto Greiner: 498001

**Loesung:**
Bei Konzern-Ansicht (standort=0) werden beide Seiten ausgefiltert, da sie sich neutralisieren sollen.

**Geaenderte Dateien:**
- `api/unternehmensplan_data.py`: Umlage-Filter fuer Umsatz und indirekte Kosten
- `api/kst_ziele_api.py`: Umlage-Filter fuer Umsatz-Query

### 5. Hochrechnungsfaktor-Fix

**Problem:** Bei vollem Monat sollte Faktor 1.0 sein

**Loesung in kst_ziele_api.py:**
```python
if tage_mit_daten >= werktage_monat:
    faktor = 1.0  # Monat ist voll, keine Hochrechnung
else:
    faktor = werktage_monat / tage_mit_daten
```

---

## GEAENDERTE DATEIEN

| Datei | Aenderung |
|-------|-----------|
| `api/unternehmensplan_data.py` | Umlage-Konten + Filter (TAG162) |
| `api/unternehmensplan_api.py` | nur_abgeschlossene=False |
| `api/kst_ziele_api.py` | Umlage-Filter + Hochrechnungs-Fix |
| `templates/controlling/kst_ziele.html` | Dashboard UI |
| `templates/base.html` | Controlling Dropdown kategorisiert |
| `routes/controlling_routes.py` | Route /controlling/kst-ziele |

---

## NEUE KONSTANTEN

```python
# api/unternehmensplan_data.py & api/kst_ziele_api.py
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]
UMLAGE_KOSTEN_KONTEN = [498001]
UMLAGE_BETRAG_PRO_MONAT = Decimal('50000')
```

---

## FIRMENSTRUKTUR-DOKUMENTATION

Wichtig fuer zukuenftige Arbeiten:

```
AUTOHAUS GREINER GmbH & Co. KG (Stellantis)
- Marken: Opel + Leapmotor
- Standorte: Deggendorf + Landau
- HAS das Personal (alle Mitarbeiter)
- subsidiary_to_company_ref = 1

AUTO GREINER GmbH & Co. KG (Hyundai)
- Marke: Hyundai
- Standort: Deggendorf
- HAT KEIN eigenes Personal
- subsidiary_to_company_ref = 2
- ZAHLT Umlage an Autohaus Greiner
```

Referenz: `docs/FIRMENSTRUKTUR.md` + `docs/KONTENPLAN_CONTROLLING.md`

---

## NAECHSTE SCHRITTE (TAG 163+)

1. **Taeglich E-Mail-Report:** Script fuer automatischen Versand KST-Status
2. **Ziel-Editor UI:** Matrix zum Bearbeiten der Monatsziele
3. **GW-Dashboard CSV-Export:** Endpoint /api/fahrzeug/gw/export pruefen
4. **Sonstige-Ziel:** Aktuell 12% - pruefen ob realistisch

---

## API-TESTS

```bash
# KST-Ziele Health
curl -s http://localhost:5000/api/kst-ziele/health

# KST-Ziele Dashboard Januar
curl -s 'http://localhost:5000/api/kst-ziele/dashboard?monat=5&standort=0'

# 1%-Ziel YTD
curl -s 'http://localhost:5000/api/unternehmensplan/ytd?gj=2025/26'
```

---

*Erstellt: TAG 162 | Autor: Claude AI*
