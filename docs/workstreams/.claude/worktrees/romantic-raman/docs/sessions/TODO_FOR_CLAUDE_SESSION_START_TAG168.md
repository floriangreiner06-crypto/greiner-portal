# TODO für Claude - Session Start TAG 168

**Erstellt:** 2026-01-05  
**Nächste Session:** TAG 168

---

## 📋 PRIORITÄTEN

### 🔴 HOCH: Nach großem Test

1. **Test-Ergebnisse auswerten**
   - [ ] Urlaubsplaner: Ansprüche korrekt angezeigt?
   - [ ] Urlaubsplaner: Resturlaub bei Mitarbeiternamen angezeigt?
   - [ ] Urlaubsplaner: Aleyna zeigt "Krankheit" statt "Schulung"?
   - [ ] PostgreSQL-Migration: Alle Views funktionieren?
   - [ ] Jahr 2026: Alle Funktionen funktionieren?

2. **Bugs aus Test beheben**
   - [ ] Kritische Bugs sofort beheben
   - [ ] Mittlere Bugs priorisieren
   - [ ] Kleine Bugs dokumentieren

---

## 🟡 MITTEL: Offene Aufgaben (aus TAG 167)

### Urlaubsplaner

3. **Individuelle Urlaubsansprüche**
   - [ ] Prüfen ob Locosoft-Export möglich ist
   - [ ] Alternative Import-Methode evaluieren
   - [ ] Oder: Manuelle Pflege dokumentieren

4. **Locosoft-Sync verbessern**
   - [ ] Automatischer Sync für neue Buchungen
   - [ ] Diskrepanz-Erkennung (DRIVE vs. Locosoft)
   - [ ] Sync-Status in UI anzeigen

### Abteilungsleiter-Planungstool

5. **Werkstatt-KPIs integrieren** (aus TAG 167 TODO)
   - [ ] Produktivität berechnen (Stempelzeit / Anwesenheit)
   - [ ] Leistungsgrad berechnen (AW × 6 / Stempelzeit)
   - [ ] Auslastung berechnen (Anwesende / Verfügbare)
   - [ ] IST-Werte für Werkstatt erweitern
   - [ ] Vorjahreswerte für Werkstatt-KPIs laden

6. **Teile-KPIs integrieren** (aus TAG 167 TODO)
   - [ ] Lagerumschlag berechnen (Umsatz / Lagerwert)
   - [ ] Penner-Quote berechnen (Langsamdreher / Gesamt-Lagerwert)
   - [ ] Servicegrad berechnen (Sofort verfügbar / Gesamt-Anfragen)
   - [ ] IST-Werte für Teile erweitern
   - [ ] Vorjahreswerte für Teile-KPIs laden

---

## 🟢 NIEDRIG: Nice-to-Have

7. **Urlaubsplaner Verbesserungen**
   - [ ] Bulk-Import aus Locosoft
   - [ ] Export-Funktion
   - [ ] Historie-Vergleich

8. **Dokumentation**
   - [ ] Benutzerhandbuch für Urlaubsplaner
   - [ ] Admin-Dokumentation für Urlaubsansprüche
   - [ ] API-Dokumentation aktualisieren

---

## 🔍 WICHTIGE HINWEISE

### Urlaubsplaner

**PostgreSQL-Migration:**
- ✅ View 2025 korrigiert (PostgreSQL-Syntax)
- ✅ View 2026 erstellt
- ⚠️ Prüfen ob alle Views funktionieren

**Jahr 2026:**
- ✅ View 2026 erstellt
- ✅ Import-Script für 2026
- ✅ API verwendet dynamisches Jahr
- ✅ Frontend verwendet dynamisches Jahr

**Frontend-Mapping:**
- ✅ vacation_type_id 5 = Krankheit (korrigiert)
- ✅ vacation_type_id 9 = Schulung (korrigiert)
- ⚠️ Prüfen ob alle Types korrekt angezeigt werden

**Locosoft-Import:**
- ✅ Berechnungslogik: Standard + Resturlaub
- ⚠️ Individuelle Ansprüche müssen manuell gepflegt werden

