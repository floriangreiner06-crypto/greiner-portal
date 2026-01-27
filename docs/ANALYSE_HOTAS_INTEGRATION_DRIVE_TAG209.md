# Analyse: H.O.T.A.S. Integration in DRIVE Features

**Datum:** 2026-01-23  
**TAG:** 209  
**Status:** 📊 **ANALYSE & INTEGRATIONSVORSCHLAG**

---

## 🎯 FRAGESTELLUNG

1. **Bei welchen DRIVE Features könnten wir H.O.T.A.S. integrieren?**
2. **Können wir H.O.T.A.S. über Locosoft als Backend abfragen?**

---

## 📋 WAS IST H.O.T.A.S.?

**H.O.T.A.S.** = **Händler-Organisations- und Termin-Abwicklungs-System**

**Funktion:** Ersatzteilpool für Werkstätten
- **Suche:** Nach Ersatzteilen im H.O.T.A.S.-Pool
- **Bestellung:** Direkte Bestellung über WebService
- **Angebote:** Über- und Altbestände anbieten

**Integration in Locosoft:**
- Zugriff über Pr. 211 (Werkstattauftrag)
- Zugriff über Pr. 572 (Bestellung)
- Zugriff über Pr. 512 (Teilepreis- und Bestandsinfo)
- Button: "Teilepool (F17)" oder "ET bestellen/ anfordern (F7)"

---

## 🔍 KÖNNEN WIR H.O.T.A.S. ÜBER LOCOSOFT ABFRAGEN?

### **Analyse der H.O.T.A.S. Dokumentation:**

**Erkenntnis:**
- ✅ **WebService vorhanden** - "Die Bestellung wird anschließend direkt über den WebService übertragen"
- ⚠️ **Aber:** WebService wird von **Locosoft** aufgerufen, nicht direkt von uns
- ⚠️ **Keine SOAP-Methode** - In Locosoft SOAP API gibt es keine H.O.T.A.S.-Methoden

### **Verfügbare Locosoft SOAP-Methoden (aktuell):**

**READ-Operationen:**
- ✅ `readPartInformation(partNumber)` - **Aber:** Nur Locosoft-Teile, nicht H.O.T.A.S.
- ✅ `readWorkOrderDetails(orderNumber)` - Auftragsdetails
- ❌ **Keine** `searchHotasParts()` oder ähnliche Methode

**LIST-Operationen:**
- ✅ `listSparePartTypes()` - Teilearten
- ❌ **Keine** `listHotasParts()` oder ähnliche Methode

**Fazit:** ⚠️ **H.O.T.A.S. ist NICHT direkt über Locosoft SOAP abfragbar!**

---

## 💡 MÖGLICHE INTEGRATIONS-OPTIONEN

### **Option 1: Direkte H.O.T.A.S. API (falls verfügbar)** ⭐⭐⭐

**Frage:** Gibt es eine H.O.T.A.S. REST API oder SOAP API?

**Vorteile:**
- ✅ Direkter Zugriff ohne Locosoft
- ✅ Vollständige Kontrolle
- ✅ Keine Abhängigkeit von Locosoft

**Nachteile:**
- ❌ Möglicherweise nicht verfügbar
- ❌ Separate Authentifizierung nötig
- ❌ Zusätzliche Integration

**Status:** ⏳ **Muss geprüft werden**

---

### **Option 2: Über Locosoft SOAP (muss erweitert werden)** ⭐⭐

**Frage:** Kann Locosoft SOAP um H.O.T.A.S.-Methoden erweitert werden?

**Vorteile:**
- ✅ Bereits vorhandene SOAP-Infrastruktur
- ✅ Einheitliche Schnittstelle
- ✅ Keine neue Authentifizierung

**Nachteile:**
- ❌ Möglicherweise nicht möglich
- ❌ Abhängigkeit von Locosoft-Entwicklung
- ❌ Wartezeit auf Implementierung

