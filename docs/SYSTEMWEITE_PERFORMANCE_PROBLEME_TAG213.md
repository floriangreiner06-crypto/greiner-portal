# Systemweite Performance-Probleme - TAG 213

**Datum:** 2026-01-27 14:42  
**Status:** 🔴 **KRITISCH - Systemweite Langsamkeit**

---

## 🔍 IDENTIFIZIERTE PROBLEME

### 1. 🔴 KRITISCH: Worker-Blockierung durch langsame Queries

**Symptome:**
- 52 etablierte Verbindungen auf Port 5000
- Nur 9 Gunicorn-Worker (sync)
- Langsame Queries blockieren Worker
- Andere Requests müssen warten

**Aktuelle Konfiguration:**
- Workers: 9 (CPU * 2 + 1)
- Worker-Class: `sync` (blockierend)
- Timeout: 180 Sekunden (sehr hoch!)
- Keepalive: 2 Sekunden

**Problem:**
- Sync-Worker können nur 1 Request gleichzeitig bearbeiten
- Langsame Query (11s Stempeluhr) blockiert Worker
- Bei 52 Requests und 9 Workern = viele Requests warten

---

### 2. 🔴 KRITISCH: Viele parallele `get_auftrag_detail` Aufrufe

**Logs zeigen:**
```
INFO:api.werkstatt_data:WerkstattData.get_auftrag_detail: Auftrag 40008, 5 Positionen, 6 Teile
INFO:api.werkstatt_data:WerkstattData.get_auftrag_detail: Auftrag 220715, 9 Positionen, 5 Teile
INFO:api.werkstatt_data:WerkstattData.get_auftrag_detail: Auftrag 220765, 11 Positionen, 3 Teile
... (viele weitere)
```

**Problem:**
- Viele einzelne `get_auftrag_detail` Aufrufe
- Könnte auch N+1 Problem haben
- Jeder Aufruf blockiert Worker

---

### 3. 🟡 MITTEL: Kein Connection-Pooling für Locosoft-DB

**Aktuell:**
- Jede Query öffnet neue Connection zu Locosoft-DB
- Connection wird nach Query geschlossen
- Kein Pooling = Overhead bei jeder Query

**Impact:**
- Connection-Overhead: ~10-50ms pro Query
- Bei vielen Queries: Summiert sich

---

### 4. 🟡 MITTEL: Server-Ressourcen OK

**Status:**
- CPU-Load: 0.13 (niedrig) ✅
- Memory: 8.4Gi verfügbar ✅
- Disk: 61% verwendet ✅
- **Problem liegt nicht in Server-Ressourcen!**

---

## 🎯 SOFORT-MASSNAHMEN

### Priorität 1: Stempeluhr-Query optimieren (KRITISCH)

**Problem:** 11+ Sekunden blockiert Worker

**Lösung:**
1. Indizes hinzufügen (15 Minuten)
2. Query vereinfachen (1-2 Stunden)
3. Caching einführen (1 Stunde)

**Geschätzter Gewinn:** 30-40x schneller (von 11s auf 0.3s bei Cache)

---

### Priorität 2: Worker-Konfiguration anpassen

**Option A: Mehr Worker (schnell)**
```python
# config/gunicorn.conf.py
workers = multiprocessing.cpu_count() * 4 + 1  # Statt * 2
# Von 9 auf ~17 Worker
```

**Option B: Async-Worker (besser, aber komplexer)**
```python
# config/gunicorn.conf.py
worker_class = "gevent"  # Statt "sync"
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
```

**Option C: Timeout reduzieren**
```python
# config/gunicorn.conf.py
timeout = 30  # Statt 180 (3 Minuten)
```

**Empfehlung:** Option A (mehr Worker) + Option C (Timeout reduzieren)

---

### Priorität 3: `get_auftrag_detail` prüfen

**Prüfen ob N+1 Problem:**
- Werden mehrere Aufträge einzeln geladen?
- Können sie in einer Query geladen werden?

