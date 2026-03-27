# TAG 92 - Werkstatt Stempeluhr LIVE

**Datum:** 2025-12-05  
**Status:** ✅ Produktiv

---

## Übersicht

Echtzeit-Monitoring der Mechaniker-Stempelungen mit Leerlauf-Alarm und Kiosk-Modus für Werkstatt-Monitor.

---

## Features

| Feature | Beschreibung |
|---------|-------------|
| **Live Dashboard** | Aktive Mechaniker mit Fortschrittsbalken |
| **Leerlauf-Alarm** | 5min = Orange, 10min = Rot + Sound |
| **Pausenkorrektur** | 12:00-13:00 wird aus Laufzeit abgezogen |
| **Abwesenheiten** | Urlaub, Schule, Krank aus Locosoft |
| **Kiosk-Modus** | Token-Auth ohne Login für Monitor-PC |
| **Standort-Filter** | subsidiary=1 für Deggendorf |

---

## URLs

| URL | Beschreibung |
|-----|-------------|
| `/werkstatt/stempeluhr` | Dashboard (Login erforderlich) |
| `/monitor/stempeluhr?token=XXX` | Kiosk-Modus (Token-Auth) |
| `/monitor/stempeluhr?token=XXX&subsidiary=1` | Nur Deggendorf |

**Token:** `Greiner2024Werkstatt!`

---

## API

```
GET /api/werkstatt/live/stempeluhr?subsidiary=1
```

Response:
```json
{
  "aktive_mechaniker": [...],
  "leerlauf_mechaniker": [...],
  "abwesend_mechaniker": [...],
  "summary": {"aktiv": 7, "leerlauf": 2, "abwesend": 3}
}
```

---

## Ausnahmen (kein Leerlauf-Alarm)

| MA-Nr | Name | Grund |
|-------|------|-------|
| 5028 | Thammer | Azubi |
| 5026 | Suttner | Azubi |
| 5005 | Scheingraber | Werkstattmeister |

Konfiguration in `api/werkstatt_live_api.py`:
```python
AZUBI_MA_NUMMERN = [5028, 5026]
NICHT_PRODUKTIV_MA = [5005]
```

---

## Kiosk-Setup (Windows)

**Dateien:**
```
\\Srvrdb01\Allgemein\Greiner Portal\...\scripts\windows\
├── START_MONITOR.bat          ← Doppelklick
└── werkstatt_monitor_start.ps1
```

**Konfiguration in .ps1:**
```powershell
$SCREEN_WIDTH = 1920
$SCREEN_HEIGHT = 1080
$URL3 = "http://10.80.80.20/monitor/stempeluhr?token=Greiner2024Werkstatt!&subsidiary=1"
```

**Autostart:** Verknüpfung in `shell:startup`

---

## Dateien

```
/opt/greiner-portal/
├── api/werkstatt_live_api.py          # Stempeluhr-API
├── templates/aftersales/
│   ├── werkstatt_stempeluhr.html      # Dashboard (mit Login)
│   └── werkstatt_stempeluhr_monitor.html  # Kiosk-Modus
├── scripts/windows/
│   ├── START_MONITOR.bat
│   └── werkstatt_monitor_start.ps1
└── app.py                              # Routes
```

---

## Alarm-Schwellen

| Leerlauf | Status | Aktion |
|----------|--------|--------|
| < 5 min | Grün | OK |
| 5-10 min | Orange | Warnung |
| > 10 min | Rot | ALARM + Sound |
| Nie gestempelt | Rot | ALARM |

---

## Pausenzeit

- **12:00 - 13:00** wird automatisch abgezogen
- Konfiguration in `api/werkstatt_live_api.py`:
```python
PAUSE_START = time(12, 0)
PAUSE_ENDE = time(13, 0)
PAUSE_DAUER_MIN = 60
```