**Status:** ⏳ **Muss bei Locosoft angefragt werden**

---

### **Option 3: Über Locosoft PostgreSQL (Bestellungen)** ⭐⭐

**Frage:** Werden H.O.T.A.S.-Bestellungen in Locosoft gespeichert?

**Vorteile:**
- ✅ Direkter Zugriff auf Bestellungen
- ✅ Keine API nötig
- ✅ Schnelle Abfragen

**Nachteile:**
- ❌ Nur Bestellungen, keine Suche
- ❌ Keine Live-Abfrage möglich
- ❌ Abhängig von Locosoft-Datenstruktur

**Status:** ⏳ **Muss geprüft werden**

---

### **Option 4: Hybrid-Ansatz (Empfohlen)** ⭐⭐⭐

**Kombination:**
1. **Fehlende Teile identifizieren** - Über Locosoft PostgreSQL
2. **H.O.T.A.S. Suche** - Über direkte H.O.T.A.S. API (falls verfügbar)
3. **Bestellung** - Über Locosoft SOAP oder direkte H.O.T.A.S. API

**Vorteile:**
- ✅ Flexibel
- ✅ Funktioniert auch wenn eine Option nicht verfügbar ist
- ✅ Beste Nutzung der verfügbaren Schnittstellen

**Status:** ⚠️ **Abhängig von H.O.T.A.S. API-Verfügbarkeit**

---

## 🎯 DRIVE FEATURES FÜR H.O.T.A.S. INTEGRATION

### **1. Teile-Status API** ⭐⭐⭐

**Datei:** `api/teile_status_api.py`

**Aktuelle Funktion:**
- Zeigt fehlende Teile auf offenen Aufträgen
- Lieferzeiten-Prognose
- Kritische Aufträge

**H.O.T.A.S. Integration:**
- ✅ **Fehlende Teile** → H.O.T.A.S. Suche
- ✅ **H.O.T.A.S. Angebote** anzeigen
- ✅ **Direkte Bestellung** aus DRIVE

**Endpoint:** `/api/teile/status`
**Erweiterung:** `/api/teile/status?hotas=true` - Zeigt H.O.T.A.S. Angebote

**Nutzen:**
- Schnellere Teilebeschaffung
- Alternative Lieferanten
- Bessere Verfügbarkeit

---

### **2. Teile-Stock Utils** ⭐⭐⭐

**Datei:** `api/teile_stock_utils.py`

**Aktuelle Funktion:**
- `get_missing_parts_for_order()` - Fehlende Teile für Auftrag
- `get_stock_level_for_subsidiary()` - Lagerbestand prüfen

**H.O.T.A.S. Integration:**
- ✅ **Fehlende Teile** → H.O.T.A.S. Suche
- ✅ **H.O.T.A.S. Verfügbarkeit** prüfen
- ✅ **Bestellvorschlag** aus H.O.T.A.S.

**Neue Funktion:**
```python
def search_hotas_parts(part_number: str) -> List[Dict]:
    """
    Sucht Teil im H.O.T.A.S. Pool.
    
    Returns:
        Liste von Angeboten mit:
        - part_number
        - description
        - price
        - supplier
        - delivery_time
    """
```

**Nutzen:**
- Automatische H.O.T.A.S. Suche bei fehlenden Teilen
- Integration in bestehende Workflows

---

### **3. Teile-Preisvergleich** ⭐⭐⭐

**Datei:** `api/teile_api.py`

**Aktuelle Funktion:**
- `/api/teile/vergleich/<teilenummer>` - Preisvergleich Locosoft vs. Schäferbarthold vs. Dello

**H.O.T.A.S. Integration:**
- ✅ **H.O.T.A.S. Preise** hinzufügen
- ✅ **Vergleich:** Locosoft vs. Schäferbarthold vs. Dello vs. **H.O.T.A.S.**
- ✅ **Günstigstes Angebot** finden

