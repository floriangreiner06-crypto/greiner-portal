# Performance-Analyse: Lange Ladezeiten in DRIVE

**TAG:** 192  
**Datum:** 2026-01-15  
**Problem:** Sehr lange Ladezeiten beim Seitenaufruf

---

## 🔍 IDENTIFIZIERTE PROBLEME

### 1. Navigation-Laden bei jedem Request ⚠️

**Problem:**
- `get_navigation_for_user()` wird bei **jedem Request** aufgerufen (context_processor)
- Lädt **alle 73 Navigation-Items** aus DB
- Filterung erfolgt **in Python** statt in SQL
- Für jedes Item wird `can_access_feature()` aufgerufen (73x)

**Aktueller Code:**
```python
# api/navigation_utils.py
def get_navigation_for_user():
    # Lädt ALLE Items
    cursor.execute('SELECT * FROM navigation_items WHERE active = true')
    all_items = rows_to_list(cursor.fetchall())  # 73 Items
    
    # Filterung in Python
    for item in all_items:
        if item.get('requires_feature'):
            if not current_user.can_access_feature(item['requires_feature']):
                continue  # 73x Feature-Checks!
```

**Performance-Impact:**
- DB-Query: ~0.17ms (OK)
- Python-Filterung: ~5-10ms (73 Items × Feature-Checks)
- **Gesamt: ~5-10ms pro Request**

### 2. Feature-Zugriff wird nicht gecacht ⚠️

**Problem:**
- `get_feature_access_from_db()` macht bei jedem Aufruf eine DB-Query
- Wird in `qa_api.py` aufgerufen (QA-Widget)
- Wird möglicherweise auch in Navigation verwendet

**Aktueller Code:**
```python
# config/roles_config.py
def get_feature_access_from_db():
    conn = get_db()
    cursor.execute('SELECT feature_name, role_name FROM feature_access')
    # ... keine Caching!
```

**Performance-Impact:**
- DB-Query: ~1-2ms pro Aufruf
- Wenn mehrmals aufgerufen: **5-10ms zusätzlich**

### 3. Komplexe Werkstatt-Queries 🔴

**Problem:**
- Werkstatt-Live-Seiten machen sehr komplexe Queries
- Viele JOINs, CTEs, Subqueries
- `get_nachkalkulation()` hat sehr komplexe Query mit mehreren CTEs

**Beispiel:**
```sql
-- api/werkstatt_data.py: get_nachkalkulation()
WITH heute_rechnungen AS (...),
     labour_summen AS (...),
     stempel_summen AS (...),
     auftrags_details AS (...)
SELECT ... FROM ... -- Sehr komplex!
```

**Performance-Impact:**
- Query-Zeit: **100-500ms** (je nach Datenmenge)
- Bei mehreren parallelen Requests: **kann zu Timeouts führen**

### 4. Keine Query-Caching ⚠️

**Problem:**
- Navigation wird bei jedem Request neu geladen
- Feature-Zugriff wird bei jedem Aufruf neu geladen
- Keine In-Memory-Caches

---

## 💡 OPTIMIERUNGS-VORSCHLÄGE

### Priorität 1: Navigation-Filterung in SQL verschieben ⭐⭐⭐

**Problem:** Alle 73 Items werden geladen, dann in Python gefiltert

**Lösung:** Filterung direkt in SQL

```python
def get_navigation_for_user():
    user_role = current_user.portal_role
    allowed_features = current_user.allowed_features  # Bereits beim Login geladen
    
    # SQL-Filterung
    query = '''
        SELECT * FROM navigation_items
        WHERE active = true
        AND (
            requires_feature IS NULL 
            OR requires_feature = ANY(%s)
        )
        AND (
            role_restriction IS NULL
            OR role_restriction = %s
            OR role_restriction = 'admin' AND %s = 'admin'
        )
        ORDER BY order_index, label
    '''
    cursor.execute(query, (allowed_features, user_role, user_role))
```

**Erwartete Verbesserung:** 5-10ms → 0.5-1ms

### Priorität 2: Feature-Zugriff cachen ⭐⭐⭐

**Problem:** `get_feature_access_from_db()` macht bei jedem Aufruf DB-Query

**Lösung:** In-Memory-Cache mit TTL

```python
from functools import lru_cache
from datetime import datetime, timedelta

_feature_access_cache = None
_cache_timestamp = None
CACHE_TTL = timedelta(minutes=5)

def get_feature_access_from_db():
    global _feature_access_cache, _cache_timestamp
    
    # Cache prüfen
    if _feature_access_cache and _cache_timestamp:
        if datetime.now() - _cache_timestamp < CACHE_TTL:
            return _feature_access_cache
    
    # Aus DB laden
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT feature_name, role_name FROM feature_access')
    # ... laden ...
    
    # Cache aktualisieren
    _feature_access_cache = merged
    _cache_timestamp = datetime.now()
    
    return merged
```

