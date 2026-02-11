# TODO für Claude - Session Start TAG 206

**Erstellt:** 2026-01-21  
**Letzte Session:** TAG 205  
**Fokus:** e-autoseller Integration - Swagger-Dokumentation integrieren

---

## 🎯 Hauptziel dieser Session

**e-autoseller Swagger-Dokumentation integrieren und API-Client erweitern**

Der e-autoseller Support hat eine Swagger-Dokumentation bereitgestellt:
- **URL:** https://nx23318.your-storageshare.de/s/o9sWLST3sNHbaAa
- **Passwort:** &$cx!Fu7L9Y99ek

**Aufgaben:**
1. Swagger-Dokumentation herunterladen und analysieren
2. Bestehende e-autoseller Integration prüfen
3. API-Client erweitern basierend auf Swagger-Spezifikation
4. Neue Endpoints implementieren (falls in Swagger dokumentiert)

---

## 📋 Aktueller Stand: e-autoseller Integration

### ✅ Bereits implementiert

#### 1. eAutoseller Client (`lib/eautoseller_client.py`)
- ✅ Login-Funktionalität (Session-basiert)
- ✅ `get_vehicle_list()` - Fahrzeugliste aus HTML parsen
- ✅ `get_dashboard_kpis()` - Dashboard-KPIs via `startdata.asp`
- ✅ HTML-Parsing mit BeautifulSoup
- ✅ Hereinnahme-Datum aus Detail-Seiten abrufen

**Bekannte Endpoints:**
- `/administration/kfzuebersicht.asp` - Fahrzeugliste (HTML)
- `/administration/startdata.asp` - Dashboard-KPIs (Pipe-separated)
- `/administration/modules/carData/dataApi.asp` - Fahrzeugdaten (HTML)

#### 2. eAutoseller API (`api/eautoseller_api.py`)
- ✅ `/api/eautoseller/vehicles` - Fahrzeugliste
- ✅ `/api/eautoseller/kpis` - Dashboard-KPIs
- ✅ `/api/eautoseller/health` - Health-Check
- ✅ Filter: Status, Min/Max Standzeit
- ✅ Standzeit-Berechnung und Status-Kategorisierung

#### 3. Dashboard-Seite
- ✅ Route: `/verkauf/eautoseller-bestand`
- ✅ KPI-Karten (Gesamt, OK, Warnung, Kritisch)
- ✅ Filter-UI
- ✅ Tabelle mit Fahrzeugliste
- ✅ Template: `templates/verkauf_eautoseller_bestand.html`

#### 4. Celery Task
- ✅ `sync_eautoseller_data` - Task erstellt
- ✅ Schedule: Alle 15 Minuten (7-18 Uhr, Mo-Fr)
- ✅ Task-Locking gegen Race Conditions

---

## 🔍 Bekannte e-autoseller APIs (vor Swagger)

### HTML-basierte APIs (aktuell genutzt)
1. **kfzuebersicht.asp** - Fahrzeugliste
   - Format: HTML
   - Parsing: BeautifulSoup
   - Status: ✅ Funktioniert

2. **startdata.asp** - Dashboard-KPIs
   - Format: Pipe-separated Werte
   - Widget-IDs: 201, 202, 203, 204, 205, 206, 207, 210, 211, 212, 215, 225, 226, 228, 229, 231
   - Status: ✅ Funktioniert

3. **dataApi.asp** - Fahrzeugdaten
   - Format: HTML
   - Status: ✅ Funktioniert

### Bekannte APIs (aus Recherche, nicht genutzt)
1. **flashXML API** (`/eaxml` oder `/flashxml`)
   - Format: XML
   - Auth: Benötigt AuthCode
   - Status: ⏳ Nicht implementiert (AuthCode fehlt)

2. **Upload API** (`/api/upload`)
   - Format: CSV
   - Status: ⏳ Nicht implementiert

---

## 📝 Aufgaben für diese Session

### PRIO 1: Swagger-Dokumentation analysieren ⭐⭐⭐

1. **Swagger-Dokumentation herunterladen**
   - URL: https://nx23318.your-storageshare.de/s/o9sWLST3sNHbaAa
   - Passwort: &$cx!Fu7L9Y99ek
   - Format: Wahrscheinlich JSON/YAML (OpenAPI/Swagger)

2. **Dokumentation analysieren**
   - Welche Endpoints sind dokumentiert?
   - Welche Authentifizierung wird verwendet?
   - Welche Datenformate (JSON, XML, etc.)?
   - Welche Parameter werden benötigt?

3. **Dokumentation speichern**
   - Datei: `docs/EAUTOSELLER_SWAGGER_API.md` (oder JSON/YAML)
   - Zusammenfassung der wichtigsten Endpoints

### PRIO 2: API-Client erweitern ⭐⭐

1. **Neue Endpoints implementieren**
   - Basierend auf Swagger-Spezifikation
   - JSON/XML-Parsing (falls vorhanden)
   - Bessere Fehlerbehandlung

2. **Authentifizierung prüfen**
   - Aktuell: Session-basiert
   - Swagger: Möglicherweise Token-basiert oder andere Methode?