**Erweiterung:**
```python
@teile_api.route('/vergleich/<teilenummer>', methods=['GET'])
def teile_vergleich(teilenummer):
    # ... bestehende Quellen ...
    
    # 4. H.O.T.A.S. (neu)
    hotas_offers = search_hotas_parts(teilenummer)
    if hotas_offers:
        result['quellen']['hotas'] = {
            'name': 'H.O.T.A.S.',
            'angebote': hotas_offers,
            'günstigstes': min(hotas_offers, key=lambda x: x['price'])
        }
```

**Nutzen:**
- Vollständiger Preisvergleich
- Günstigstes Angebot finden
- Bessere Entscheidungsgrundlage

---

### **4. Werkstatt Live API** ⭐⭐

**Datei:** `api/werkstatt_live_api.py`

**Aktuelle Funktion:**
- `/api/werkstatt/live/forecast` - Kapazitätsplanung mit Teile-Status

**H.O.T.A.S. Integration:**
- ✅ **Teile-Status erweitern** - H.O.T.A.S. Verfügbarkeit anzeigen
- ✅ **Alternative Lieferanten** - Wenn Teile fehlen, H.O.T.A.S. Option zeigen

**Nutzen:**
- Bessere Planung
- Alternative Beschaffungswege
- Weniger Stillstand

---

### **5. Teile-Bestellungen** ⭐⭐

**Datei:** `api/parts_api.py`, `templates/aftersales/teilebestellungen.html`

**Aktuelle Funktion:**
- ServiceBox Bestellungen (Stellantis)
- Bestellstatus-Tracking

**H.O.T.A.S. Integration:**
- ✅ **H.O.T.A.S. Bestellungen** hinzufügen
- ✅ **Bestellstatus** von H.O.T.A.S. anzeigen
- ✅ **Einheitliche Übersicht** aller Bestellungen

**Nutzen:**
- Zentrale Bestellübersicht
- Vollständige Transparenz
- Bessere Nachverfolgung

---

## 📊 INTEGRATIONS-PRIORITÄTEN

| Feature | Priorität | Aufwand | Nutzen |
|---------|-----------|---------|--------|
| **Teile-Status API** | ⭐⭐⭐ | Mittel | Sehr hoch |
| **Teile-Stock Utils** | ⭐⭐⭐ | Niedrig | Sehr hoch |
| **Teile-Preisvergleich** | ⭐⭐⭐ | Mittel | Hoch |
| **Werkstatt Live API** | ⭐⭐ | Mittel | Mittel |
| **Teile-Bestellungen** | ⭐⭐ | Hoch | Mittel |

---

## 🔍 TECHNISCHE UMSETZUNG

### **Schritt 1: H.O.T.A.S. API Client erstellen**

**Neue Datei:** `lib/hotas_client.py`

```python
class HotasClient:
    """
    H.O.T.A.S. API Client für DRIVE
    
    Features:
    - Suche nach Ersatzteilen
    - Bestellung von Teilen
    - Abfrage von Bestellstatus
    """
    
    def __init__(self, username: str, password: str):
        self.base_url = "https://hotas-api.example.com"  # TODO: Echte URL
        self.username = username
        self.password = password
    
    def search_parts(self, part_number: str) -> List[Dict]:
        """Sucht Teil im H.O.T.A.S. Pool."""
        pass
    
    def place_order(self, part_number: str, quantity: int, supplier: str) -> Dict:
        """Bestellt Teil über H.O.T.A.S."""
        pass
    
    def get_order_status(self, order_number: str) -> Dict:
        """Abfrage Bestellstatus."""
        pass
```

**Status:** ⏳ **Muss H.O.T.A.S. API-Dokumentation prüfen**

---

### **Schritt 2: Integration in Teile-Stock Utils**

**Erweiterung:** `api/teile_stock_utils.py`

