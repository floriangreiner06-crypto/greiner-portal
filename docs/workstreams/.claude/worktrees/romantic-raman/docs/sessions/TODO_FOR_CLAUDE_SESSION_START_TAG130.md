# TODO für Session TAG 130

**Erstellt:** 2025-12-19
**Vorgänger:** SESSION_WRAP_UP_TAG129.md

---

## Priorität 1: Sites konsolidieren

Vor User-Onboarding muss das Portal aufgeräumt werden:

1. **Routen-Inventur** - Alle aktiven Routes auflisten
2. **Doppelte/verwaiste Seiten** - Entfernen oder zusammenführen
3. **Navigation** - Klare Struktur, keine toten Links
4. **Feature-Matrix** - Wer nutzt welches Feature ab wann

### Ziel: Schlankes Portal mit 10-15 Kern-Features statt 30+ verstreuten

---

## Priorität 2 (zurückgestellt): Testumgebung für Wartungsplan-Validierung

Das Team soll den Wartungsplan-Scraper validieren können.

### Vorgeschlagene Lösung: Web-UI

```
Route: /test/wartungsplan

Features:
├── VIN eingeben (Textfeld)
├── Dropdown: Aktuelle Werkstatt-Aufträge (VINs aus Gudat)
├── "Abrufen" Button
├── Ergebnis-Anzeige:
│   ├── Fahrzeugdaten (Kennzeichen, EZ, km aus Locosoft)
│   ├── Gefundene Wartungsarbeiten (Liste)
│   ├── Screenshots (Thumbnails, klickbar)
│   └── Raw JSON (aufklappbar)
└── Validierungs-Buttons: "Korrekt ✓" / "Fehlerhaft ✗"
```

### Implementierungs-Schritte

1. Flask-Route `/test/wartungsplan` erstellen
2. Template `test_wartungsplan.html`
3. API-Endpoint zum Abrufen `/api/test/wartungsplan/<vin>`
4. Screenshot-Serving (statisch oder Base64)
5. Feedback-Speicherung (SQLite-Tabelle `wartungsplan_validierung`)

---

## Priorität 2: Batch-Test verschiedener VINs

Verschiedene Fahrzeugtypen testen:
- Alte Opel (W0L-Präfix, vor 2021)
- Neue Opel (VX-Präfix, Stellantis-Ära)
- Verschiedene Modelle (Corsa, Astra, Mokka, Grandland)

### VINs aus Locosoft holen:

```sql
SELECT vin, license_plate, first_registration_date, model_name
FROM vehicles
WHERE vin LIKE 'VX%' OR vin LIKE 'W0L%'
ORDER BY first_registration_date DESC
LIMIT 20;
```

---

## Priorität 3: DRIVE-Integration (später)

Nach erfolgreicher Validierung:
- Wartungsplan an Werkstatt-Auftrag anhängen
- API-Endpoint für DRIVE
- Automatischer Abruf bei Auftragsanlage?

---

## Technische Notizen

### Wartungsplan-Scraper

**Datei:** `tools/scrapers/servicebox_wartungsplan_scraper.py`

**Aufruf:**
```bash
python3 tools/scrapers/servicebox_wartungsplan_scraper.py <VIN>
python3 tools/scrapers/servicebox_wartungsplan_scraper.py <VIN> --visible  # Browser sichtbar
```

**Output:**
- JSON: `/opt/greiner-portal/logs/servicebox_wartungsplaene/wartungsplan_<VIN>.json`
- Screenshots: `/opt/greiner-portal/logs/servicebox_wartungsplaene/*.png`
- HTML: `/opt/greiner-portal/logs/servicebox_wartungsplaene/*.html`

### Formular-Felder im Servicebox

| Feld | Selektor | Wert |
|------|----------|------|
| Einsatzbedingungen | `select[name='selectedPE']` | "Normale Bedingungen" |
| Alter | `#listeAnnees` | 1-20 Jahre |
| km | `#listeKmMiles` | 25.000, 50.000, ... |
| Vidange | `select[name='selectedVidange']` | "Yes" |

**Wichtig:** Nach Auswahl der Einsatzbedingungen 4 Sekunden warten (AJAX lädt Alter/km-Optionen nach).

---

## Offene Fragen

1. Soll das Team nur VINs aus aktuellen Aufträgen testen oder beliebige eingeben können?
2. Wo soll das Validierungs-Feedback gespeichert werden?
3. Sollen fehlerhafte Ergebnisse automatisch gemeldet werden?

---

## Referenzen

- `docs/sessions/SESSION_WRAP_UP_TAG129.md` - Letzte Session
- `docs/GUDAT_VS_LOCOSOFT_SOAP_ANALYSE.md` - SOAP-Erkenntnisse
- `tools/scrapers/servicebox_wartungsplan_scraper.py` - Haupt-Scraper