3. **Code-Refactoring**
   - Bestehende HTML-Parsing-Logik beibehalten (Fallback)
   - Neue JSON/XML-Endpoints hinzufügen
   - Code-Duplikate vermeiden

### PRIO 3: Integration testen ⭐

1. **Neue Endpoints testen**
   - Mit echten Credentials testen
   - Response-Formate prüfen
   - Fehlerbehandlung testen

2. **Bestehende Funktionalität prüfen**
   - Sicherstellen, dass nichts kaputt geht
   - HTML-Parsing als Fallback behalten

3. **Dokumentation aktualisieren**
   - `docs/EAUTOSELLER_API_ENDPOINTS.md` aktualisieren
   - Neue Endpoints dokumentieren
   - Code-Beispiele hinzufügen

---

## 🔧 Technische Details

### Aktuelle Implementierung

**Login:**
```python
# lib/eautoseller_client.py
client = EAutosellerClient(
    username='fGreiner',
    password='fGreiner12',
    loginbereich='kfz'
)
client.login()  # Session-basiert
```

**Fahrzeugliste:**
```python
vehicles = client.get_vehicle_list(
    active_only=True,
    fetch_hereinnahme=True  # Langsamer, aber vollständig
)
```

**KPIs:**
```python
kpis = client.get_dashboard_kpis()
# Gibt Dict mit widget_201, widget_202, etc. zurück
```

### Credentials
- **Username:** fGreiner
- **Password:** fGreiner12
- **Loginbereich:** kfz
- **Base URL:** https://greiner.eautoseller.de/

**Konfiguration:**
- `config/credentials.json` (falls vorhanden)
- Environment Variables: `EAUTOSELLER_USERNAME`, `EAUTOSELLER_PASSWORD`, `EAUTOSELLER_LOGINBEREICH`

---

## 📚 Referenzen

### Dokumentation
- `docs/EAUTOSELLER_API_ENDPOINTS.md` - Aktuelle Endpoint-Dokumentation
- `docs/EAUTOSELLER_API_ANALYSE_FINAL.md` - Analyse-Ergebnisse
- `docs/EAUTOSELLER_IMPLEMENTATION_COMPLETE.md` - Implementierungs-Status
- `docs/EAUTOSELLER_BROWSER_ANALYSE_ANLEITUNG.md` - Browser-Analyse-Anleitung

### Code-Dateien
- `lib/eautoseller_client.py` - API-Client
- `api/eautoseller_api.py` - Flask API-Endpoints
- `routes/verkauf_routes.py` - Route-Registrierung
- `templates/verkauf_eautoseller_bestand.html` - Dashboard-Template
- `celery_app/tasks.py` - Celery Task

### Scripts
- `scripts/explore_eautoseller_api.py` - API-Exploration
- `scripts/eautoseller_test_apis.py` - API-Tests
- `scripts/eautoseller_complete_api_discovery.py` - API-Discovery

---

## ⚠️ Bekannte Limitationen

### HTML-Parsing
- Fahrzeugliste wird teilweise gefunden (20 Fahrzeuge)
- Parsing muss noch verfeinert werden
- Möglicherweise dynamisches Laden via JavaScript

### API-Format
- Aktuell: HTML-basiert (Parsing erforderlich)
- Erwartung: Swagger zeigt möglicherweise JSON/XML-Endpoints

### Authentifizierung
- Aktuell: Session-basiert (Cookie)
- Swagger: Möglicherweise Token-basiert oder andere Methode

---

## 🎯 Erwartete Ergebnisse

1. **Swagger-Dokumentation analysiert**
   - Datei gespeichert in `docs/`
   - Zusammenfassung erstellt

2. **API-Client erweitert**
   - Neue Endpoints implementiert (falls in Swagger)
   - JSON/XML-Parsing hinzugefügt
   - Bestehende Funktionalität beibehalten

3. **Dokumentation aktualisiert**
   - Neue Endpoints dokumentiert
   - Code-Beispiele hinzugefügt

4. **Tests durchgeführt**
   - Neue Endpoints getestet
   - Bestehende Funktionalität geprüft

---

## 💡 Wichtige Hinweise

1. **Bestehende Funktionalität nicht brechen**
   - HTML-Parsing als Fallback behalten
   - Schrittweise Migration zu neuen APIs

2. **Swagger-Dokumentation kann unvollständig sein**
   - Nicht alle Endpoints sind möglicherweise dokumentiert
   - HTML-basierte APIs weiterhin nutzen, falls nötig

3. **Authentifizierung prüfen**
   - Swagger zeigt möglicherweise andere Auth-Methode
   - Session-basierte Auth beibehalten, falls nötig

4. **Fehlerbehandlung**
   - Graceful Fallback zu HTML-Parsing
   - Gute Fehlermeldungen für Debugging

---

## 🔗 Nächste Schritte

1. **Swagger-Dokumentation herunterladen** (manuell oder via Script)
2. **Dokumentation analysieren** und wichtige Endpoints identifizieren
3. **API-Client erweitern** basierend auf Swagger
4. **Tests durchführen** und Dokumentation aktualisieren

---

**Status:** ⏳ Warten auf Swagger-Dokumentation  
**Nächster Schritt:** Swagger-Dokumentation analysieren
