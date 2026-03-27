# SESSION WRAP-UP TAG 120

**Datum:** 2025-12-16
**Schwerpunkt:** Konsistente AW-Berechnung, Scheduler-Cleanup, Werkstatt-Reports

---

## 1. Erledigte Aufgaben

### 1.1 Scheduler-System Konsolidierung
- **Problem:** Drei redundante Scheduler-Systeme liefen parallel (alte system_jobs, APScheduler, Celery)
- **Lösung:**
  - Alte Admin-Templates entfernt: `system_status.html`, `jobs.html`, `job_history.html`
  - `admin_api.py` bereinigt (281 → 47 Zeilen)
  - `admin_routes.py` redirected zu `/admin/celery/`
  - APScheduler Blueprint aus `app.py` entfernt
  - Stellantis-Pfad in `celery_app/tasks.py` korrigiert

### 1.2 Werkstatt Tagesbericht Email
- **Fixes:**
  - Wagner, Lena (5025) zu AZUBI_MA_NUMMERN hinzugefügt
  - Azubis aus Top-Mechaniker-Query ausgeschlossen
  - Auftragsnummern in "Aufmerksamkeit erforderlich" angezeigt
  - Portal-Link korrigiert zu `http://drive.auto-greiner.de`

### 1.3 Konsistente AW-Berechnung (Hauptaufgabe)

#### Problem: Auftrag 219328 mit 4,9% Leistungsgrad
- **Ursache:** Nur 5 von 71 AW waren fakturiert, Rest (66 AW) noch offen
- **Analyse:** Massive Duplikate in times-Tabelle (6316 vs 617 min dedupliziert)

#### Lösung: Alle APIs und Templates vereinheitlicht

**API-Änderungen (`werkstatt_live_api.py`):**

1. **Nachkalkulation** (Zeile 1295):
   - Neue CTE-Felder: `gesamt_aw`, `fakturiert_aw`, `offen_aw`, `zugeordnet_aw`, `nicht_zugeordnet_aw`
   - Boolean: `vollstaendig_abgerechnet`
   - ORDER BY fix: `l.vorgabe_aw` → `l.gesamt_aw`

2. **Auftrag-Detail** (Zeile 1681):
   - AW-Aufschlüsselung in Summen-Sektion
   - Flags: `vollstaendig_abgerechnet`, `vollstaendig_zugeordnet`

3. **Neue Problemfälle-API** (Zeile 1760):
   - `/api/werkstatt/live/problemfaelle` (PostgreSQL-basiert)
   - Ersetzt alte SQLite-Cache-API
   - Zeigt alle AW + Status-Flags

**Template-Änderungen:**

1. **werkstatt_tagesbericht.html:**
   - Neue "Status"-Spalte in Nachkalkulation
   - Badges: "Offen" (gelb), Mechaniker-Zuordnung (blau)
   - Summary zeigt "(X offen)" bei unvollständigen Aufträgen

2. **werkstatt_uebersicht.html:**
   - API-Aufruf geändert: `/api/werkstatt/live/problemfaelle`
   - Status-Spalte mit Tooltips
   - Auftrag-Detail-Modal erweitert mit AW-Aufschlüsselung

### 1.4 Anwesenheits-Report Analyse
- **Problem:** Alle 6 Mechaniker zeigten "Type 1 vergessen"
- **Diagnose:**
  - Type 1 (Anwesenheit) für Werkstatt-MA fehlt in PostgreSQL
  - Büro-MA (z.B. Geppert) haben Type 1
  - KOMMT-Stempelung existiert in Locosoft (Screenshot), aber nicht im Export
- **Ergebnis:** Locosoft-Export-Problem, nicht Portal-Bug
  - Locosoft exportiert Type 1 nicht für Werkstatt-Mitarbeiter (MA 5xxx)

---

## 2. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/werkstatt_live_api.py` | Nachkalkulation, Auftrag-Detail, neue Problemfälle-API |
| `api/admin_api.py` | Bereinigt (nur logs + health) |
| `routes/admin_routes.py` | Redirect zu Celery |
| `app.py` | APScheduler Blueprint entfernt |
| `celery_app/tasks.py` | Stellantis-Pfad korrigiert |
| `templates/aftersales/werkstatt_tagesbericht.html` | Status-Spalte |
| `templates/aftersales/werkstatt_uebersicht.html` | Problemfälle + Detail-Modal |
| `templates/admin/system_status.html` | GELÖSCHT |
| `templates/admin/jobs.html` | GELÖSCHT |
| `templates/admin/job_history.html` | GELÖSCHT |

---

## 3. Neue API-Felder (TAG 120)

### Response-Felder für Aufträge:
```json
{
  "vorgabe_aw": 71.0,           // Alle AW (gesamt)
  "fakturiert_aw": 5.0,         // Bereits abgerechnet
  "offen_aw": 66.0,             // Noch nicht abgerechnet
  "zugeordnet_aw": 60.0,        // Mit Mechaniker
  "nicht_zugeordnet_aw": 11.0,  // Ohne Mechaniker
  "vollstaendig_abgerechnet": false,
  "vollstaendig_zugeordnet": false
}
```

### Summary-Felder:
```json
{
  "anzahl_unvollstaendig": 3,
  "unvollstaendig_fakturiert": 3,
  "unvollstaendig_zugeordnet": 1
}
```

---

## 4. Offene Punkte

### 4.1 Locosoft Anwesenheits-Export
- **Problem:** Type 1 (Anwesenheit) für Werkstatt-MA (5xxx) wird nicht exportiert
- **Aktion:** Locosoft kontaktieren bzgl. Export-Konfiguration
- **Workaround:** Keiner möglich - Daten fehlen in Quelle

### 4.2 Werkstatt Tagesbericht Email
- Script `scripts/reports/werkstatt_tagesbericht_email.py` lokal erstellt
- Muss noch auf Server deployed und in Celery integriert werden

---

## 5. Technische Erkenntnisse

### times-Tabelle Type-Definitionen:
| Type | Bedeutung |
|------|-----------|
| 1 | Gestempelte Anwesenheits-Zeit |
| 2 | Gestempelte Zeit auf Aufträge |
| 3 | Gestempelte Kommt-Zeit (nicht exportiert!) |
| 4 | Gestempelte Geht-Zeit (nicht exportiert!) |

### Datenfluss:
- `loco_auswertung_db` = Batch-Export (nicht Live!)
- Type 2 wird untertägig gesynct
- Type 1 nur für Büro-MA, nicht Werkstatt

---

## 6. Deployment-Status

**Auf Server deployed:**
- `werkstatt_live_api.py` ✓
- `werkstatt_tagesbericht.html` ✓
- `werkstatt_uebersicht.html` ✓

**Neustart durchgeführt:** ✓

---

*Erstellt: 2025-12-16*