**Lösung:** Falls N+1 Problem → Batch-Loading implementieren

---

### Priorität 4: Connection-Pooling für Locosoft-DB

**Implementierung:**
```python
# api/db_utils.py
from psycopg2 import pool

# Connection Pool erstellen
locosoft_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host=locosoft_creds['host'],
    port=locosoft_creds['port'],
    database=locosoft_creds['database'],
    user=locosoft_creds['user'],
    password=locosoft_creds['password']
)

@contextmanager
def locosoft_session():
    conn = locosoft_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        locosoft_pool.putconn(conn)
```

**Geschätzter Gewinn:** 10-20% schneller (weniger Connection-Overhead)

---

## 📊 AKTUELLE SITUATION

**Server-Status:**
- ✅ CPU: Niedrig (0.13)
- ✅ Memory: OK (8.4Gi verfügbar)
- ✅ Disk: OK (61% verwendet)
- ❌ **Worker: Blockiert durch langsame Queries**

**Request-Status:**
- 52 etablierte Verbindungen
- 9 Worker (können nur 9 Requests gleichzeitig bearbeiten)
- **43 Requests warten!**

**Query-Status:**
- Stempeluhr: 11+ Sekunden 🔴
- get_auftrag_detail: Viele parallele Aufrufe 🟡
- Andere Queries: Normal 🟢

---

## 🔧 IMPLEMENTIERUNGS-PLAN

### Schritt 1: Worker erhöhen (5 Minuten)

**Datei:** `config/gunicorn.conf.py`

```python
# VORHER:
workers = multiprocessing.cpu_count() * 2 + 1  # 9 Worker

# NACHHER:
workers = multiprocessing.cpu_count() * 4 + 1  # ~17 Worker
timeout = 30  # Statt 180 (3 Minuten)
```

**Service neu starten:**
```bash
sudo systemctl restart greiner-portal
```

**Geschätzter Gewinn:** 2x mehr parallele Requests möglich

---

### Schritt 2: Stempeluhr-Indizes (15 Minuten)

**Migration:** `migrations/add_stempeluhr_performance_indexes_tag213.sql`

(Siehe `STEMPELUHR_PERFORMANCE_PROBLEM_TAG213.md`)

---

### Schritt 3: Stempeluhr-Caching (1 Stunde)

**Implementierung:** Redis-Cache mit 10 Sekunden TTL

(Siehe `STEMPELUHR_PERFORMANCE_PROBLEM_TAG213.md`)

---

## 📈 ERWARTETE VERBESSERUNG

**Aktuell:**
- 52 Requests, 9 Worker → 43 Requests warten
- Stempeluhr: 11 Sekunden
- **Gesamt: Sehr langsam** 🔴

**Nach Worker-Erhöhung:**
- 52 Requests, 17 Worker → 35 Requests warten
- **Gewinn: 2x mehr parallele Requests** 🟡

**Nach Stempeluhr-Optimierung:**
- Stempeluhr: 0.3 Sekunden (Cache-Hit)
- Worker werden schneller frei
- **Gewinn: 30-40x schneller** ✅

**Nach allen Optimierungen:**
- **Gesamt: 10-20x schneller** 🚀

---

## 🚨 SOFORT-EMPFEHLUNG

**1. Worker erhöhen (5 Minuten):**
```python
workers = multiprocessing.cpu_count() * 4 + 1
timeout = 30
```

**2. Service neu starten:**
```bash
sudo systemctl restart greiner-portal
```

**3. Stempeluhr-Indizes hinzufügen (15 Minuten)**

**4. Monitoring:**
- Logs beobachten
- Performance prüfen
- Weitere Optimierungen bei Bedarf

---

**Status:** 🔴 **KRITISCH - Sofort-Maßnahmen nötig**  
**Nächste Schritte:** Worker erhöhen + Stempeluhr optimieren
