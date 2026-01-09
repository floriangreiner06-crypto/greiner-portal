# Mobis EDMOS API Analyse - Teilebezug für Hyundai Garantie

**Erstellt:** 2026-01-09 (TAG 175)  
**Ziel:** Teilebezug aus Mobis (EDMOS) für Garantieaufträge nachweisen

---

## 🎯 PROBLEMSTELLUNG

**Hyundai Garantie-Richtlinie 2025-09, Abschnitt 8.2 (Arbeitskarte):**
- ✅ **Pflicht:** Verwendete Hyundai Original-Teile dokumentieren
- ✅ **Pflicht:** Angabe des schadenverursachenden Teiles (Teilenummer)

**Aktuelle Situation:**
- Teile werden aus Locosoft (`parts`-Tabelle) geholt
- **Problem:** Kein Nachweis, dass es Hyundai Original-Teile sind
- **Problem:** Keine Bestätigung des Teilebezugs aus Mobis (EDMOS)

**Ziel:**
- Teilebezug aus Mobis (EDMOS) abrufen
- Nachweis, dass es Hyundai Original-Teile sind
- Integration in Garantieakte-Workflow

---

## 🔍 MOBIS EDMOS SYSTEM

**URL:** https://edos.mobiseurope.com/EDMOSN/gen/index.jsp  
**Login:**
- Benutzer: `G2403Koe`
- Passwort: `Greiner3!`

**EDMOS = Electronic Dealer Management System**
- Mobis Europe Parts System
- Verwaltung von Hyundai Original-Teilen
- Bestellungen, Lieferungen, Lagerbestand

---

## 📋 ZU PRÜFEN BEI API-ANALYSE

### 1. Website-Struktur analysieren
- [ ] Login-Prozess verstehen
- [ ] Session-Management (Cookies, Tokens)
- [ ] Hauptmenü-Navigation
- [ ] Teile-Bereich finden

### 2. API-Endpunkte identifizieren
- [ ] Network-Tab im Browser öffnen (F12 → Network)
- [ ] Nach Login: Alle Requests analysieren
- [ ] Suche nach:
  - REST API Calls (`/api/`, `/rest/`, `/v1/`, etc.)
  - SOAP Services (`.asmx`, `?wsdl`)
  - GraphQL Endpoints
  - AJAX/Fetch Requests (JSON-Responses)

### 3. Teilebezug-Funktionen finden
- [ ] Bestellungen anzeigen
- [ ] Lieferungen anzeigen
- [ ] Teile-Suche
- [ ] Auftragsbezogene Teile
- [ ] Garantie-Teile

### 4. Datenstruktur analysieren
- [ ] Request-Format (JSON, XML, Form-Data)
- [ ] Response-Format
- [ ] Authentifizierung (Token, Session-ID)
- [ ] Parameter (Auftragsnummer, Teilenummer, Datum)

---

## 🔧 MÖGLICHE API-STRUKTUREN

### Option 1: REST API
```
GET /api/parts/orders/{order_number}
GET /api/parts/deliveries?order={order_number}
GET /api/parts/search?part_number={teilenummer}
```

### Option 2: SOAP Service
```
POST /services/PartsService.asmx
Body: <soap:Envelope>...</soap:Envelope>
```

### Option 3: AJAX-Endpoints
```
POST /ajax/getPartsForOrder.do
POST /ajax/getDeliveries.do
```

### Option 4: GraphQL
```
POST /graphql
Query: { parts(orderNumber: "123") { ... } }
```

---

## 📊 BENÖTIGTE DATEN FÜR GARANTIE

### Für jeden Garantieauftrag:
1. **Teilebezug-Liste:**
   - Teilenummer (Hyundai Original)
   - Beschreibung
   - Bestellnummer (Mobis)
   - Lieferdatum
   - Menge
   - Preis (EK)

2. **Schadenverursachendes Teil:**
   - Teilenummer
   - Beschreibung
   - Bestellnummer
   - Lieferdatum

3. **Nachweis:**
   - Mobis Bestellnummer
   - Mobis Lieferschein
   - Bestätigung: Hyundai Original-Teil

---

## 🛠️ INTEGRATION IN DRIVE PORTAL

### 1. Neue API-Datei erstellen
**Datei:** `api/mobis_edmos_api.py`

**Funktionen:**
- `login()` - Authentifizierung
- `get_parts_for_order(order_number)` - Teile für Auftrag
- `get_deliveries(order_number)` - Lieferungen
- `verify_hyundai_original_part(part_number)` - Prüfung Original-Teil

### 2. Integration in Garantieakte-Workflow
**Datei:** `api/garantieakte_workflow.py`

**Erweiterung:**
- Mobis-Teilebezug abrufen
- Mit Locosoft-Teilen abgleichen
- In Garantieakte-PDF einfügen

### 3. Datenbank-Erweiterung (optional)
**Tabelle:** `mobis_teilebezug`

**Felder:**
- `order_number` (INT)
- `part_number` (VARCHAR)
- `mobis_order_number` (VARCHAR)
- `delivery_date` (DATE)
- `is_hyundai_original` (BOOLEAN)
- `created_at` (TIMESTAMP)

---

## 📝 NÄCHSTE SCHRITTE

1. **Manuelle Analyse:**
   - In Mobis einloggen
   - Browser DevTools öffnen (F12)
   - Network-Tab aktivieren
   - Teilebezug für einen Garantieauftrag anzeigen
   - Alle Requests dokumentieren

2. **API-Dokumentation:**
   - Request-URLs notieren
   - Request-Body/Parameters notieren
   - Response-Struktur notieren
   - Authentifizierung verstehen

3. **Test-Integration:**
   - Python-Client erstellen
   - Test-Request senden
   - Response parsen
   - In DRIVE Portal integrieren

---

## 🔗 RELEVANTE DATEIEN

- `api/arbeitskarte_api.py` - Aktuelle Teile-Integration (Locosoft)
- `api/garantieakte_workflow.py` - Garantieakte-Erstellung
- `api/arbeitskarte_pdf.py` - PDF-Generierung mit Teilen
- `docs/hyundai/GARANTIE_DOKUMENTATION_GUDAT_ANALYSE_TAG173.md` - Dokumentationspflichten

---

## ⚠️ HINWEISE

- **Authentifizierung:** Mobis verwendet möglicherweise Session-basierte Auth (Cookies)
- **Rate Limiting:** API könnte Rate Limits haben
- **Datenformat:** Möglicherweise proprietäres Format (nicht Standard JSON)
- **HTTPS:** Alle Requests über HTTPS
- **CORS:** Möglicherweise CORS-Beschränkungen (Server-Side Request nötig)

---

**Status:** ⏳ Wartet auf manuelle API-Analyse
