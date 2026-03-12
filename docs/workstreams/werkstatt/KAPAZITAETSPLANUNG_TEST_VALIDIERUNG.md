# Kapazitätsplanung – Test & Validierung

**Stand:** 2026-03-12  
**Zweck:** Ansicht war bisher buggy/ungenutzt; mit Filialen-Filter (Deggendorf/Landau) und Gudat pro Center wieder testbar und validierbar machen.

---

## 1. Filialen unterscheiden (Deggendorf / Landau)

- **Filter:** Oben rechts auf der Seite „Kapazitätsplanung“ gibt es das Dropdown **Betrieb** (Alle / Deggendorf / Landau).
- **Werkstatt-Kapazität (10-Tage), Forecast, Listen:** Nutzen bereits `subsidiary` (1 = Deggendorf, 3 = Landau) und werden gefiltert.
- **Gudat Team-Kapazität:** Wird jetzt ebenfalls nach Filiale geladen:
  - **Deggendorf** gewählt → KIC-URL `.../greiner/deggendorf/kic`, Credentials aus `gudat.username/password` oder `gudat.centers.deggendorf`.
  - **Landau** gewählt → KIC-URL `.../greiner/landau/kic`, Credentials aus `gudat.centers.landau` (username/password).
  - **Alle Betriebe** → aktuell Deggendorf (Default).

Die Gudat-Box zeigt den Filialnamen in Klammern an („Gudat Team-Kapazität (Deggendorf)“ bzw. „(Landau)“).

---

## 2. API-Check (manuell / Test)

### Gudat Kapazität pro Center

```bash
# Deggendorf (Default)
curl -s "http://drive/api/werkstatt/live/gudat/kapazitaet" | jq '.success, .kapazitaet, .center'

# Explizit Deggendorf
curl -s "http://drive/api/werkstatt/live/gudat/kapazitaet?subsidiary=1" | jq '.success, .kapazitaet, .center'

# Landau
curl -s "http://drive/api/werkstatt/live/gudat/kapazitaet?subsidiary=3" | jq '.success, .kapazitaet, .center'
```

**Erwartung:**  
- `success: true`  
- `kapazitaet`: Zahl (AW)  
- `center`: `"deggendorf"` oder `"landau"`  
- Bei Landau: Wenn KIC für Landau nicht verfügbar oder Credentials fehlen, kommt ein Fehler (dann `gudat.centers.landau` in `config/credentials.json` prüfen und ggf. KIC-Login für Landau testen).

### Werkstatt-Kapazität (Forecast, KPIs)

```bash
curl -s "http://drive/api/werkstatt/live/kapazitaet?subsidiary=1" | jq '.success, .datum_heute'
curl -s "http://drive/api/werkstatt/live/kapazitaet?subsidiary=3" | jq '.success, .datum_heute'
```

---

## 3. Erwartete Struktur (Gudat Widget)

Das Frontend erwartet von `/api/werkstatt/live/gudat/kapazitaet` mindestens:

| Feld         | Typ    | Beschreibung                    |
|-------------|--------|----------------------------------|
| `success`   | bool   | true bei Erfolg                 |
| `kapazitaet`| number | AW Gesamt (nur interne Teams)   |
| `geplant`   | number | AW verplant                     |
| `frei`      | number | AW frei (negativ = überbucht)   |
| `auslastung`| number | Prozent                         |
| `status`    | string | ok / warning / critical         |
| `teams`     | array  | Team-Objekte (id, name, capacity, planned, free, utilization, status) |
| `woche`     | array  | Tages-Daten (date, capacity, planned, free, utilization, status) |
| `center`    | string | deggendorf | landau (für Anzeige)   |

Bei Fehler: `success: false`, `error: "..."`.

---

## 4. Landau-KIC prüfen

Falls Landau-Daten nicht kommen:

1. **KIC-URL testen:** Im Browser `https://werkstattplanung.net/greiner/landau/kic` aufrufen – ob Login-Seite erscheint.
2. **Credentials:** In `config/credentials.json` unter `external_systems.gudat.centers.landau` müssen `username` und `password` gesetzt sein (gleiche User wie für OAuth oder KIC-Login für Landau).
3. **Gudat-Health pro Center:**  
   `GET /api/gudat/health?center=landau` – wenn 503 oder Fehler, ist der KIC-Login für Landau fehlgeschlagen.

---

## 5. Kurz-Checkliste für Freigabe

- [ ] Filter „Deggendorf“: Gudat-Box zeigt Deggendorf-Zahlen und „(Deggendorf)“.
- [ ] Filter „Landau“: Gudat-Box zeigt Landau-Zahlen und „(Landau)“ oder klare Fehlermeldung (z. B. KIC nicht verfügbar).
- [ ] „Aktualisieren“ lädt alle Blöcke neu (inkl. Gudat) mit dem gewählten Filter.
- [ ] Werkstatt-Kapazität (10-Tage), HEUTE, WOCHE, Listen reagieren auf Filter (subsidiary 1/3).
- [ ] Keine Konsolenfehler im Browser bei Wechsel des Filters und bei Aktualisieren.

---

## 6. Gudat UI vs Drive – Bedeutung der Prozentzahl („28 % von heute“)

### Was die Gudat-UI zeigt

- **Werkstattplanung.net (Gudat):** Pro Team und Tag werden **absolute AW-Werte** angezeigt (z. B. Kapazität, gebucht, frei/überbucht). Es gibt dort **keine Tages-Prozentzahl** in derselben Form wie in Drive; die Farben (rot/grün) zeigen Überbuchung bzw. freie Kapazität.

### Was Drive zeigt (Kapazitätsplanung → „Diese Woche“)

- **Prozent pro Tag (z. B. „28 %“ für HEUTE):** Das ist die **Auslastung** für diesen Tag:
  - **Formel:** `Auslastung = (geplant / Kapazität) × 100`
  - Quelle: Gudat KIC `workload_week_summary` → `get_week_overview()` in `tools/gudat_client.py` → `utilization = total_planned / total_cap * 100`.
- **28 % heißt also:** 28 % der Tageskapazität sind **verplant**, 72 % sind **frei** (nicht „28 % frei“).
- **„X AW frei“ und „Y AW“:** Kommen direkt aus der Gudat-API (`free_workload`, `base_workload`); die Prozentzahl daneben ist immer **Auslastung**, nicht „frei in %“.

### Vergleich Gudat UI ↔ Drive

| Gudat UI | Drive (Deggendorf/Landau) |
|----------|---------------------------|
| AW pro Team und Tag (Tabelle) | Gleiche Quelle (Gudat KIC), aggregiert **über alle Teams pro Tag** |
| Keine Tages-„Auslastung in %“ in derselben Form | Pro Tag: **Auslastung in %** (geplant/Kapazität) + „X AW frei“, „Y AW“ Kapazität |

Zum Abgleich: gleiches Datum und gleicher Betrieb (Deggendorf/Landau) wählen; die Summen „geplant“ und „Kapazität“ über alle Teams in der Gudat-UI sollten mit den Werten in Drive für diesen Tag übereinstimmen (gleiche API-Quelle).

### Optional: Kennzeichnung in der UI

In der Kapazitätsplanung kann bei der Prozentzahl ein Tooltip/Label **„Auslastung“** angezeigt werden, damit klar ist: **nicht** „28 % frei“, sondern **28 % ausgelastet** (72 % frei).