**Erwartete Verbesserung:** 1-2ms → 0.01ms (Cache-Hit)

### Priorität 3: Navigation-Caching ⭐⭐

**Problem:** Navigation wird bei jedem Request neu geladen

**Lösung:** Per-User-Cache (Session-basiert)

```python
from flask import has_request_context, g

def get_navigation_for_user():
    # Cache in Flask g (Request-Context)
    if has_request_context() and hasattr(g, 'navigation_items'):
        return g.navigation_items
    
    # ... Navigation laden ...
    
    # In g speichern
    if has_request_context():
        g.navigation_items = root_items
    
    return root_items
```

**Erwartete Verbesserung:** 5-10ms → 0.01ms (Cache-Hit)

### Priorität 4: Werkstatt-Queries optimieren ⭐

**Problem:** Sehr komplexe Queries mit vielen JOINs

**Lösung:**
1. Indizes prüfen/erstellen
2. Query-Analyse mit EXPLAIN ANALYZE
3. Möglicherweise Materialized Views für häufig genutzte Daten

**Erwartete Verbesserung:** 100-500ms → 50-200ms

---

## 🚀 SOFORT-MASSNAHMEN

### 1. Navigation-Filterung optimieren (5 Min)

**Datei:** `api/navigation_utils.py`

```python
def get_navigation_for_user():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter')
        allowed_features = getattr(current_user, 'allowed_features', [])
        
        # SQL-Filterung (statt Python-Filterung)
        # Prüfe ob User admin ist
        is_admin = 'admin' in allowed_features if allowed_features else False
        
        query = '''
            SELECT 
                id, parent_id, label, url, icon, order_index,
                requires_feature, role_restriction, is_dropdown,
                is_header, is_divider, active, category
            FROM navigation_items
            WHERE active = true
            AND (
                requires_feature IS NULL 
                OR requires_feature = ANY(%s)
            )
            AND (
                role_restriction IS NULL
                OR role_restriction = %s
                OR (role_restriction = 'admin' AND %s = true)
            )
            ORDER BY order_index, label
        '''
        
        cursor.execute(query, (allowed_features, user_role, is_admin))
        filtered_items = rows_to_list(cursor.fetchall())
        conn.close()
        
        # Struktur als Baum aufbauen (wie bisher)
        # ...
```

### 2. Feature-Zugriff cachen (5 Min)

**Datei:** `config/roles_config.py`

```python
from datetime import datetime, timedelta

_feature_access_cache = None
_cache_timestamp = None
CACHE_TTL = timedelta(minutes=5)

def get_feature_access_from_db():
    global _feature_access_cache, _cache_timestamp
    
    # Cache prüfen
    if _feature_access_cache and _cache_timestamp:
        if datetime.now() - _cache_timestamp < CACHE_TTL:
            return _feature_access_cache
    
    try:
        from api.db_connection import get_db
        import logging
        logger = logging.getLogger(__name__)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT feature_name, role_name 
            FROM feature_access 
            ORDER BY feature_name, role_name
        ''')
        
        db_access = {}
        for row in cursor.fetchall():
            feature = row['feature_name']
            role = row['role_name']
            if feature not in db_access:
                db_access[feature] = []
            db_access[feature].append(role)
        
        conn.close()
        
        # Mit FEATURE_ACCESS zusammenführen
        merged = FEATURE_ACCESS.copy()
        merged.update(db_access)
        
        # Cache aktualisieren
        _feature_access_cache = merged
        _cache_timestamp = datetime.now()
        
        return merged
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Fehler beim Laden aus DB, verwende Config: {e}")
        return FEATURE_ACCESS
```

---

## 📊 ERWARTETE VERBESSERUNGEN

| Optimierung | Aktuell | Nach Optimierung | Verbesserung |
|------------|---------|------------------|--------------|
| Navigation-Laden | 5-10ms | 0.5-1ms | **90%** |
| Feature-Zugriff | 1-2ms | 0.01ms | **99%** |
| Gesamt (Navigation) | 6-12ms | 0.5-1ms | **90%** |

**Gesamt-Verbesserung pro Request: ~10ms schneller**

---

## 🔍 WEITERE ANALYSE NÖTIG

1. **Welche Seiten sind besonders langsam?**
   - Werkstatt-Live?
   - Controlling-Dashboard?
   - Verkauf-Seiten?

2. **Sind es die ersten Requests oder alle?**
   - Cold-Start-Problem?
   - Oder kontinuierlich langsam?

3. **Server-Ressourcen:**
   - CPU-Auslastung?
   - Memory-Auslastung?
   - DB-Verbindungen?

---

## ✅ NÄCHSTE SCHRITTE

1. **Sofort:** Navigation-Filterung optimieren
2. **Sofort:** Feature-Zugriff cachen
3. **Dann:** Werkstatt-Queries analysieren
4. **Dann:** Weitere Performance-Messungen

---

**Status:** Analyse abgeschlossen, Optimierungen vorgeschlagen
