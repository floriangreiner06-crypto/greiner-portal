# TODO FÜR CLAUDE SESSION START - TAG 121

**Erstellt:** 2025-12-16
**Letzte Session:** TAG 120

---

## 1. Offene Aufgaben

### 1.1 Locosoft Anwesenheits-Problem (EXTERN)
- **Status:** Wartet auf Locosoft
- **Problem:** Type 1 (Anwesenheit) wird für Werkstatt-MA (5xxx) nicht in `loco_auswertung_db` exportiert
- **Beweis:** KOMMT-Stempelung existiert in Locosoft UI (Screenshot), fehlt aber in PostgreSQL
- **Aktion:** User muss Locosoft kontaktieren

### 1.2 Werkstatt Tagesbericht Email Script
- **Datei:** `scripts/reports/werkstatt_tagesbericht_email.py`
- **Status:** Lokal erstellt, noch nicht deployed
- **TODO:**
  - [ ] Script auf Server deployen
  - [ ] In Celery Task integrieren
  - [ ] Email-Versand testen

---

## 2. Abgeschlossene Aufgaben (TAG 120)

### 2.1 Scheduler-Cleanup
- Alte system_jobs UI entfernt
- APScheduler Blueprint entfernt
- Nur noch Celery + Flower aktiv

### 2.2 Konsistente AW-Berechnung
- Nachkalkulation zeigt alle AW (nicht nur fakturierte)
- Problemfälle-API auf PostgreSQL migriert
- Status-Badges für Fakturierung + Mechaniker-Zuordnung
- Auftrag-Detail-Modal erweitert

### 2.3 Werkstatt Tagesbericht Fixes
- Azubis aus Top-Mechaniker ausgeschlossen
- Auftragsnummern bei Problemen angezeigt
- Portal-Link korrigiert

---

## 3. Wichtige Dateien dieser Session

```
api/werkstatt_live_api.py          # Nachkalkulation, Problemfälle, Auftrag-Detail
templates/aftersales/werkstatt_tagesbericht.html
templates/aftersales/werkstatt_uebersicht.html
api/admin_api.py                   # Bereinigt
celery_app/tasks.py                # Stellantis-Pfad fix
```

---

## 4. API-Referenz (TAG 120)

### Neue Felder in Auftrags-Responses:
```
fakturiert_aw          - Abgerechnete AW
offen_aw               - Nicht abgerechnete AW
zugeordnet_aw          - AW mit Mechaniker
nicht_zugeordnet_aw    - AW ohne Mechaniker
vollstaendig_abgerechnet  - Boolean
vollstaendig_zugeordnet   - Boolean
```

### Neuer Endpoint:
```
GET /api/werkstatt/live/problemfaelle
- Ersetzt /api/werkstatt/problemfaelle (SQLite)
- PostgreSQL-basiert mit korrekten AW-Daten
```

---

## 5. Bekannte Einschränkungen

### Anwesenheits-Report:
- Zeigt "Type 1 vergessen" für Werkstatt-MA
- Ist KORREKT basierend auf verfügbaren Daten
- Problem liegt bei Locosoft-Export, nicht Portal

---

## 6. Quick-Start Befehle

```bash
# Service-Status
sudo systemctl status greiner-portal

# Logs
journalctl -u greiner-portal -f

# Celery Tasks
/admin/celery/

# Flower Dashboard
:5555
```

---

*Nächste Session: Bei Bedarf*