```python
def get_missing_parts_with_hotas_alternatives(order_number: int, subsidiary: int) -> List[Dict]:
    """
    Ermittelt fehlende Teile + H.O.T.A.S. Alternativen.
    
    Returns:
        Liste mit:
        - part_number
        - is_available (Locosoft)
        - hotas_offers (Liste von H.O.T.A.S. Angeboten)
    """
    missing_parts = get_missing_parts_for_order(order_number, subsidiary)
    
    for part in missing_parts:
        # H.O.T.A.S. Suche
        hotas_offers = hotas_client.search_parts(part['part_number'])
        part['hotas_offers'] = hotas_offers
        part['has_hotas_alternative'] = len(hotas_offers) > 0
    
    return missing_parts
```

---

### **Schritt 3: Integration in Teile-Status API**

**Erweiterung:** `api/teile_status_api.py`

```python
@teile_status_bp.route('/status', methods=['GET'])
def get_teile_status():
    # ... bestehende Logik ...
    
    # H.O.T.A.S. Option hinzufügen
    include_hotas = request.args.get('hotas', 'false').lower() == 'true'
    
    if include_hotas:
        # Für jeden fehlenden Teil H.O.T.A.S. Suche
        for auftrag in auftraege:
            for teil in auftrag['fehlende_teile']:
                hotas_offers = hotas_client.search_parts(teil['part_number'])
                teil['hotas_offers'] = hotas_offers
```

---

### **Schritt 4: Integration in Teile-Preisvergleich**

**Erweiterung:** `api/teile_api.py`

```python
@teile_api.route('/vergleich/<teilenummer>', methods=['GET'])
def teile_vergleich(teilenummer):
    # ... bestehende Quellen ...
    
    # H.O.T.A.S. hinzufügen
    try:
        hotas_offers = hotas_client.search_parts(teilenummer)
        if hotas_offers:
            result['quellen']['hotas'] = {
                'name': 'H.O.T.A.S.',
                'angebote': hotas_offers,
                'günstigstes': min(hotas_offers, key=lambda x: x['price']),
                'anzahl_angebote': len(hotas_offers)
            }
    except Exception as e:
        result['quellen']['hotas'] = {'error': str(e)}
```

---

## 📋 NÄCHSTE SCHRITTE

### **1. H.O.T.A.S. API prüfen** ⏳

**Zu prüfen:**
- [ ] Gibt es eine H.O.T.A.S. REST API?
- [ ] Gibt es eine H.O.T.A.S. SOAP API?
- [ ] Welche Endpunkte sind verfügbar?
- [ ] Wie funktioniert die Authentifizierung?
- [ ] Gibt es API-Dokumentation?

**Kontakt:**
- H.O.T.A.S. Support kontaktieren
- API-Dokumentation anfordern
- Test-Zugang beantragen

---

### **2. Locosoft SOAP erweitern (optional)** ⏳

**Zu prüfen:**
- [ ] Kann Locosoft SOAP um H.O.T.A.S.-Methoden erweitert werden?
- [ ] Gibt es bereits H.O.T.A.S.-Methoden in SOAP?
- [ ] Was kostet die Erweiterung?

**Kontakt:**
- Locosoft Support kontaktieren
- H.O.T.A.S. SOAP-Integration anfragen
- Kosten erfragen

---

### **3. Locosoft PostgreSQL prüfen** ⏳

**Zu prüfen:**
- [ ] Werden H.O.T.A.S.-Bestellungen in Locosoft gespeichert?
- [ ] In welcher Tabelle?
- [ ] Welche Felder sind verfügbar?

**SQL-Query:**
```sql
-- Prüfen ob H.O.T.A.S. Bestellungen gespeichert werden
SELECT * FROM information_schema.tables 
WHERE table_name LIKE '%hotas%' OR table_name LIKE '%teilepool%';

-- Prüfen ob Bestellungen H.O.T.A.S. Quelle haben
SELECT * FROM parts_orders 
WHERE supplier_name LIKE '%HOTAS%' OR supplier_name LIKE '%H.O.T.A.S.%';
```

