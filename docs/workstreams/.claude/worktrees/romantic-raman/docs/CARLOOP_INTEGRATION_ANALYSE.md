# Carloop Integration Analyse

**Erstellt:** 2025-12-20 (TAG 131)
**Status:** ✅ Locosoft-Schnittstelle bereits aktiv!

---

## Zusammenfassung

| Aspekt | Ergebnis |
|--------|----------|
| **Locosoft-Schnittstelle** | ✅ **Bereits aktiv** (Port 7100) |
| **Kundendaten-Sync** | ✅ Aktiv |
| **Rechnungsdaten-Sync** | ✅ Aktiv |
| **Mietwagen in Locosoft** | ✅ 22 Fahrzeuge vorhanden (Typ G) |
| **SOAP rentalCar Support** | ✅ writeAppointment hat rentalCar-Feld |
| **REST API** | ❌ Nicht vorhanden |

---

## WICHTIG: Bestehende Locosoft-Integration

Im Carloop unter **Firmengruppe > Bearbeiten > Schnittstellen** ist bereits konfiguriert:

| Schnittstelle | Typ | URL | Status |
|--------------|-----|-----|--------|
| Kundendaten | Locosoft Kundenschnittstelle | `http://10.80.80.7:7100` | ✅ aktiv |
| Rechnungsdaten | Locosoft Rechnungsdatenschnittstelle | `http://10.80.80.7:7100` | ✅ aktiv |

**Offene Frage:** Werden Mietwagen-Reservierungen auch synchronisiert?

---

## Mietwagen-Mapping Carloop ↔ Locosoft

| Carloop Kennzeichen | Locosoft Nr | Typ |
|--------------------|-------------|-----|
| DEG-OR33 | 57960 | G |
| DEG-OR44 | 57953 | G |
| DEG-OR50 | 57169 | G |
| DEG-OR88 | 57959 | G |
| DEG-OR99 | 57170 | G |
| DEG-OR106 | 56989 | G |
| DEG-OR110 | 56969 | G |
| DEG-OR113 | 56029 | G |
| DEG-OR115 | 56740 | G |
| DEG-OR120 | 57932 | G |
| DEG-OR141 | 57507 | G |
| DEG-OR155 | 56977 | G |
| DEG-OR200 | 57930 | G |
| DEG-OR222 | 57772 | G |
| DEG-OR280 | 57505 | G |
| DEG-OR333 | 58067 | G |
| DEG-OR444 | 57773 | G |
| DEG-OR555 | 58124 | G |
| DEG-OR700 | 58453 | G |
| DEG-OR796 | 57948 | G |
| DEG-OR800 | 57945 | G |

**Typ G = Gewerblich/Mietwagen**

---

## 1. System-Übersicht

### Was ist Carloop?
- Markenübergreifendes Mietwagensystem von **Opel Rent**
- Betrieben von **FREE2MOVE GERMANY GmbH**
- Web-basierte Oberfläche unter https://www.carloop-vermietsystem.de

### Greiner-Zugang
- **URL:** https://www.carloop-vermietsystem.de
- **Mandant:** Autohaus Greiner GmbH (ID: 729)
- **Credentials:** admin100328 / Opel1234!

---

## 2. API-Analyse

### 2.1 Öffentliche REST API
**Ergebnis: Nicht vorhanden**

Getestete Endpunkte (alle 404):
- `/api/v1/vehicles`, `/api/v1/rentals`
- `/api/vehicles`, `/api/rentals`
- `/rest/vehicles`, `/rest/rentals`
- `/swagger`, `/api-docs`, `/openapi.json`

### 2.2 Interne AJAX-Endpunkte
Die Web-Oberfläche nutzt FullCalendar mit AJAX-Datenquelle:
- `/de/Mobilitaets-Manager/Vermietung/getrentals` → Erfordert 3 Parameter (unbekannt)
- `/de/Mobilitaets-Manager/Vermietung/Plantafel/getevents` → Liefert HTML statt JSON

**Problem:** Die internen Endpunkte sind nicht dokumentiert und liefern ohne spezifische Parameter Fehler.

### 2.3 FREE2MOVE Partner API
**Existiert, aber separater Dienst**

- Dokumentation: https://docs.partner.free2move.com/docs/overview
- Bietet: Rental-Management, Vehicle-Operations, OIDC-Auth
- **Aber:** Vermutlich separate Credentials erforderlich, nicht über Carloop-Login nutzbar

