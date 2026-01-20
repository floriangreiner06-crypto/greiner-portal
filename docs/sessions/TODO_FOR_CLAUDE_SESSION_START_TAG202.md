# TODO für Claude Session Start TAG 202

**Erstellt:** 2026-01-20  
**Letzte Session:** TAG 201

---

## 📋 Offene Aufgaben

### 1. Code-Optimierung (Empfohlen)

**VIN-Suche-Logik dupliziert:**
- Problem: VIN-Suche-Logik ist in `get_fahrzeuge_by_marke` und `get_fahrzeug_details` dupliziert
- Lösung: Helper-Funktion `find_vehicle_by_vin(vin)` in `api/bankenspiegel_api.py` erstellen
- Datei: `api/bankenspiegel_api.py`

**Genobank-Zinsberechnung:**
- Problem: Zinsen werden bei jedem API-Call neu berechnet (falls nicht vorhanden)
- Lösung: Zinsen beim Import berechnen und in `fahrzeugfinanzierungen` speichern
- Datei: `scripts/imports/import_genobank_finanzierungen.py`

**Locosoft-Bulk-Abfrage:**
- Problem: Bei Genobank-Marken-Statistik: N+1 Query Problem (jede VIN einzeln abfragen)
- Lösung: Bulk-Abfrage für alle VINs auf einmal
- Datei: `api/bankenspiegel_api.py` (get_einkaufsfinanzierung)

---

### 2. Performance-Optimierung (Optional)

**Caching für Locosoft-Abfragen:**
- Falls Fahrzeugdetails häufig aufgerufen werden, könnte Caching helfen
- Redis oder Memory-Cache für VIN → Fahrzeugdetails

**Index auf fahrzeugfinanzierungen.vin:**
- Prüfen ob Index existiert: `CREATE INDEX IF NOT EXISTS idx_fahrzeugfinanzierungen_vin ON fahrzeugfinanzierungen(vin);`

---

### 3. Validierung & Testing

**Summen-Validierung:**
- Frontend-Validierung: Prüfe ob Summe der Marken-Badges = Gesamtanzahl
- Warnung in Console falls Diskrepanz

**Testanleitung erweitern:**
- Screenshots für Testanleitung hinzufügen
- Test-Checkliste für manuelle Tests

---

## 🔍 Qualitätsprobleme (aus TAG 201)

### ⚠️ Bekannte Issues

1. **VIN-Suche-Logik dupliziert**
   - In `get_fahrzeuge_by_marke` und `get_fahrzeug_details`
   - **Priorität:** Mittel
   - **Empfehlung:** Helper-Funktion erstellen

2. **Genobank-Zinsberechnung**
   - Wird bei jedem API-Call neu berechnet (falls nicht vorhanden)
   - **Priorität:** Niedrig
   - **Empfehlung:** Beim Import berechnen

3. **Locosoft-Abfragen in Schleife**
   - Bei Genobank-Marken-Statistik: N+1 Query Problem
   - **Priorität:** Mittel
   - **Empfehlung:** Bulk-Abfrage

---

## 📝 Wichtige Hinweise für nächste Session

### Aktuelle Features (TAG 201):
- ✅ Genobank-Integration vollständig
- ✅ Fahrzeugdetails-Modal aus Locosoft
- ✅ Zinskosten in allen Modalen
- ✅ Sortierung nach Standzeit
- ✅ Testanleitung erstellt

### Datenquellen:
- **fahrzeugfinanzierungen**: Haupttabelle für Finanzierungsdaten
- **Locosoft**: Fahrzeugdetails (VIN, Modell, Marke, EZ, KM)
- **konten & salden**: Genobank-Konto 4700057908 (sollzins)

### API-Endpunkte:
- `GET /api/bankenspiegel/einkaufsfinanzierung` - Hauptübersicht
- `GET /api/bankenspiegel/einkaufsfinanzierung/fahrzeuge?institut=X&marke=Y` - Fahrzeugliste
- `GET /api/bankenspiegel/fahrzeug-details?vin=XXX` - Einzelfahrzeug-Details

### Wichtige Dateien:
- `api/bankenspiegel_api.py` - Haupt-API (3 Endpunkte)
- `templates/einkaufsfinanzierung.html` - Template mit 2 Modalen
- `static/js/einkaufsfinanzierung.js` - Frontend-Logik
- `scripts/imports/import_genobank_finanzierungen.py` - Genobank-Import

---

## 🐛 Bekannte Bugs

**Keine kritischen Bugs bekannt.**

**Kleinere Issues:**
- Browser-Cache kann alte Daten zeigen (Strg+F5 löst)
- VIN-Suche kann bei sehr kurzen VINs mehrere Treffer finden (LIMIT 1 verhindert)

---

## 📚 Dokumentation

**Erstellt in TAG 201:**
- `docs/TESTANLEITUNG_FAHRZEUGFINANZIERUNGEN.md` - Testanleitung für Verkaufsleitung & Buchhaltung
- Kopiert nach: `/mnt/greiner-portal-sync/docs/` (Windows-Sync)

**Zu aktualisieren:**
- API-Dokumentation (falls vorhanden)
- Code-Kommentare erweitern

---

## 🔄 Nächste Schritte (Priorität)

1. **Hoch:** Code-Optimierung (VIN-Suche Helper-Funktion)
2. **Mittel:** Performance (Bulk-Abfrage für Locosoft)
3. **Niedrig:** Genobank-Zinsen beim Import berechnen

---

**Ende TODO_FOR_CLAUDE_SESSION_START_TAG202**
