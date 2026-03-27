# SESSION WRAP-UP TAG 94
**Datum:** 05. Dezember 2025
**Branch:** feature/tag82-onwards
**Fokus:** Kapazitätsplanung Werkstatt - API + Widget

---

## 🎯 ERREICHT

### 1. ✅ API-Endpoints für Kapazitätsplanung
**Datei:** `api/werkstatt_live_api.py`

#### GET /api/werkstatt/live/kapazitaet
- Mechaniker-Verfügbarkeit (mit Arbeitszeiten aus Locosoft)
- Abwesenheiten aus `absence_calendar`
- Offene Aufträge mit Vorgabe-AW
- Auslastungsberechnung pro Betrieb

#### GET /api/werkstatt/live/forecast (MEGA-Endpoint)
- 10-Tage Vorschau (Arbeitstage, ohne Wochenende/Feiertage)
- Tagesweise Kapazität vs. geplante Arbeit
- Warnungen: Unverplant, Überfällig, Teile fehlen
- Teile-Status mit Servicebox-Integration

### 2. ✅ Dashboard komplett überarbeitet
**Datei:** `templates/dashboard.html`

#### Änderungen:
- **Bankensaldo ENTFERNT** (deprimiert nur!)
- **Werkstatt-Kapazität als KPI #1** (Profitabilität!)
- **Kapazitäts-Widget** mit Forecast-Balken
- **Aftersales/Werkstatt aktiviert** (war disabled)
- **Quick Actions** aktualisiert

### 3. ✅ DRIVE Philosophy dokumentiert
**Datei:** `docs/DRIVE_PHILOSOPHY.md`

Kernprinzipien:
- 110% ist das Ziel (nicht 100%)
- Zeige Potenzial, nicht Probleme
- Negativer Saldo = Nicht anzeigen
- Jeder Screen muss zu Handlung führen

---

## 📊 WIDGET-FEATURES

### Kapazitäts-Widget zeigt:
| Element | Beschreibung |
|---------|--------------|
| **KPI: Heute** | Auslastung in % |
| **KPI: Woche** | Wochen-Auslastung |
| **KPI: Unverplant** | Aufträge ohne Termin |
| **KPI: Teile** | Warten auf Teile |
| **Forecast-Bars** | 10 Tage visualisiert |
| **110% Ziel-Linie** | Grün markiert |
| **Warnungen** | Pills oben |
| **Detail-Tables** | Aufklappbar |

### Farb-Schema:
- 🔵 <50% = Unterausgelastet
- 🟢 50-110% = Optimal (ZIEL!)
- 🟡 110-130% = Hoch
- 🔴 >130% = Kritisch

---

## 🚀 DEPLOYMENT

### Dateien im Sync-Ordner:
```
Server/templates/dashboard.html      ← NEU (mit Widget)
Server/docs/DRIVE_PHILOSOPHY.md      ← NEU (Leitlinien)
```

### Auf Server kopieren:
```bash
# Auf 10.80.80.20:
sudo cp /mnt/greiner-portal-sync/templates/dashboard.html /opt/greiner-portal/templates/
sudo cp /mnt/greiner-portal-sync/docs/DRIVE_PHILOSOPHY.md /opt/greiner-portal/docs/

# Restart (nur wenn Python geändert)
# Templates brauchen nur Browser-Refresh!
```

---

## ⚠️ WICHTIG FÜR NÄCHSTE SESSION

### API muss auf Server sein!
Die Endpoints `/api/werkstatt/live/kapazitaet` und `/api/werkstatt/live/forecast` 
müssen in `api/werkstatt_live_api.py` sein und registriert!

Falls Fehler "404" oder "Verbindungsfehler":
1. Prüfen ob API-Datei aktuell ist
2. Prüfen ob Blueprint registriert in `app.py`
3. `systemctl restart greiner-portal`

### Dashboard-JS inline
Das JavaScript ist direkt im Template (kein separates File).
Bei Änderungen: Template editieren, Browser refreshen.

---

## 📝 GIT COMMIT (empfohlen)

```bash
git add templates/dashboard.html
git add docs/DRIVE_PHILOSOPHY.md
git add api/werkstatt_live_api.py
git commit -m "feat(tag94): Werkstatt-Kapazitätsplanung Widget

- API: /api/werkstatt/live/kapazitaet + forecast
- Dashboard: Bankensaldo ersetzt durch Werkstatt-KPI
- Widget: 10-Tage Forecast mit 110% Ziel
- Warnungen: Unverplant, Überfällig, Teile
- Docs: DRIVE_PHILOSOPHY.md (Projektwissen)

110% ist das Ziel! 🔥"
```

---

## 🔜 NÄCHSTE SCHRITTE

1. **Testen** - Dashboard aufrufen, Widget prüfen
2. **Feintuning** - Farben, Layout, Texte
3. **Werkstatt-Übersicht** - Separate Seite mit mehr Details
4. **Auftrag-Click** - Deep-Link zu Locosoft

---

**Status:** ✅ Implementiert, bereit zum Deployen
**Dauer:** ~2 Stunden
**Key Achievement:** DRIVE zeigt jetzt Profitabilität statt Depression! 🚀