---

### **4. Implementierung planen** ⏳

**Für jede Integration:**
- [ ] API-Client erstellen
- [ ] Integration in bestehende Features
- [ ] Frontend erweitern
- [ ] Tests durchführen

---

## 💡 WICHTIGE ERKENNTNISSE

### **✅ Was möglich ist:**
1. **Integration in Teile-Status API** - Fehlende Teile + H.O.T.A.S. Alternativen
2. **Integration in Teile-Preisvergleich** - H.O.T.A.S. Preise hinzufügen
3. **Integration in Teile-Stock Utils** - Automatische H.O.T.A.S. Suche

### **⚠️ Was zu prüfen ist:**
1. **H.O.T.A.S. API** - Gibt es eine API?
2. **Locosoft SOAP** - Kann es erweitert werden?
3. **Locosoft PostgreSQL** - Werden Bestellungen gespeichert?

### **❌ Was nicht möglich ist:**
1. **Direkte SOAP-Abfrage** - Keine H.O.T.A.S.-Methoden in Locosoft SOAP
2. **Ohne API** - Integration erfordert API-Zugriff

---

## 🎯 EMPFEHLUNG

### **Phase 1: API prüfen** ⏳

1. **H.O.T.A.S. API-Dokumentation anfordern**
2. **Test-Zugang beantragen**
3. **API-Endpunkte testen**

### **Phase 2: Integration implementieren** ⏳

1. **H.O.T.A.S. Client erstellen** (`lib/hotas_client.py`)
2. **Teile-Status API erweitern** (höchste Priorität)
3. **Teile-Preisvergleich erweitern**
4. **Teile-Stock Utils erweitern**

### **Phase 3: Frontend erweitern** ⏳

1. **H.O.T.A.S. Angebote anzeigen**
2. **Direkte Bestellung aus DRIVE**
3. **Bestellstatus-Tracking**

---

## 📚 REFERENZEN

### **Dokumentation:**
- `/mnt/greiner-portal-sync/Loco_sst_dokus/Loco H.O.T.A.S. Schnittstelle.pdf` - Vollständige Dokumentation
- `docs/ANALYSE_HOTAS_SCHNITTSTELLE_TAG209.md` - H.O.T.A.S. Analyse

### **Code:**
- `api/teile_status_api.py` - Teile-Status API
- `api/teile_stock_utils.py` - Teile-Stock Utils
- `api/teile_api.py` - Teile-Preisvergleich
- `api/werkstatt_live_api.py` - Werkstatt Live API
- `api/parts_api.py` - Teile-Bestellungen

---

## 🎯 FAZIT

**H.O.T.A.S. kann in mehrere DRIVE Features integriert werden:**

1. ✅ **Teile-Status API** - Fehlende Teile + H.O.T.A.S. Alternativen
2. ✅ **Teile-Preisvergleich** - H.O.T.A.S. Preise hinzufügen
3. ✅ **Teile-Stock Utils** - Automatische H.O.T.A.S. Suche
4. ✅ **Werkstatt Live API** - Teile-Status erweitern
5. ✅ **Teile-Bestellungen** - H.O.T.A.S. Bestellungen hinzufügen

**Aber:** ⚠️ **H.O.T.A.S. ist NICHT direkt über Locosoft SOAP abfragbar!**

**Lösung:**
- ✅ **Direkte H.O.T.A.S. API** (falls verfügbar) - Empfohlen
- ⚠️ **Locosoft SOAP erweitern** (muss angefragt werden)
- ⚠️ **Locosoft PostgreSQL** (nur Bestellungen, keine Suche)

**Nächster Schritt:**
- H.O.T.A.S. API-Dokumentation anfordern
- Test-Zugang beantragen
- API-Endpunkte prüfen

---

**Status:** 📊 Analyse abgeschlossen  
**Nächster Schritt:** H.O.T.A.S. API-Dokumentation anfordern
