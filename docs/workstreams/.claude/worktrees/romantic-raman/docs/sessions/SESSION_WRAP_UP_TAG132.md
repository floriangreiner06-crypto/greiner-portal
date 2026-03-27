# SESSION WRAP-UP TAG 132
**Datum:** 2025-12-22
**Thema:** TEK Daily PDF Reports per E-Mail

---

## Erledigte Aufgaben

### 1. TEK PDF-Generator erstellt
**Datei:** `api/pdf_generator.py`
- Neue Funktion `generate_tek_daily_pdf(data)`
- ReportLab-basiertes PDF mit:
  - Header: TEK - Tägliche Erfolgskontrolle + Monat
  - KPI-Box: DB1, Marge (farbig), Prognose, Breakeven
  - Breakeven-Status-Balken (grün/rot)
  - Bereiche-Tabelle mit Ampel-Status pro Zeile
  - Vergleich vs. Vormonat/Vorjahr
- Hilfsfunktionen: `format_percent()`, `format_currency_short()`

### 2. TEK Daily Report Script
**Datei:** `scripts/send_daily_tek.py`
- Vollständiges Script für täglichen TEK-Versand
- TEST_MODE mit nur einem Empfänger (florian.greiner)
- Standort-Filter: None=Gesamt, 'DEG'=Deggendorf, 'LAN'=Landau
- HTML-E-Mail mit Übersichtstabelle + PDF-Anhang
- Breakeven proportional für Standorte (DEG 75%, LAN 25%)

### 3. Footer-Texte vereinheitlicht
**Dateien:** `pdf_generator.py`, `send_daily_tek.py`, `send_daily_auftragseingang.py`
- "Automatisch generiert von DRIVE"
- "In DRIVE öffnen" (statt "Im Portal öffnen")
- URL: `http://` statt `https://`

---

## Test-Ergebnisse

| Test | Status |
|------|--------|
| TEK Gesamt-Report | OK |
| TEK Landau-Report | OK |
| E-Mail-Versand | OK |
| PDF-Generierung | OK |

---

## Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `scripts/send_daily_tek.py` | TEK Daily Report Script |

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/pdf_generator.py` | +generate_tek_daily_pdf(), Footer-Text |
| `scripts/send_daily_auftragseingang.py` | Footer-Text aktualisiert |

---

## Konfiguration TEK Report

```python
# In scripts/send_daily_tek.py
TEST_MODE = True                    # True = nur Test-Empfänger
TEST_EMPFAENGER = ["florian.greiner@auto-greiner.de"]
TEST_STANDORT = 'LAN'               # None, 'DEG', 'LAN'

# Produktion (später):
PROD_EMPFAENGER = [
    "peter.greiner@auto-greiner.de",
    "florian.greiner@auto-greiner.de",
    "anton.suess@auto-greiner.de",
    "matthias.koenig@auto-greiner.de",
    "christian.aichinger@auto-greiner.de"
]
```

---

## Cronjob (für Produktion)

```bash
# TEK Report täglich 17:30 Mo-Fr
30 17 * * 1-5 /opt/greiner-portal/venv/bin/python /opt/greiner-portal/scripts/send_daily_tek.py >> /opt/greiner-portal/logs/tek_mail.log 2>&1
```

---

## Offene Punkte für nächste Session

1. **TEK Report Produktion aktivieren**
   - TEST_MODE = False setzen
   - Cronjob einrichten
   - Evtl. separate Reports pro Standort?

2. **Carloop-Sync testen** (von TAG131)
   - `/test/ersatzwagen` → "Carloop Sync" klicken

3. **Weitere Reports?**
   - Werkstatt-Report für Serviceleitung?
   - Verkaufs-Report für Verkaufsleitung?

---

## Sync-Befehle

```bash
# Alles syncen
cp /mnt/greiner-portal-sync/api/pdf_generator.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/scripts/send_daily_tek.py /opt/greiner-portal/scripts/
cp /mnt/greiner-portal-sync/scripts/send_daily_auftragseingang.py /opt/greiner-portal/scripts/

sudo systemctl restart greiner-portal
```

---

## Test-URL
- TEK Dashboard: `http://drive.auto-greiner.de/controlling/tek`
