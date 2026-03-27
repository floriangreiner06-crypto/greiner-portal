# TODO für Claude Session Start (TAG 201)

**Erstellt:** 2026-01-20 (TAG 200)  
**Nächste Session:** TAG 201

---

## 🔍 OFFENE PUNKTE AUS TAG 200

### 1. Termine im grafischen Planer (PRIORITÄT: HOCH)
**Problem:** Termine werden erstellt, erscheinen aber nicht im grafischen Planer

**Vorgehen:**
1. Bestehenden Termin aus Locosoft analysieren:
   ```bash
   python3 scripts/analyse_existing_appointment.py <TERMIN_NR>
   ```
2. Manuellen Termin in Locosoft erstellen (für Auftrag #40167)
3. Termin per SOAP lesen und mit unseren vergleichen
4. Unterschiede identifizieren

**Dokumentation:**
- `docs/TERMIN_PLANER_PROBLEM_ANALYSE_TAG200.md`
- `scripts/analyse_existing_appointment.py`

**Mögliche Lösungen:**
- Workshop/Station-Zuweisung fehlt?
- Mechaniker-Zuweisung fehlt?
- Weitere SOAP-Parameter erforderlich?
- Locosoft-Konfiguration/Filter?

---

## 📋 WEITERE TASKS

### 2. Gudat → Locosoft Sync erweitern
- [ ] Batch-Sync für mehrere Termine
- [ ] Gudat Task-Details holen und übertragen
- [ ] Automatische Synchronisation implementieren

### 3. Kapazitätsplanung validieren
- [ ] Forecast-Daten mit Gudat vergleichen
- [ ] Unverplante Aufträge priorisieren
- [ ] ML-Vorhersagen integrieren

---

## 📁 WICHTIGE DATEIEN

### Session-Wrap-Up:
- `docs/sessions/SESSION_WRAP_UP_TAG200.md`

### Dokumentation:
- `docs/GUDAT_LOCOSOFT_SYNC_TEST_ZUSAMMENFASSUNG_TAG200.md`
- `docs/TERMIN_PLANER_PROBLEM_ANALYSE_TAG200.md`
- `docs/AUSLASTUNG_BERECHNUNG_UNTerschied_TAG200.md`

### Code:
- `api/gudat_locosoft_sync_api.py` - Gudat → Locosoft Sync
- `templates/dashboard.html` - Dashboard Auslastung-Fix

---

## ⚠️ HINWEISE

- Termine werden erfolgreich erstellt (validiert)
- Problem liegt bei Planer-Anzeige (systematische Analyse erforderlich)
- Dashboard zeigt jetzt konsistente Werte
