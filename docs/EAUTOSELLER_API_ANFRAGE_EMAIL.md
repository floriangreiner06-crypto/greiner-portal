# e-autoseller API - Anfrage-E-Mail an Support

**An:** support@eautoseller.de  
**Betreff:** API-Zugang für Greiner Portal DRIVE Integration  
**Datum:** 2026-01-21

---

## E-Mail-Vorlage

```
Hallo Herr Janka,

vielen Dank für Ihre Rückfrage.

Wir benötigen einen **Produktivzugang** für die Integration in unser internes Management-System (Greiner Portal DRIVE).

Für unsere Integration benötigen wir folgende Endpunkte:

### Fahrzeugdaten (Hauptfunktionalität)
- GET /dms/vehicles
  → Liste aller Fahrzeuge abrufen (mit Filtern: offerReference, vin, changedSince, status)
  
- GET /dms/vehicle/{id}
  → Einzelnes Fahrzeug nach ID abrufen
  
- GET /dms/vehicle/{id}/details
  → Detaillierte Fahrzeuginformationen (mit withAdditionalInformation, resolveEquipments)
  
- GET /dms/vehicle/{id}/overview
  → Fahrzeugübersicht

### Preise
- GET /dms/vehicles/prices
  → Alle aktiven Fahrzeuge mit Preisen und Änderungszeitstempeln
  
- GET /dms/vehicles/prices/suggestions
  → Preisvorschläge für aktive Fahrzeuge

### Statistik (optional, für Dashboard-KPIs)
- GET /dms/vehicle/{id}/statistics
  → Fahrzeug-Statistiken (Beta)

### Referenzen (optional, für Dropdown-Filter)
- GET /references/makes
  → Liste aller Marken/Hersteller

### Filialen (optional, für Multi-Standort-Support)
- GET /dms/branches
  → Liste aller Filialen/Standorte

**Zweck der Integration:**
- Automatische Synchronisation des Fahrzeugbestands
- Dashboard mit KPIs (Standzeit, Bestand, etc.)
- Live-Anzeige der Fahrzeugliste im internen Portal
- Standzeit-Überwachung und Alarmierung

**Technische Details:**
- System: Greiner Portal DRIVE (Flask-basierte Web-Anwendung)
- Server: 10.80.80.20 (auto-greiner.de)
- Firma: Autohaus Greiner (Deggendorf, Landau)
- eAutoseller-Instanz: https://greiner.eautoseller.de/

**Zugriff:**
- Automatische Synchronisation alle 15 Minuten (7-18 Uhr, Mo-Fr)
- Manuelle Abfragen über Web-Interface
- Keine Schreibzugriffe (nur GET-Requests)

Falls Sie weitere Informationen benötigen, stehe ich gerne zur Verfügung.

Mit freundlichen Grüßen
[Ihr Name]
Autohaus Greiner
```

---

## Alternative: Kurze Version

```
Hallo Herr Janka,

vielen Dank für Ihre Rückfrage.

Wir benötigen einen **Produktivzugang** für die Integration in unser internes Management-System.

**Benötigte Endpunkte:**

**Fahrzeugdaten:**
- GET /dms/vehicles (Liste aller Fahrzeuge)
- GET /dms/vehicle/{id} (Einzelnes Fahrzeug)
- GET /dms/vehicle/{id}/details (Fahrzeugdetails)
- GET /dms/vehicle/{id}/overview (Fahrzeugübersicht)

**Preise:**
- GET /dms/vehicles/prices (Preise mit Timestamps)
- GET /dms/vehicles/prices/suggestions (Preisvorschläge)

**Optional (für erweiterte Features):**
- GET /dms/vehicle/{id}/statistics (Statistiken)
- GET /references/makes (Marken-Referenzen)
- GET /dms/branches (Filialen)

**Zweck:** Automatische Synchronisation des Fahrzeugbestands für Dashboard und Standzeit-Überwachung.

**System:** Greiner Portal DRIVE (https://greiner.eautoseller.de/)

Mit freundlichen Grüßen
[Ihr Name]
```

---

## Priorisierung der Endpunkte

### PRIO 1 (Essentiell) ⭐⭐⭐
- `GET /dms/vehicles` - Fahrzeugliste (Hauptendpunkt)
- `GET /dms/vehicle/{id}/details` - Fahrzeugdetails
- `GET /dms/vehicles/prices` - Preise

### PRIO 2 (Wichtig) ⭐⭐
- `GET /dms/vehicle/{id}/overview` - Fahrzeugübersicht
- `GET /dms/vehicle/{id}` - Einzelnes Fahrzeug

### PRIO 3 (Optional) ⭐
- `GET /dms/vehicle/{id}/statistics` - Statistiken (Beta)
- `GET /references/makes` - Marken-Referenzen
- `GET /dms/branches` - Filialen
- `GET /dms/vehicles/prices/suggestions` - Preisvorschläge

---

## Hinweise für die E-Mail

1. **Produktivzugang:** Klarstellen, dass wir Produktivzugang benötigen
2. **Endpunkte auflisten:** Alle benötigten Endpunkte explizit nennen
3. **Zweck erklären:** Warum wir die API nutzen (Dashboard, Synchronisation)
4. **Technische Details:** System-Informationen bereitstellen
5. **Zugriff:** Nur GET-Requests, keine Schreibzugriffe

---

## Nach der Freischaltung

1. **Credentials speichern:**
   - In `config/credentials.json` (ApiKey, ClientSecret)
   - Oder als Environment Variables

2. **API-Client erweitern:**
   - Neue Methoden in `lib/eautoseller_client.py`
   - Authentifizierung via Header (ApiKey, ClientSecret)

3. **Integration testen:**
   - Endpoints testen
   - Datenvalidierung
   - Fehlerbehandlung

4. **Migration:**
   - Schrittweise von HTML-Parsing zu Swagger-API
   - HTML als Fallback behalten

---

**Erstellt:** 2026-01-21  
**Status:** ⏳ Warten auf API-Credentials nach E-Mail-Versand
