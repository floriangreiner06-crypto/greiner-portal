# Performance-Optimierung Strategie TAG 208

**Datum:** 2026-01-22  
**Problem:** Server langsam, lange Ladezeiten  
**Risiko:** DB-Verbindungs-Umstellung könnte Bugs verursachen

---

## 🔍 IDENTIFIZIERTE RISIKEN

### 1. Cursor-Sharing Problem ⚠️
**Problem:** Funktionen erhalten Cursor als Parameter
```python
# Aktuell:
cur_loco = conn_loco.cursor()
avg_problematisch = get_avg_problematische_auftraege_safe(cur_loco, subsidiary)
# Cursor wird an andere Funktion übergeben
```

**Risiko bei Context Manager:**
- Wenn Context Manager geschlossen wird, bevor Funktion fertig ist → "connection already closed"
- Cursor muss innerhalb des Context Managers bleiben

### 2. Nested Connections ⚠️
**Problem:** Zwei Connections gleichzeitig (Locosoft + Portal)
```python
conn_loco = get_locosoft_connection()
conn_portal = db_session().__enter__()
# Beide müssen gleichzeitig offen sein
```

**Risiko bei Context Manager:**
- Nested Context Manager müssen korrekt verschachtelt werden
- Reihenfolge des Schließens ist wichtig

### 3. TAG 200 Problem bekannt ⚠️
**Bekanntes Problem:** Manuelles `db_session().__enter__()` hat zu Fehlern geführt
- "connection already closed" Fehler
- Context Manager wurde nicht korrekt beendet

---

## 💡 EMPFOHLENE STRATEGIE

### Phase 1: Sichere Optimierungen (KEIN Risiko) ✅

**1. Einfache Endpoints umstellen**
- Endpoints mit nur EINER Connection
- KEIN Cursor-Sharing
- KEINE nested Connections

**Beispiele:**
- `/api/werkstatt/live/status` (Zeile 237)
- `/api/werkstatt/live/leistung` (Zeile 577)
- `/api/werkstatt/live/auftraege` (Zeile 2006)

**Vorgehen:**
```python
# Statt:
conn = get_locosoft_connection()
cur = conn.cursor()
# ... Queries ...
cur.close()
conn.close()

# Besser:
with locosoft_session() as conn:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # ... Queries ...
    # Automatisches Cleanup
```

### Phase 2: Komplexe Fälle (MIT Vorsicht) ⚠️

**2. `/forecast` Endpoint (Zeile 1105)**
- Zwei Connections gleichzeitig
- Cursor-Sharing mit Helper-Funktionen
- **Vorsicht:** Schrittweise umstellen, gründlich testen

**Lösung:**
```python
# Nested Context Manager
with locosoft_session() as conn_loco:
    cur_loco = conn_loco.cursor(cursor_factory=RealDictCursor)
    
    with db_session() as conn_portal:
        cur_portal = conn_portal.cursor()
        
        # Alle Queries hier
        # Helper-Funktionen erhalten cur_loco/cur_portal
        avg_problematisch = get_avg_problematische_auftraege_safe(cur_loco, subsidiary)
        
        # Return VOR dem Schließen
        return jsonify({...})
```

### Phase 3: Monitoring & Validierung ✅

**3. Nach jeder Änderung:**
- Service neustarten
- Endpoint testen
- Logs prüfen
- Performance messen

---

## 🚨 WICHTIGE REGELN

### ✅ DO's
1. **Eine Änderung pro Commit** - Leichteres Rollback
2. **Testen nach jeder Änderung** - Sofort Feedback
3. **Logs prüfen** - Fehler früh erkennen
4. **Context Manager für einfache Fälle** - Sicherer als manuelles Cleanup

### ❌ DON'Ts
1. **NICHT alles auf einmal umstellen** - Zu riskant
2. **NICHT Cursor außerhalb Context Manager verwenden** - Connection wird geschlossen
3. **NICHT Return-Statements im Context Manager vergessen** - Daten müssen vorher geladen sein

---

## 📋 KONKRETE UMSETZUNG

### Schritt 1: Einfache Endpoints (Sicher)
1. `/api/werkstatt/live/status` (Zeile 237)
2. `/api/werkstatt/live/leistung` (Zeile 577)
3. `/api/werkstatt/live/auftraege` (Zeile 2006)

### Schritt 2: Testen
- Service neustarten
- Jeden Endpoint testen
- Logs prüfen

### Schritt 3: Weitere Endpoints
- Nur wenn Schritt 1 erfolgreich
- Schrittweise vorgehen

### Schritt 4: Komplexe Fälle
- `/forecast` Endpoint (Zeile 1105)
- Sehr vorsichtig
- Gründlich testen

---

## 🎯 ERWARTETE VERBESSERUNGEN

### Performance
- **Connection Pooling:** Bessere Wiederverwendung
- **Automatisches Cleanup:** Keine Connection-Leaks
- **Konsistenz:** Einheitliches Pattern

### Stabilität
- **Weniger Fehler:** Automatisches Exception-Handling
- **Bessere Logs:** Klarere Fehlermeldungen
- **Einfacheres Debugging:** Einheitliches Pattern

---

## 📊 RISIKO-BEWERTUNG

| Änderung | Risiko | Impact | Priorität |
|----------|--------|--------|-----------|
| Einfache Endpoints | 🟢 **Niedrig** | 🟢 Hoch | ⭐⭐⭐ |
| Komplexe Endpoints | 🟡 **Mittel** | 🟢 Hoch | ⭐⭐ |
| `/forecast` Endpoint | 🟠 **Hoch** | 🟢 Hoch | ⭐ |

---

**Status:** ⏳ Warten auf Entscheidung  
**Nächster Schritt:** Phase 1 starten (einfache Endpoints)
