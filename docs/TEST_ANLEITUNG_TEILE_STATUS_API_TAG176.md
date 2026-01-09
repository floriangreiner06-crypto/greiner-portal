# Test-Anleitung: Teile-Status API (TAG 176)

**Datum:** 2026-01-09  
**Zweck:** Testen ob der GROUP BY Fix funktioniert

---

## 📋 FEATURES DIE TEILE_STATUS_API VERWENDEN

### 1. **Frontend-Seite: Teile-Status** ✅

**URL:** `/werkstatt/teile-status`

**Route:**
- `routes/werkstatt_routes.py::werkstatt_teile_status()`
- Template: `templates/aftersales/werkstatt_teile_status.html`

**Navigation:**
- Hauptmenü → "After Sales" → "Teile" → "**Teile-Status**"
- Oder direkt: `http://10.80.80.20:5000/werkstatt/teile-status`

**Berechtigung:**
- Benötigt: `current_user.can_access_feature('teilebestellungen')`

---

### 2. **Drive Briefing** (Quick-Link)

**Templates:**
- `templates/aftersales/drive_briefing.html`
- `templates/sb/drive_briefing.html`

**Link:** Button "Teile-Status" im Drive Briefing

---

## 🔌 API-ENDPUNKTE

### 1. `/api/teile/status` (Haupt-Endpoint)

**Methode:** GET

**Query-Parameter:**
- `subsidiary` (optional): Betrieb (1, 2, 3)
- `min_wert` (optional, default: 20): Mindest-Teilewert in Euro
- `min_tage` (optional, default: 0): Mindest-Wartezeit in Tagen
- `limit` (optional, default: 100): Max. Anzahl Ergebnisse
- `sort` (optional, default: `tage_desc`): Sortierung (`tage_desc`, `wert_desc`, `teile_desc`)

**Beispiel:**
```
GET /api/teile/status?subsidiary=1&min_wert=50&min_tage=7&sort=wert_desc
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2026-01-09T20:42:00",
  "filter": {...},
  "summary": {
    "auftraege_gesamt": 42,
    "teile_gesamt": 156,
    "wert_gesamt": 12500.50,
    "kritisch": 5,
    "warnung": 12,
    "normal": 25
  },
  "auftraege": {
    "kritisch": [...],
    "warnung": [...],
    "normal": [...]
  }
}
```

---

### 2. `/api/teile/auftrag/<nr>` (Detail)

**Methode:** GET

**Beispiel:**
```
GET /api/teile/auftrag/220123
```

**Response:**
```json
{
  "success": true,
  "auftrag": {...},
  "fehlende_teile": [
    {
      "part_number": "12345678",
      "bezeichnung": "Bremsbelag",
      "menge": 2,
      "wert": 89.50,
      "lieferant_nr": 7702309,
      "lieferant_name": "BTZ",
      "lieferzeit_tage": 9.2,
      "lieferzeit_prognose": "18.01.2026"
    }
  ],
  "anzahl_fehlend": 3,
  "wert_gesamt": 250.00,
  "frueheste_fertigstellung": {
    "tage": 12,
    "datum": "21.01.2026"
  }
}
```

---

### 3. `/api/teile/lieferanten` (Lieferanten-Statistik)

**Methode:** GET

**Beispiel:**
```
GET /api/teile/lieferanten
```

**Response:**
```json
{
  "success": true,
  "lieferanten": [
    {
      "supplier_number": 7702309,
      "name": "BTZ",
      "avg_tage": 9.2,
      "min_tage": 3,
      "max_tage": 18,
      "anzahl_lieferungen": 4573,
      "kategorie": "schnell",
      "kategorie_icon": "🟢"
    }
  ],
  "anzahl": 16
}
```

**Wichtig:** Dieser Endpoint verwendet auch `load_lieferzeiten()` - sollte jetzt funktionieren!

---

### 4. `/api/teile/kritisch` (Kritische Aufträge)

**Methode:** GET

**Query-Parameter:**
- `subsidiary` (optional): Betrieb (1, 2, 3)

**Beispiel:**
```
GET /api/teile/kritisch?subsidiary=1
```

**Response:**
```json
{
  "success": true,
  "anzahl_kritisch": 5,
  "auftraege": [...]
}
```

---

### 5. `/api/teile/health` (Health-Check)

**Methode:** GET

**Beispiel:**
```
GET /api/teile/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-09T20:42:00",
  "lieferzeiten_cache": 16
}
```

**Wichtig:** `lieferzeiten_cache` sollte > 0 sein (vorher: 0 wegen Fehler)

---

### 6. `/api/teile/reload-cache` (Cache neu laden)

**Methode:** POST

**Beispiel:**
```
POST /api/teile/reload-cache
```

**Response:**
```json
{
  "success": true,
  "message": "Cache neu geladen: 16 Lieferanten"
}
```

---

## 🧪 TEST-ANLEITUNG

### Test 1: Health-Check (Schnelltest)

**Browser:**
```
http://10.80.80.20:5000/api/teile/health
```

**Erwartetes Ergebnis:**
- ✅ `"status": "ok"`
- ✅ `"lieferzeiten_cache": 16` (oder mehr, nicht 0!)

