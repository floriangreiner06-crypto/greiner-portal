# Mobis Teilebezug über Locosoft SOAP

**Erstellt:** 2026-01-09 (TAG 175)  
**Erkenntnis:** Hyundai verwendet Locosoft SOAP auch für Workshop Automation!

---

## 🎯 ERKENNTNIS

**Wichtig:** Hyundai verwendet für den **Hyundai Workshop Automation** auch den **Locosoft SOAP-Dienst**!

Das bedeutet:
- ✅ **Locosoft SOAP** ist bereits verfügbar und funktioniert
- ✅ **Teile-Daten** sind bereits in Locosoft verfügbar
- ✅ **Keine Mobis EDMOS API nötig** - wir können über Locosoft SOAP auf Teile-Daten zugreifen!

---

## ✅ VORAUSSETZUNGEN

### 1. Locosoft SOAP-Client vorhanden
- ✅ `tools/locosoft_soap_client.py` existiert
- ✅ `readWorkOrderDetails()` Methode vorhanden
- ✅ `readPartInformation()` Methode vorhanden
- ✅ Verbindung getestet (10.80.80.7:8086)

### 2. Konfiguration
- ✅ SOAP-Host: 10.80.80.7
- ✅ SOAP-Port: 8086
- ✅ User: 9001
- ✅ Password: Max2024
- ✅ Interface-Version: 2.2

---

## 🔍 VERFÜGBARE SOAP-METHODEN

### 1. `readWorkOrderDetails(orderNumber)`
**Liest komplette Auftragsdetails inkl. Teile.**

```python
from tools.locosoft_soap_client import get_soap_client

client = get_soap_client()
work_order = client.read_work_order_details(220542)

# Enthält vermutlich:
# - order_number
# - labours (Arbeitspositionen)
# - parts (Teile) ← WICHTIG!
# - vehicle
# - customer
# - etc.
```

**Zu prüfen:**
- Enthält `work_order['parts']` die Teile?
- Welche Felder haben die Teile?
- Ist `parts_type` enthalten (Hyundai Original = 5)?

### 2. `readPartInformation(partNumber)`
**Liest Teile-Informationen inkl. Lagerbestand.**

```python
part_info = client.read_part_information("98850J7500")

# Enthält vermutlich:
# - part_number
# - description
# - parts_type (5 = Hyundai Original)
# - stock_level
# - price
# - etc.
```

**Zu prüfen:**
- Ist `parts_type` enthalten?
- Wie erkennen wir Hyundai Original-Teile?

---

## 📋 LOCOSOFT DATENBANK-STRUKTUR

### Teile-Typen (aus `loco_part_types`)
```sql
SELECT * FROM loco_part_types;
```

**Erwartete Werte:**
- `5` = Hyundai
- `6` = Hyundai Zubehör
- `65` = Hyundai (AT)

### Teile in Auftrag (aus `parts` Tabelle)
```sql
SELECT 
    p.part_number,
    p.amount,
    p.sum,
    p.parts_type,
    pm.description
FROM parts p
LEFT JOIN parts_master pm ON p.part_number = pm.part_number
WHERE p.order_number = 220542
  AND p.parts_type IN (5, 6, 65)  -- Hyundai Original
```

---

## 🚀 IMPLEMENTIERUNGS-ANSATZ

### Option 1: Über Locosoft SOAP (Empfohlen)
```python
from tools.locosoft_soap_client import get_soap_client

def get_hyundai_original_parts_for_order(order_number: int) -> List[Dict]:
    """
    Ruft Hyundai Original-Teile für einen Auftrag ab.
    
    Args:
        order_number: Auftragsnummer
    
    Returns:
        Liste von Teilen mit:
        - part_number: Teilenummer
        - description: Beschreibung
        - amount: Menge
        - parts_type: 5 = Hyundai Original
        - is_hyundai_original: True
    """
    client = get_soap_client()
    if not client:
        return []
    
    # Lese Auftragsdetails
    work_order = client.read_work_order_details(order_number)
    if not work_order:
        return []
    
    # Filtere Hyundai Original-Teile
    hyundai_parts = []
    parts = work_order.get('parts', [])
    
    for part in parts:
        parts_type = part.get('parts_type') or part.get('partsType')
        
        # Hyundai Original: parts_type = 5, 6, 65
        if parts_type in [5, 6, 65]:
            hyundai_parts.append({
                'part_number': part.get('part_number') or part.get('partNumber'),
                'description': part.get('description') or part.get('text_line'),
                'amount': part.get('amount', 0),
                'sum': part.get('sum', 0),
                'parts_type': parts_type,
                'is_hyundai_original': True
            })
    
    return hyundai_parts
```

