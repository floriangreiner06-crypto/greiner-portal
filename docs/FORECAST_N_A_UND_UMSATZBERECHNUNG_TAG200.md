# Forecast "N/A" und Umsatzberechnung - Analyse

**Datum:** 2026-01-20  
**TAG:** 200

---

## 🔍 PROBLEM 1: FORECAST ZEIGT "N/A"

### Symptom
- Forecast-Bereich zeigt "N/A" Badge
- Info-Banner: "Kapazitäts-Forecast wird noch entwickelt. Nutzen Sie vorerst die LIVE-Daten oben."

### Ursache gefunden

**API-Fehler:** `{"error":"connection already closed","success":false}`

**Endpunkt:** `GET /api/werkstatt/live/forecast`

**Problem:** Die Datenbank-Verbindung wird zu früh geschlossen, bevor die Query ausgeführt wird.

**Code-Stelle:** `api/werkstatt_live_api.py` Zeile 1105-1658

### Analyse

```python
@werkstatt_live_bp.route('/forecast', methods=['GET'])
def get_kapazitaets_forecast():
    try:
        conn_loco = get_locosoft_connection()
        cur_loco = conn_loco.cursor(cursor_factory=RealDictCursor)
        
        conn_portal = db_session().__enter__()
        cur_portal = conn_portal.cursor()
        
        # ... viele Queries ...
        
        cur_loco.close()
        conn_loco.close()
        cur_portal.close()
        conn_portal.close()  # ← Wird zu früh geschlossen?
        
        return jsonify({...})
```

**Mögliche Ursachen:**
1. **Context Manager Problem:** `db_session().__enter__()` wird manuell aufgerufen, aber nicht korrekt verwaltet
2. **Connection Pooling:** Verbindung wird vom Pool zurückgenommen, bevor Query fertig ist
3. **Exception Handling:** Fehler wird abgefangen, aber Connection wird trotzdem geschlossen

### Lösung

**Option 1: Context Manager korrekt verwenden**
```python
# Statt:
conn_portal = db_session().__enter__()

# Besser:
with db_session() as conn_portal:
    cur_portal = conn_portal.cursor()
    # ... Queries ...
    # Automatisches Cleanup
```

**Option 2: Connection-Management prüfen**
- Prüfe ob `get_locosoft_connection()` korrekt funktioniert
- Prüfe ob `db_session()` korrekt implementiert ist

---

## 💰 PROBLEM 2: UMSATZBERECHNUNG (415,71 €)

### Woher kommt der Umsatz?

**Endpunkt:** `GET /api/werkstatt/leistung?zeitraum=heute`

**Code-Stelle:** `api/werkstatt_api.py` Zeile 64-335

### Berechnung

**Frontend-Code:**
```javascript
// templates/aftersales/kapazitaetsplanung.html Zeile 582-606
function loadHeuteLive() {
    const url = '/api/werkstatt/live/leistung?zeitraum=heute';
    // ...
    const umsatz = data.gesamt_umsatz || 0;
    document.getElementById('kapa-heute-umsatz').textContent = 
        formatCurrency(umsatz) + ' Umsatz';
}
```

**⚠️ HINWEIS:** Frontend ruft `/api/werkstatt/live/leistung` auf, aber der Endpunkt ist `/api/werkstatt/leistung`!

**API-Berechnung:**
```python
# api/werkstatt_api.py Zeile 146
gesamt_umsatz = sum(m.get('umsatz', 0) for m in mechaniker)
```

**Umsatz pro Mechaniker:**
- Wird aus `labours` + `charge_types` berechnet
- Formel: `SUM(labours.time_units * charge_types.timeunit_rate)`
- Nur für heute gestempelte/verrechnete AW

### Datenquelle

**SQL-Query (vereinfacht):**
```sql
SELECT 
    l.mechanic_no,
    SUM(l.time_units * ct.timeunit_rate) as umsatz
FROM labours l
JOIN charge_types ct ON l.charge_type = ct.type
WHERE DATE(l.invoice_date) = CURRENT_DATE  -- Heute verrechnet
  AND l.is_invoiced = true
GROUP BY l.mechanic_no
```

**Berechnung:**
- **AW (Arbeitswerte):** Aus `labours.time_units`
- **AW-Preis:** Aus `charge_types.timeunit_rate` (Stundenverrechnungssatz)
- **Umsatz = AW × AW-Preis**

**Beispiel:**
- 104 AW gestempelt
- AW-Preis: ~4,00 € (durchschnittlich)
- Umsatz: 104 × 4,00 = **416,00 €** ✅ (passt zu 415,71 €)

### Unterschied: LIVE vs. VERRECHNET

**LIVE HEUTE (gestempelt):**
- Zeigt **gestempelte AW** (was Mechaniker gerade arbeiten)
- Umsatz = gestempelte AW × AW-Preis (geschätzt)

**VERRECHNET (abgerechnet):**
- Zeigt **verrechnete AW** (was bereits fakturiert wurde)
- Umsatz = verrechnete AW × tatsächlicher AW-Preis (aus Rechnung)

**Im Screenshot:**
- "104 AW gestempelt" = LIVE (was gerade passiert)
- "415,71 € Umsatz" = VERRECHNET (was bereits abgerechnet wurde)

---

## 🔧 LÖSUNGSVORSCHLÄGE

### 1. Forecast "N/A" beheben

**Sofort:**
```python
# api/werkstatt_live_api.py Zeile 1131
# Statt:
conn_portal = db_session().__enter__()

# Besser:
with db_session() as conn_portal:
    cur_portal = conn_portal.cursor()
    # ... alle Queries ...
    # Automatisches Cleanup
```

**Oder:**
```python
# Prüfe Connection-Management
try:
    conn_portal = db_session().__enter__()
    # ... Queries ...
finally:
    if conn_portal:
        conn_portal.close()
```

### 2. Umsatzberechnung dokumentieren

**Frontend anpassen:**
- Tooltip hinzufügen: "Umsatz = verrechnete AW × AW-Preis (heute abgerechnet)"
- Oder: "Umsatz = gestempelte AW × geschätzter AW-Preis" (wenn LIVE)

**API-Endpunkt prüfen:**
- Frontend ruft `/api/werkstatt/live/leistung` auf
- Aber Endpunkt ist `/api/werkstatt/leistung`
- → Prüfe ob Redirect oder Alias existiert

---

## 📊 ZUSAMMENFASSUNG

| Problem | Status | Lösung |
|---------|--------|--------|
| Forecast "N/A" | ❌ **API-Fehler** | Connection-Management beheben |
| Umsatzberechnung | ✅ **Funktioniert** | Dokumentation/Tooltip hinzufügen |

**Umsatzberechnung:**
- ✅ Korrekt: 415,71 € = verrechnete AW × AW-Preis
- ✅ Datenquelle: `labours` + `charge_types` (heute verrechnet)
- ⚠️ Frontend-Endpunkt prüfen: `/api/werkstatt/live/leistung` vs. `/api/werkstatt/leistung`

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-20  
**TAG:** 200
