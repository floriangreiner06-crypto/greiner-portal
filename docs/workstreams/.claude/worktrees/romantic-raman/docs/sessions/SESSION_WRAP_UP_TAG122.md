# SESSION WRAP-UP TAG 122

**Datum:** 2025-12-16
**Schwerpunkt:** SB-Rolle, times-Tabelle Analyse, DRIVE Kapazität mit Abwesenheiten

---

## Erledigte Aufgaben

### 1. Serviceberater (SB) Rolle in DRIVE

**Personalisiertes SB-Dashboard `/mein-bereich`:**
- Dynamische Startseite nach LDAP-Login basierend auf `portal_role`
- KPI-Badges: Erreichung, Rang, Prognose, Trend
- Quick-Links zu Team-Ranking, Werkstatt Live, Urlaubsplaner

**Dateien:**
- `templates/sb/mein_bereich.html` - NEU
- `app.py` - Route `/mein-bereich` + dynamische `/start` Route
- `api/serviceberater_api.py` - `/mein-dashboard` Endpoint
- `config/roles_config.py` - SB-Konfiguration

**SB-Zuordnung:**
```python
SERVICEBERATER_CONFIG = {
    4000: {'name': 'Herbert Huber', 'standort': 'deggendorf'},
    4005: {'name': 'Andreas Kraus', 'standort': 'deggendorf'},
    5009: {'name': 'Valentin Salmansberger', 'standort': 'deggendorf'},
    4002: {'name': 'Leonhard Keidl', 'standort': 'landau'},
    4003: {'name': 'Edith Egner', 'standort': 'landau'},
    5003: {'name': 'Walter Smola', 'standort': 'landau'},
    1006: {'name': 'Stephan Metzner', 'standort': 'landau'},
}
```

---

### 2. Type 1 Anwesenheit entfernt

**Problem:** PostgreSQL `times` Tabelle enthält nur ABGESCHLOSSENE Einträge (mit `end_time`). Während der Arbeitszeit sind keine Type 1 Daten verfügbar.

**Lösung:** Anwesenheits-Report aus UI entfernt:
- Navigation Link aus `base.html` entfernt
- Badge aus `dashboard.html` entfernt
- Route `/werkstatt/anwesenheit` redirected mit Flash-Nachricht
- API Endpoint mit Deprecation Notice versehen

---

### 3. Gudat API Fixes

**Pfad-Fix in `kapazitaetsplanung.html`:**
```javascript
// Vorher (falsch):
'/api/werkstatt/gudat/kapazitaet'
// Nachher (korrekt):
'/api/werkstatt/live/gudat/kapazitaet'
```

**Kapazitäts-Berechnung korrigiert:**
- Nur INTERNE Teams für Kapazität: `{2, 3, 5}` (Allg. Reparatur, Diagnose, NW/GW)
- Externe Teams werden nicht mehr addiert

---

### 4. times-Tabelle Analyse (WICHTIG!)

**Entdeckung:** Die `times` Tabelle existiert im **`private`** Schema!

```sql
-- Tabelle existiert:
SELECT * FROM pg_tables WHERE tablename = 'times';
-- Ergebnis: schemaname = 'private'

-- Aber KEINE Berechtigung:
SELECT * FROM private.times LIMIT 1;
-- FEHLER: keine Berechtigung für Schema private
```

**Lösung erforderlich vom Locosoft-Admin:**
```sql
GRANT USAGE ON SCHEMA private TO loco_auswertung_benutzer;
GRANT SELECT ON private.times TO loco_auswertung_benutzer;
```

**Workaround implementiert:**
- `/api/werkstatt/live/auftraege-enriched` arbeitet jetzt ohne `times`
- Verwendet `labours.is_invoiced` für abgerechnete Zeit-Schätzung

---

### 5. DRIVE Kapazität mit Abwesenheiten

**Neues Feature:** Dynamische Kapazitätsberechnung basierend auf:
- Anzahl aktive Mechaniker pro Betrieb (aus `employees_history`)
- Abwesenheiten aus `absence_calendar` (Urlaub, Krankheit, Schule, etc.)
- 10 AW pro Mechaniker pro Tag als Basis

**API Response erweitert:**
```json
{
  "mechaniker_pro_betrieb": {"1": 14, "3": 5},
  "aw_pro_mechaniker": 10,
  "tage": [{
    "kapazitaet_aw": 120,
    "kapazitaet_basis_aw": 140,
    "mechaniker": {
      "gesamt": 14,
      "abwesend": 2,
      "verfuegbar": 12,
      "gruende": "Url, Krn"
    }
  }]
}
```

**Template aktualisiert:**
- Badge mit Anzahl abwesender Mechaniker
- Kapazität als `120/140 AW` (aktuell/basis)
- Tooltip mit Abwesenheitsgründen

---

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/serviceberater_api.py` | SB-Config, `/mein-dashboard` Endpoint |
| `api/werkstatt_live_api.py` | times-Fallback, DRIVE Kapazität mit Abwesenheiten |
| `app.py` | `/start` dynamisch, `/mein-bereich` Route |
| `config/roles_config.py` | SB Feature-Zugriff |
| `templates/sb/mein_bereich.html` | NEU - SB Dashboard |
| `templates/aftersales/drive_kapazitaet.html` | Abwesenheits-Badges |
| `templates/aftersales/kapazitaetsplanung.html` | Gudat API Pfad Fix |
| `templates/base.html` | Anwesenheits-Link entfernt |
| `templates/dashboard.html` | Anwesenheits-Badge entfernt |

---

## Offene Punkte

### Locosoft-Admin erforderlich:
```sql
GRANT USAGE ON SCHEMA private TO loco_auswertung_benutzer;
GRANT SELECT ON private.times TO loco_auswertung_benutzer;
```

Nach GRANT: Code in `werkstatt_live_api.py` kann auf `private.times` umgestellt werden für echte Stempeluhr-Daten.

---

## Sync-Befehle

```bash
# Bereits synchronisiert:
cp /mnt/greiner-portal-sync/api/werkstatt_live_api.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/templates/aftersales/drive_kapazitaet.html /opt/greiner-portal/templates/aftersales/

# Nach Commit noch syncen:
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/
rsync -av /mnt/greiner-portal-sync/templates/ /opt/greiner-portal/templates/
cp /mnt/greiner-portal-sync/app.py /opt/greiner-portal/
cp /mnt/greiner-portal-sync/config/roles_config.py /opt/greiner-portal/config/

# Neustart erforderlich:
sudo systemctl restart greiner-portal
```

---

## Nächste Session (TAG 123)

- [ ] Locosoft-Admin: GRANT für private.times
- [ ] Nach GRANT: werkstatt_live_api.py auf private.times umstellen
- [ ] SB-Dashboard testen mit echtem Login
- [ ] DRIVE Kapazität mit Abwesenheiten verifizieren