### Abteilungsleiter-Planungstool

**Status:** ✅ Grundfunktionalität implementiert (TAG 166)

**Placeholder-Werte:**
- ⚠️ Werkstatt: Produktivität, Leistungsgrad, Auslastung
- ⚠️ Teile: Lagerumschlag, Penner-Quote, Servicegrad

**Datenquellen:**
- `werkstatt_data.py` - Werkstatt-KPIs
- `teile_data.py` - Teile-KPIs
- `api/abteilungsleiter_planung_data.py` - SSOT für Planung

---

## 🐛 BEKANNTE ISSUES

### Urlaubsplaner

1. **Individuelle Urlaubsansprüche**
   - Status: ⚠️ Manuelle Pflege erforderlich
   - Action: Prüfen ob Locosoft-Export möglich
   - Priorität: 🟡 MITTEL

2. **Locosoft-Sync**
   - Status: ⚠️ Kein automatischer Sync
   - Action: Sync-Logik implementieren
   - Priorität: 🟡 MITTEL

### Abteilungsleiter-Planungstool

3. **Werkstatt-KPIs (Placeholder)**
   - Status: ⚠️ Placeholder-Werte
   - Action: Aus `werkstatt_data.py` laden
   - Priorität: 🔴 HOCH

4. **Teile-KPIs (Placeholder)**
   - Status: ⚠️ Placeholder-Werte
   - Action: Aus `teile_data.py` laden
   - Priorität: 🔴 HOCH

---

## 📚 DOKUMENTATION

**Erstellt in TAG 167:**
- `docs/sessions/URLAUBSPLANER_GENEHMIGUNG_DEBUG_TAG167.md`
- `docs/sessions/URLAUBSPLANER_POSTGRESQL_MIGRATION_FIX_TAG167.md`
- `docs/sessions/URLAUBSPLANER_ANSPRUECHE_LOCOSOFT_IMPORT_TAG167.md`
- `docs/sessions/URLAUBSPLANER_ALEYNA_BUG_FIX_TAG167.md`
- `docs/sessions/URLAUBSPLANER_HISTORIE_TAG167.md`

**Aktualisiert:**
- `api/vacation_api.py` - Jahr-Default, Logging
- `templates/urlaubsplaner_v2.html` - Jahr-Dynamic, Frontend-Mapping
- Views 2025/2026 - PostgreSQL-Syntax

**Zu erstellen:**
- Benutzerhandbuch für Urlaubsplaner
- Admin-Dokumentation für Urlaubsansprüche
- API-Dokumentation für Urlaubs-API

---

## 🔄 CODE-ÄNDERUNGEN (TAG 167)

**Geänderte Dateien:**
- `api/vacation_api.py` - Jahr-Default, Logging
- `templates/urlaubsplaner_v2.html` - Jahr-Dynamic, Frontend-Mapping

**Neue Dateien:**
- `scripts/migrations/fix_vacation_balance_view_postgresql.sql`
- `scripts/migrations/create_vacation_balance_2026.sql`
- `scripts/migrations/fix_andrea_ulrich_inaktiv.sql`
- `scripts/migrations/fix_edith_anspruch_39.sql`
- `scripts/setup/import_vacation_entitlements_2026_from_locosoft.py`
- Verschiedene Check-Scripts

**Git Status:**
- ✅ Alle Änderungen lokal
- ✅ Server-Sync: Erfolgreich (via scp)
- ⚠️ Git-Commit: Noch nicht committed

---

## 💡 IDEEN FÜR ZUKUNFT

1. **Automatischer Locosoft-Sync**
   - Celery-Task für täglichen Sync
   - Diskrepanz-Erkennung
   - Auto-Korrektur (optional)

2. **Urlaubsplaner-Export**
   - Export nach Excel
   - Export nach PDF
   - Historie-Vergleich

3. **Urlaubsplaner-Analytics**
   - Urlaubsverteilung pro Abteilung
   - Auslastung pro Monat
   - Trends über Jahre

---

**Nächste Session:** TAG 168  
**Fokus:** Test-Ergebnisse auswerten, Bugs beheben, Werkstatt/Teile KPIs integrieren

