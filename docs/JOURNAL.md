# Greiner Portal DRIVE - Session Journal

## TAG 112 Teil 2 (2025-12-11)
**Branch:** feature/tag112-onwards

### Themen:
- **Stempeluhr Zeit-Aufschlüsselung:** Heute vs Gesamt auf Auftrag
  - API: Neue Felder `heute_session_min`, `heute_abgeschlossen_min`, `heute_gesamt_min`
  - Frontend: Große Anzeige = HEUTE, kleine Zeile "Ges: X min" = Auftragsfortschritt
  - Fortschrittsbalken basiert auf GESAMT vs Vorgabe (für Mehrtages-Aufträge)

### Beispiel:
```
Litwin,Jaroslaw          44 min    ← Heute
                    Ges: 439 min   ← Auftragsfortschritt (für Vorgabe)
```

### Dateien:
- api/werkstatt_live_api.py (Query erweitert)
- templates/aftersales/werkstatt_stempeluhr.html
- templates/aftersales/werkstatt_stempeluhr_monitor.html

---

## TAG 112 (2025-12-10/11)
**Branch:** feature/tag112-onwards
**Commits:** 9018476, +1 (Frontend Pausiert)

### Themen:
- Werkstatt Dashboard V2 (Gauges, Trend-Chart)
- Stempeluhr Saldo-Bug Fix
- auftrags_art (W/G/T) aus Locosoft
- ist_pausenzeit + Pausen-Banner
- Neue Kategorie "Pausiert/Wartet" (API + Frontend)

### Known Issue:
- Pausiert-Logik zeigt auch Feierabend-MA (TODO)

### Dateien:
- api/werkstatt_live_api.py
- api/werkstatt_api.py
- templates/aftersales/werkstatt_stempeluhr*.html
- docs/SESSION_WRAP_UP_TAG112.md
- docs/WERKSTATT_LEISTUNG_DOKU_TAG112.md

---
