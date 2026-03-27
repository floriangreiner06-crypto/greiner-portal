# Werkstatt Kiosk Scripts

Batch-Scripts zum Starten der Werkstatt-Übersichten im Chrome Kiosk-Modus.

## Scripts

| Script | Beschreibung |
|--------|--------------|
| `Stempeluhr_Monitor_Deggendorf.bat` | Stempeluhr (TAG 112) |
| `Liveboard_Monitor_Deggendorf.bat` | Liveboard Gantt-Ansicht (TAG 126) |
| `Liveboard_Monitor_Deggendorf_Karten.bat` | Liveboard Karten-Ansicht (TAG 126) |

## Verwendung

Einfach Doppelklick auf die .bat Datei.

## Beenden

**Alt+F4** - Kiosk beenden

## Autostart einrichten

1. Verknüpfung erstellen
2. Verknüpfung nach `shell:startup` kopieren (Win+R → shell:startup)

## URLs

| Ansicht | URL |
|---------|-----|
| Stempeluhr | `/werkstatt/stempeluhr/monitor?token=XXX&subsidiary=1,2` |
| Liveboard Gantt | `/monitor/liveboard/gantt?token=XXX&betrieb=deg` |
| Liveboard Karten | `/monitor/liveboard?token=XXX&betrieb=deg` |

---
*TAG 126 (2025-12-18)*
