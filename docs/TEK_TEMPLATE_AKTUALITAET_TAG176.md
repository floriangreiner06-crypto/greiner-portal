# TEK Template Aktualität - Wann ist das Template aktuell? (TAG 176)

**Datum:** 2026-01-09  
**Frage:** Wann ist das TEK Template aktuell?

---

## 🔍 TEK TEMPLATE - AKTUALISIERUNGS-MECHANISMUS

### Template: `templates/controlling/tek_dashboard_v2.html`

**Aktualisierung:**
- ✅ **Bei jedem Seitenaufruf** oder Filter-Änderung
- ✅ JavaScript-Funktion `loadData()` ruft `/controlling/api/tek` auf
- ✅ **Kein Cache** - Daten werden immer live berechnet

**Mechanismus:**
```javascript
async function loadData() {
    const url = `/controlling/api/tek?firma=${firma}&standort=${standort}&monat=${monat}&jahr=${jahr}&modus=teil&umlage=mit`;
    const res = await fetch(url);
    const data = await res.json();
    renderAll(data);
}
```

---

## 📊 TEK API - DATENQUELLEN

Die TEK API (`/controlling/api/tek`) nutzt **zwei verschiedene Datenquellen**:

### 1. Monatsdaten (Gesamt-Monat)
**Datenquelle:** Gespiegelte Tabellen (`loco_journal_accountings`)
- **Tabelle:** `loco_journal_accountings` (mit Prefix `loco_`)
- **Aktualisierung:** Nach **Locosoft Mirror** um **19:00 Uhr**
- **Status:** 
  - ✅ **Ab 19:00 Uhr** aktuell (nach Mirror)
  - ❌ **Vor 19:00 Uhr** veraltet (letzter Mirror war gestern 19:00 Uhr)

**Code:**
```python
# routes/controlling_routes.py
cursor.execute("""
    SELECT ...
    FROM loco_journal_accountings  # Gespiegelte Tabelle!
    WHERE accounting_date >= ? AND accounting_date < ?
""", (von, bis))
```

### 2. Heute-Daten (Tagesdaten)
**Datenquelle:** Direkte Locosoft PostgreSQL-Verbindung
- **Verbindung:** `locosoft_session()` → Direkt zu `10.80.80.8:5432`
- **Aktualisierung:** **Live** aus Locosoft PostgreSQL
- **Status:**
  - ✅ **Ab 19:00 Uhr** aktuell (nach Locosoft PostgreSQL-Befüllung)
  - ❌ **Vor 19:00 Uhr** veraltet (Locosoft PostgreSQL noch nicht fertig)

**Code:**
```python
# routes/controlling_routes.py
with locosoft_session() as loco_conn:  # Direkte Verbindung!
    loco_cur = loco_conn.cursor()
    loco_cur.execute("""
        SELECT ...
        FROM journal_accountings  # Direkt aus Locosoft!
        WHERE accounting_date >= %s AND accounting_date < %s
    """, (vortag_str, heute_str))
```

---

## ⏰ ZEITPLAN - WANN IST DAS TEMPLATE AKTUELL?

| Zeit | Locosoft PostgreSQL | Locosoft Mirror | Template Status |
|------|---------------------|-----------------|-----------------|
| **18:00-19:00** | ❌ Wird befüllt (1 Stunde) | ❌ Noch nicht gestartet | ❌ **VERALTET** |
| **19:00** | ✅ **Fertig** | ✅ **Startet** | ⏳ Wird aktuell |
| **19:00-19:15** | ✅ Fertig | ⏳ Läuft (5-15 Min) | ⏳ Wird aktuell |
| **19:15+** | ✅ Fertig | ✅ **Fertig** | ✅ **AKTUELL** |

---

## ✅ ZUSAMMENFASSUNG

### Wann ist das TEK Template aktuell?

**Ab 19:00 Uhr** (nach Locosoft PostgreSQL-Befüllung)

**Details:**
1. **Locosoft PostgreSQL** ist um **19:00 Uhr** fertig (1 Stunde Befüllung)
2. **Locosoft Mirror** startet um **19:00 Uhr** (spiegelt Daten in DRIVE DB)
3. **Template** lädt Daten bei jedem Seitenaufruf:
   - **Monatsdaten:** Aus gespiegelten Tabellen (`loco_journal_accountings`) → Ab 19:00 Uhr aktuell
   - **Heute-Daten:** Direkt aus Locosoft PostgreSQL → Ab 19:00 Uhr aktuell

**Vor 19:00 Uhr:**
- ❌ Monatsdaten: Veraltet (letzter Mirror war gestern 19:00 Uhr)
- ❌ Heute-Daten: Veraltet (Locosoft PostgreSQL noch nicht fertig)

**Nach 19:00 Uhr:**
- ✅ Monatsdaten: Aktuell (nach Mirror)
- ✅ Heute-Daten: Aktuell (nach PostgreSQL-Befüllung)

---

## 🔄 AKTUALISIERUNGS-ZYKLUS

```
18:00-19:00: Locosoft befüllt PostgreSQL (1 Stunde)
    ↓
19:00: Locosoft PostgreSQL fertig
    ↓
19:00: Locosoft Mirror startet (spiegelt Daten)
    ↓
19:00-19:15: Mirror läuft (5-15 Minuten)
    ↓
19:15+: Template ist AKTUELL ✅
```

**Wichtig:** Das Template aktualisiert sich **bei jedem Seitenaufruf**, aber die Daten sind nur **ab 19:00 Uhr** aktuell!

---

**Status:** ✅ Dokumentiert - Template ist ab 19:00 Uhr aktuell
