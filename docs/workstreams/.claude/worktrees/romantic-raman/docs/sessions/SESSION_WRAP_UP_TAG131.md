# SESSION WRAP-UP TAG 131
**Datum:** 2025-12-20
**Thema:** Ersatzwagen-Kalender PoC mit Carloop-Integration

---

## Erledigte Aufgaben

### 1. Carloop-Scraper erstellt
**Datei:** `tools/carloop_scraper.py`
- Web-Scraper für Carloop (keine API verfügbar)
- Login mit Session-Authentifizierung
- Extrahiert Fahrzeuge (22 Stück) und Reservierungen (15 Stück)
- Parst HTML-Tabellen aus Vermietungsübersicht

### 2. SQLite-Datenmodell für Carloop
**Datei:** `models/carloop_models.py`
- Tabelle `carloop_reservierungen` (Reservierungen mit Status, Kunde, Zeitraum)
- Tabelle `carloop_fahrzeuge` (Fahrzeug-Mapping mit Locosoft-Nr)
- UPSERT-Funktionen für Sync

### 3. Ersatzwagen-API erweitert
**Datei:** `api/ersatzwagen_api.py`
- `POST /api/ersatzwagen/sync` - Carloop scrapen → SQLite speichern
- `GET /api/ersatzwagen/carloop` - Reservierungen aus DB abrufen
- Bestehendes: `/fahrzeuge`, `/kalender`, `/verfuegbar`, `/zuweisen`, `/health`

### 4. Kalender-UI erweitert
**Datei:** `templates/test/ersatzwagen_kalender.html`
- "Carloop Sync" Button zum manuellen Scrapen
- Tabelle mit Carloop-Reservierungen (Kennzeichen, Kunde, Von, Bis, Status)
- Statistik: 21 Ersatzwagen, Frei/Belegt-Anzeige

---

## Fahrzeug-Mapping (Carloop → Locosoft)

| Kennzeichen | Locosoft-Nr | Modell |
|-------------|-------------|--------|
| DEG-OR 33 | 57960 | Astra |
| DEG-OR 44 | 57953 | Astra |
| DEG-OR 50 | 57169 | Grandland |
| DEG-OR 88 | 57959 | Astra L |
| DEG-OR 99 | 57170 | Grandland |
| DEG-OR 106 | 56989 | Astra L |
| DEG-OR 110 | 56969 | Astra L Sports Tourer |
| DEG-OR 113 | 56029 | Frontera |
| DEG-OR 115 | 56740 | Movano |
| DEG-OR 120 | 57932 | Corsa |
| DEG-OR 141 | 57507 | Mokka |
| DEG-OR 155 | 56977 | Combo Life |
| DEG-OR 200 | 57930 | Corsa |
| DEG-OR 222 | 57772 | Mokka |
| DEG-OR 280 | 57505 | Mokka |
| DEG-OR 333 | 58067 | Grandland |
| DEG-OR 444 | 57773 | Corsa |
| DEG-OR 555 | 58124 | Corsa |
| DEG-OR 700 | 58453 | Frontera |
| DEG-OR 796 | 57948 | Corsa Edition |
| DEG-OR 800 | 57945 | Corsa Edition |

---

## Sync-Befehle (für Server)

```bash
# Models-Ordner erstellen (einmalig)
mkdir -p /opt/greiner-portal/models
touch /opt/greiner-portal/models/__init__.py

# Dateien syncen
cp /mnt/greiner-portal-sync/api/ersatzwagen_api.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/tools/carloop_scraper.py /opt/greiner-portal/tools/
cp /mnt/greiner-portal-sync/models/carloop_models.py /opt/greiner-portal/models/
cp /mnt/greiner-portal-sync/templates/test/ersatzwagen_kalender.html /opt/greiner-portal/templates/test/

# Neustart
sudo systemctl restart greiner-portal
```

---

## Erkenntnisse

1. **Carloop hat keine API** - nur Web-Scraping möglich
2. **Bestehende Carloop→Locosoft Integration** auf Port 7100 (nur Kunden/Faktura)
3. **Locosoft SOAP** hat `rentalCar`-Feld in Terminen, aber keine Tarif-Strukturen
4. **DRIVE als Master** für Werkstatt-Ersatzwagen geplant

---

## Offene Punkte für nächste Session

1. Carloop-Sync testen (nach Server-Neustart mit models-Ordner)
2. Automatischen Sync-Job einrichten (Scheduler)
3. Reservierungen nach Locosoft schreiben (SOAP writeAppointment)
4. UI: Drag&Drop Zuweisung Ersatzwagen → Termin

---

## Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `tools/carloop_scraper.py` | Web-Scraper für Carloop |
| `models/carloop_models.py` | SQLite-Tabellen für Carloop-Daten |
| `models/__init__.py` | Modul-Init (auf Server erstellen!) |

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/ersatzwagen_api.py` | +sync, +carloop Endpoints |
| `templates/test/ersatzwagen_kalender.html` | +Sync-Button, +Carloop-Tabelle |

---

## Test-URL
`https://drive.auto-greiner.de/test/ersatzwagen`
