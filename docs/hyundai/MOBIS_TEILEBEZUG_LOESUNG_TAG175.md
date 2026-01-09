# Mobis Teilebezug - Lösung über Locosoft SOAP → Hyundai Workshop Automation

**Erstellt:** 2026-01-09 (TAG 175)  
**Erkenntnis:** Locosoft SOAP kann als Gateway zu Hyundai Workshop Automation fungieren!

---

## 🎯 PROBLEMSTELLUNG

**Hyundai Garantie-Richtlinie 2025-09:**
- ✅ **Pflicht:** Verwendete Hyundai Original-Teile dokumentieren
- ✅ **Pflicht:** Angabe des schadenverursachenden Teiles (Teilenummer)
- ✅ **Pflicht:** Nachweis des Teilebezugs aus Mobis (EDMOS)

**Aktuelle Situation:**
- Teile werden aus Locosoft (`parts`-Tabelle) geholt
- **Problem:** Kein Nachweis, dass es Hyundai Original-Teile sind
- **Problem:** Keine Bestätigung des Teilebezugs aus Mobis (EDMOS)

---

## 🔍 ERKENNTNISSE AUS HAR-ANALYSE

### 1. Hyundai Workshop Automation API
- **Base URL:** `https://hmd.wa.hyundai-europe.com:9092`
- **Format:** REST API (JSON)
- **Authentifizierung:** Bearer Token (JWT)

### 2. Repair Order API
- **Endpunkt:** `POST /api/services/app/repairorder/SearchRepairOrders`
- **Response enthält:** `dmsroNo` (Locosoft Auftragsnummer!)
- **Wichtig:** `requestItems` Array (hier sollten Teile sein, aber in HAR leer)

### 3. Parts Catalog Service
- **Base URL:** `https://asoneq.hyundai-corp.io/quotation/partscatalogservice`
- **Endpunkte:**
  - `POST /selectparts/selectvehicleinfobyvin` - Fahrzeuginfo
  - `POST /selectparts/selectlargegroupinfobyvin` - Teilegruppen

---

## 🚀 LÖSUNGSANSATZ

### Option 1: Über Locosoft SOAP (Empfohlen, wenn verfügbar)

**Frage:** Gibt es Locosoft SOAP-Methoden für Hyundai Workshop Automation?

**Zu prüfen:**
- Gibt es `getHyundaiRepairOrderDetails()`?
- Gibt es `getHyundaiPartsForOrder()`?
- Gibt es `getMobisPartsDelivery()`?

**Vorteile:**
- ✅ Bereits vorhandene SOAP-Infrastruktur
- ✅ Keine neue Authentifizierung nötig
- ✅ Einheitliche Schnittstelle

### Option 2: Direkt über Hyundai Workshop Automation REST API

**Implementierung:**
```python
from api.hyundai_workshop_automation_api import HyundaiWorkshopAutomationClient

client = HyundaiWorkshopAutomationClient()
client.login(username, password)

# Suche Repair Order
repair_orders = client.search_repair_orders(
    dmsro_no="4824.057"  # Locosoft Auftragsnummer
)

# Hole Details (wenn Endpunkt vorhanden)
ro_detail = client.get_repair_order_detail(repair_orders[0]['id'])

# Extrahiere Teile aus requestItems
parts = ro_detail.get('requestItems', [])
```

**Vorteile:**
- ✅ Direkter Zugriff
- ✅ Vollständige Daten

**Nachteile:**
- ⚠️ Neue Authentifizierung nötig
- ⚠️ Token-Management
- ⚠️ Separate API-Infrastruktur

---

## 📋 NÄCHSTE SCHRITTE

### 1. Locosoft SOAP prüfen
- [ ] WSDL analysieren auf Hyundai-relevante Methoden
- [ ] Testen ob Locosoft SOAP auf Hyundai Workshop Automation zugreifen kann
- [ ] Dokumentation von Locosoft anfragen (falls nötig)

### 2. Hyundai Workshop Automation API
- [ ] GetRepairOrderDetail-Endpunkt finden (oder testen)
- [ ] RequestItems-Struktur analysieren (wenn gefüllt)
- [ ] API-Client erstellen

### 3. Integration
- [ ] Entscheidung: Locosoft SOAP oder direkte REST API?
- [ ] Teilebezug-Funktion implementieren
- [ ] In Garantieakte-Workflow integrieren

---

## 🔗 RELEVANTE DATEIEN

- HAR-Datei: `/mnt/greiner-portal-sync/Hyundai_Garantie/hmd.wa.hyundai-europe.com.har`
- Dokumentation: `docs/hyundai/HYUNDAI_WORKSHOP_AUTOMATION_API_ANALYSE_TAG175.md`
- API-Client (TODO): `api/hyundai_workshop_automation_api.py`

---

**Status:** ⏳ Wartet auf Locosoft SOAP-Analyse und GetRepairOrderDetail-Endpunkt