---

## 3. Web-Scraping Möglichkeiten

### 3.1 Fahrzeugliste ✅
Aus der Widget-Konfiguration extrahierbar:

```
DEG-OR33: Astra
DEG-OR44: Astra
DEG-OR88: Astra L Lim. 5-trg.
DEG-OR106: Astra L Lim. 5-trg.
DEG-OR110: Astra L Sports Toure
DEG-OR155: Combo Life E Edition
DEG-OR444: Corsa
DEG-OR800: Corsa F Edition
DEG-OR796: Corsa F Edition
DEG-OR120: Corsa F GS
DEG-OR200: Corsa F GS
DEG-OR555: Corsa F GS
DEG-OR888: Corsa F GS
DEG-OR113: Frontera GS 1.2 100kW
DEG-OR700: Frontera GS 1.2 100kW
DEG-OR333: Grandland 1.2 48V Mild
DEG-OR50: Grandland 1.2 48V Mild
DEG-OR99: Grandland 1.2 48V Mild
DEG-OR280: Mokka GS
DEG-OR141: Mokka GS
DEG-OR222: Mokka GS
DEG-OR115: Movano Kasten H2 35
```

### 3.2 Reservierungen ⚠️
Werden via AJAX dynamisch geladen. Erfordert:
1. Analyse der JavaScript-Konfiguration
2. Nachbau der AJAX-Calls mit korrekten Parametern
3. Regelmäßiges Re-Login (Session-Management)

---

## 4. DMS-Schnittstelle (Betzemeier)

Carloop bietet eine **DMS-Integration** für Betzemeier-Systeme:
- **Kunden-Sync:** Kundendaten werden ausgetauscht
- **Rechnungs-Sync:** Rechnungsdaten fließen ins DMS
- **Kein Duplikat-Erfassung:** Daten nur einmal eingeben

**Relevanz für Greiner:**
Falls Greiner ein Betzemeier-DMS nutzt, könnte die bestehende Schnittstelle genutzt werden.

---

## 5. Locosoft Integration

### SOAP writeAppointment hat Mietwagen-Feld
```xml
<rentalCar>
  <number>int</number>
</rentalCar>
```

**Problem:**
- Locosoft erwartet eine Mietwagen-Nummer
- Carloop verwendet andere IDs (vehicleId)
- Mapping zwischen Systemen erforderlich

---

## 6. Empfehlung

### Option A: Manuelle Synchronisation (minimal)
1. Fahrzeugliste einmal manuell abgleichen
2. Mietwagen in Locosoft mit Carloop-Kennzeichen verknüpfen
3. Nutzer tragen Reservierungen weiterhin manuell ein

### Option B: Web-Scraper für Übersicht (mittel)
1. Scraper liest Carloop-Fahrzeuge regelmäßig aus
2. Anzeige in DRIVE als "Carloop-Übersicht"
3. Keine Schreiboperationen, nur Lesen

### Option C: FREE2MOVE Partner API (aufwändig)
1. Kontakt zu FREE2MOVE aufnehmen
2. Partner-API Zugang beantragen
3. Vollständige Bidirektionale Integration

### Option D: Betzemeier DMS-Schnittstelle prüfen (falls vorhanden)
1. Klären ob Greiner Betzemeier-DMS nutzt
2. Bestehende Schnittstelle analysieren
3. Integration über DMS-Ebene

---

## 7. Technische Dateien

| Datei | Beschreibung |
|-------|--------------|
| `tools/scrapers/carloop_explorer.py` | Erster Exploration-Versuch |
| `tools/scrapers/carloop_api_test.py` | API-Endpunkt Tests |

---

## 8. Offene Fragen

1. Nutzt Greiner ein Betzemeier DMS (werwiso/werwismart)?
2. Hat Greiner direkten Kontakt zu FREE2MOVE für API-Zugang?
3. Wie viele Reservierungen pro Monat? (Aufwand-Nutzen-Verhältnis)
4. Welche Locosoft-Mietwagen-Nummern existieren bereits?

---

## Quellen

- [FREE2MOVE Partner API](https://docs.partner.free2move.com/)
- [Betzemeier Carloop-Schnittstelle](https://www.betzemeier.de/carloop-das-markenuebergreifende-mietwagensystem-die-neue-schnittstelle-ist-ab-sofort-verfuegbar/)
- [Carloop Vermietsystem](https://carloop-vermietsystem.de/)