### Option 2: Über Locosoft Datenbank (Fallback)
```python
from api.db_utils import get_locosoft_connection

def get_hyundai_original_parts_from_db(order_number: int) -> List[Dict]:
    """Ruft Hyundai Original-Teile aus Locosoft DB ab."""
    conn = get_locosoft_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.part_number,
            pm.description,
            p.amount,
            p.sum,
            p.parts_type
        FROM parts p
        LEFT JOIN parts_master pm ON p.part_number = pm.part_number
        WHERE p.order_number = %s
          AND p.parts_type IN (5, 6, 65)  -- Hyundai Original
        ORDER BY p.order_position
    """, [order_number])
    
    parts = cursor.fetchall()
    conn.close()
    
    return [
        {
            'part_number': p['part_number'],
            'description': p['description'],
            'amount': p['amount'],
            'sum': p['sum'],
            'parts_type': p['parts_type'],
            'is_hyundai_original': True
        }
        for p in parts
    ]
```

---

## 🔧 INTEGRATION IN GARANTIEAKTE-WORKFLOW

### Aktuelle Integration
**Datei:** `api/garantieakte_workflow.py`

**Erweiterung:**
```python
from tools.locosoft_soap_client import get_soap_client

def create_garantieakte_with_parts(order_number: int):
    """Erstellt Garantieakte inkl. Teilebezug-Nachweis."""
    
    # 1. Hole Teile über SOAP
    client = get_soap_client()
    work_order = client.read_work_order_details(order_number)
    
    # 2. Filtere Hyundai Original-Teile
    hyundai_parts = [
        p for p in work_order.get('parts', [])
        if p.get('parts_type') in [5, 6, 65]
    ]
    
    # 3. Erstelle Garantieakte mit Teilebezug
    garantieakte = create_garantieakte_ordner(...)
    
    # 4. Füge Teilebezug-Liste hinzu
    save_teilebezug_liste(garantieakte, hyundai_parts)
    
    return garantieakte
```

---

## 📝 NÄCHSTE SCHRITTE

### 1. SOAP-Struktur prüfen
- [ ] Test: `readWorkOrderDetails(220542)` aufrufen
- [ ] Prüfen ob `parts` enthalten ist
- [ ] Struktur der Parts analysieren
- [ ] Prüfen ob `parts_type` enthalten ist

### 2. Implementierung
- [ ] Funktion `get_hyundai_original_parts_for_order()` erstellen
- [ ] In `garantieakte_workflow.py` integrieren
- [ ] Teilebezug-Liste in PDF einfügen

### 3. Test
- [ ] Mit echten Garantieauftrag testen
- [ ] Prüfen ob alle Hyundai Original-Teile erkannt werden
- [ ] PDF-Generierung testen

---

## ✅ VORTEILE

1. **Keine neue API nötig** - Locosoft SOAP ist bereits vorhanden
2. **Bereits getestet** - SOAP-Verbindung funktioniert
3. **Einfache Integration** - Kann direkt verwendet werden
4. **Hyundai Original-Nachweis** - Über `parts_type` (5, 6, 65)

---

## ⚠️ ZU PRÜFEN

1. **Enthält `readWorkOrderDetails` Teile?**
   - Muss getestet werden
   - Falls nicht: Fallback auf DB-Abfrage

2. **Ist `parts_type` in SOAP-Response?**
   - Muss getestet werden
   - Falls nicht: Über `readPartInformation()` prüfen

3. **Mobis Bestellnummer?**
   - Locosoft enthält möglicherweise keine Mobis Bestellnummer
   - Falls nötig: Weiterhin Mobis EDMOS API analysieren

---

**Status:** ✅ Locosoft SOAP ist verfügbar - kann direkt verwendet werden!