**Vorher (mit Bug):**
- ⚠️ Cache würde 0 sein (Fallback-Werte)

---

### Test 2: Frontend-Seite öffnen

**Browser:**
```
http://10.80.80.20:5000/werkstatt/teile-status
```

**Erwartetes Ergebnis:**
- ✅ Seite lädt ohne Fehler
- ✅ Tabelle zeigt Aufträge mit fehlenden Teilen
- ✅ Filter funktionieren (Betrieb, Min-Wert, Min-Tage)
- ✅ Kategorisierung funktioniert (kritisch/warnung/normal)

**Was prüfen:**
1. **Summary-Karten:** Zeigen korrekte Zahlen
2. **Tabelle:** Zeigt Aufträge mit fehlenden Teilen
3. **Lieferzeiten:** Werden angezeigt (wenn verfügbar)
4. **Keine Fehler:** Browser-Konsole sollte keine Fehler zeigen

---

### Test 3: API direkt testen (curl)

**Status-Endpoint:**
```bash
curl "http://10.80.80.20:5000/api/teile/status?subsidiary=1&min_wert=20&limit=10"
```

**Erwartetes Ergebnis:**
- ✅ `"success": true`
- ✅ `"summary"` enthält Zahlen
- ✅ `"auftraege"` enthält Liste

---

### Test 4: Lieferanten-Endpoint

**Browser:**
```
http://10.80.80.20:5000/api/teile/lieferanten
```

**Erwartetes Ergebnis:**
- ✅ `"success": true`
- ✅ `"lieferanten"` enthält Liste (16 Lieferanten)
- ✅ Jeder Lieferant hat `avg_tage`, `kategorie`, etc.

**Vorher (mit Bug):**
- ❌ Fehler: "column supplier_number must appear in GROUP BY"

---

### Test 5: Cache neu laden

**Browser (POST):**
```
http://10.80.80.20:5000/api/teile/reload-cache
```

**Oder curl:**
```bash
curl -X POST "http://10.80.80.20:5000/api/teile/reload-cache"
```

**Erwartetes Ergebnis:**
- ✅ `"success": true`
- ✅ `"message": "Cache neu geladen: 16 Lieferanten"`
- ✅ Keine Fehler in Logs

---

### Test 6: Auftrag-Detail

**Browser:**
```
http://10.80.80.20:5000/api/teile/auftrag/220123
```

**Erwartetes Ergebnis:**
- ✅ `"success": true`
- ✅ `"fehlende_teile"` enthält Liste
- ✅ Jedes Teil hat `lieferzeit_prognose` (wenn Lieferant bekannt)

---

## ✅ ERFOLGSKRITERIEN

### Nach Fix sollte funktionieren:

- [x] **Health-Check:** `lieferzeiten_cache > 0` (16 Lieferanten)
- [x] **Frontend-Seite:** Lädt ohne Fehler
- [x] **Status-Endpoint:** Gibt Daten zurück
- [x] **Lieferanten-Endpoint:** Funktioniert ohne GROUP BY Fehler
- [x] **Cache reload:** Funktioniert ohne Fehler
- [x] **Logs:** Keine Warnings mehr bei Service-Start

---

## 🐛 WAS WURDE BEHOBEN?

### Vorher (mit Bug):
```
WARNING:api.teile_status_api:Konnte Lieferzeiten nicht laden: 
column "loco_parts_inbound_delivery_notes.supplier_number" must appear 
in the GROUP BY clause
```

**Folge:**
- ❌ Lieferzeiten-Cache wurde nicht geladen
- ❌ Fallback-Werte wurden verwendet (3 hardcoded Lieferanten)
- ❌ Lieferzeiten-Prognosen waren ungenau

### Nachher (mit Fix):
```
INFO:api.teile_status_api:Lieferzeiten geladen: 16 Lieferanten
```

**Ergebnis:**
- ✅ Lieferzeiten-Cache wird korrekt geladen
- ✅ 16 Lieferanten mit echten Daten
- ✅ Lieferzeiten-Prognosen sind genauer

---

## 📊 VERGLEICH VORHER/NACHHER

| Aspekt | Vorher (Bug) | Nachher (Fix) |
|--------|--------------|---------------|
| Cache-Größe | 0 (Fallback) | 16 Lieferanten |
| Lieferanten-Daten | 3 hardcoded | 16 aus DB |
| Lieferzeiten-Prognose | Ungenau | Genauer |
| Logs | WARNING | INFO |
| Frontend | Funktioniert (mit Fallback) | Funktioniert (mit echten Daten) |

---

## 🎯 SCHNELLTEST (2 Min)

1. **Health-Check öffnen:**
   ```
   http://10.80.80.20:5000/api/teile/health
   ```
   ✅ Prüfen: `lieferzeiten_cache` sollte 16 sein

2. **Frontend-Seite öffnen:**
   ```
   http://10.80.80.20:5000/werkstatt/teile-status
   ```
   ✅ Prüfen: Seite lädt, zeigt Daten

3. **Browser-Konsole prüfen:**
   - F12 → Console
   - ✅ Keine Fehler

---

**Status:** ✅ Fix implementiert - Bereit zum Testen!
