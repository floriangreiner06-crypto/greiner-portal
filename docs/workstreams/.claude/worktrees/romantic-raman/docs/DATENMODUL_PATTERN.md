# DATENMODUL-PATTERN - DRIVE Single Source of Truth
**Version:** 1.0 (TAG 148)
**Erstellt:** 2025-12-30
**Status:** STANDARD für alle zukünftigen Datenmodule

---

## 🎯 ZIEL

Einheitliches Pattern für wiederverwendbare Datenmodule in DRIVE:
- **Eine** Datenquelle für jedes Feature
- **Konsistenz** zwischen Web-UI, Reports, Scripts
- **Testbarkeit** durch klare Trennung
- **Wartbarkeit** durch Modularisierung

---

## 📐 ARCHITEKTUR-PRINZIP

```
┌─────────────────────────────────────────────────┐
│     api/{bereich}_data.py                       │
│     = SINGLE SOURCE OF TRUTH                    │
│     - Geschäftslogik                            │
│     - SQL-Queries                               │
│     - Datenberechnungen                         │
└─────────────────────────────────────────────────┘
                     ▲         ▲         ▲
                     │         │         │
        ┌────────────┴─┐   ┌───┴────┐   ┴──────────┐
        │ Web-UI       │   │ Scripts│   │ Reports  │
        │ (Routes)     │   │        │   │          │
        └──────────────┘   └────────┘   └──────────┘
```

**Vorteile:**
✅ 100% Konsistenz (eine Datenquelle)
✅ Testbar (isolierte Funktionen)
✅ Wiederverwendbar (API + Scripts + Reports)
✅ Wartbar (Änderungen an EINER Stelle)

---

## 🏗️ STANDARD-PATTERN

### 1. Datei-Struktur

```
api/
  {bereich}_data.py          # Datenmodul (Single Source of Truth)
  {bereich}_api.py           # API-Routes (nutzt Datenmodul)
routes/
  {bereich}_routes.py        # HTML-Routes (nutzt API oder Datenmodul)
scripts/
  {bereich}_helper.py        # Scripts (nutzen Datenmodul)
```

**Beispiele:**
- `api/controlling_data.py` → `api/controlling_api.py` (nicht verwendet!)
- `api/werkstatt_data.py` → `api/werkstatt_live_api.py`
- `api/teile_data.py` → `api/teile_status_api.py`

---

### 2. Klassen-basiertes Pattern (EMPFOHLEN)

```python
"""
{Bereich} Datenmodul - Single Source of Truth
==================================================
Wiederverwendbare Geschäftslogik für {Bereich}-KPIs

Nutzer:
- Web-UI: api/{bereich}_api.py
- Scripts: scripts/{bereich}_helper.py
- Reports: scripts/send_daily_{bereich}.py

TAG{X}: Erstellt
"""

from datetime import date, timedelta
from api.db_utils import db_session, row_to_dict


class {Bereich}Data:
    """
    Datenmodell für {Bereich}

    Alle Methoden sind statisch (keine Instanzvariablen).
    Nutzt db_session() Context Manager für DB-Zugriff.
    """

    @staticmethod
    def get_{entity}(id, zeitraum=None, filter=None):
        """
        Holt {Entity}-Daten aus der Datenbank

        Args:
            id (int|str): {Entity}-ID
            zeitraum (tuple, optional): (von, bis) Datum-Tuple
            filter (dict, optional): Filter-Parameter (firma, standort, etc.)

        Returns:
            dict: {Entity}-Daten mit Keys:
                - id: {Entity}-ID
                - name: Name
                - kpi1: KPI-Wert 1
                - kpi2: KPI-Wert 2

        Example:
            >>> data = {Bereich}Data.get_{entity}(123, zeitraum=('2025-01-01', '2025-12-31'))
            >>> print(data['kpi1'])
            42.5
        """
        # Default-Zeitraum: Aktueller Monat
        if not zeitraum:
            heute = date.today()
            von = heute.replace(day=1).isoformat()
            bis = (heute.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
        else:
            von, bis = zeitraum

        # Filter bauen
        filter_sql = ""
        filter_params = [von, bis]

        if filter and filter.get('firma'):
            filter_sql += " AND firma_id = %s"
            filter_params.append(filter['firma'])

        # Daten abfragen
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    id,
                    name,
                    SUM(wert1) as kpi1,
                    AVG(wert2) as kpi2
                FROM {bereich}_tabelle
                WHERE datum >= %s AND datum < %s
                  AND id = %s
                  {filter_sql}
                GROUP BY id, name
            """, [von, bis, id] + filter_params)

            row = cursor.fetchone()
            if not row:
                return None

            return row_to_dict(row)

    @staticmethod
    def get_{entity}_trend(id, monate=12):
        """
        Holt Trend-Daten für Charts

        Args:
            id (int|str): {Entity}-ID
            monate (int): Anzahl Monate zurück

        Returns:
            list: Liste von dicts mit Keys:
                - monat: Monat (YYYY-MM)
                - wert: KPI-Wert

        Example:
            >>> trend = {Bereich}Data.get_{entity}_trend(123, monate=6)
            >>> for punkt in trend:
            ...     print(f"{punkt['monat']}: {punkt['wert']}")
        """
        heute = date.today()
        von = (heute.replace(day=1) - timedelta(days=monate*30)).isoformat()
        bis = heute.isoformat()

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    TO_CHAR(datum, 'YYYY-MM') as monat,
                    SUM(wert) as wert
                FROM {bereich}_tabelle
                WHERE datum >= %s AND datum < %s
                  AND id = %s
                GROUP BY TO_CHAR(datum, 'YYYY-MM')
                ORDER BY monat
            """, (von, bis, id))

            return [row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_{entity}_list(zeitraum=None, filter=None, limit=100, offset=0):
        """
        Holt Liste von {Entity}s

        Args:
            zeitraum (tuple, optional): (von, bis)
            filter (dict, optional): Filter-Parameter
            limit (int): Max. Anzahl Ergebnisse
            offset (int): Offset für Pagination

        Returns:
            dict: {
                'items': list of dicts,
                'total': int (Gesamt-Anzahl)
            }

        Example:
            >>> result = {Bereich}Data.get_{entity}_list(limit=10)
            >>> print(f"Zeige {len(result['items'])} von {result['total']}")
        """
        # Implementation...
        pass

    @staticmethod
    def calculate_kpi(umsatz, einsatz):
        """
        Berechnet KPI (z.B. DB1, Marge)

        Args:
            umsatz (float): Umsatz
            einsatz (float): Einsatz

        Returns:
            dict: {
                'db1': float,
                'marge': float (in %)
            }

        Example:
            >>> kpi = {Bereich}Data.calculate_kpi(1000, 600)
            >>> print(f"DB1: {kpi['db1']}, Marge: {kpi['marge']}%")
            DB1: 400.0, Marge: 40.0%
        """
        db1 = umsatz - einsatz
        marge = (db1 / umsatz * 100) if umsatz > 0 else 0

        return {
            'db1': round(db1, 2),
            'marge': round(marge, 1)
        }
```

---

### 3. Funktions-basiertes Pattern (ALTERNATIV)

Für einfachere Module ohne Klassen-Overhead:

```python
"""
{Bereich} Datenmodul - Single Source of Truth
"""

from api.db_utils import db_session, row_to_dict


def get_{bereich}_data(monat=None, jahr=None, filter=None):
    """
    Holt {Bereich}-Daten

    Args:
        monat (int, optional): Monat (1-12)
        jahr (int, optional): Jahr (YYYY)
        filter (dict, optional): Filter-Parameter

    Returns:
        dict: {Bereich}-Daten
    """
    # Implementation...
    pass


def calculate_{bereich}_kpi(data):
    """
    Berechnet KPIs
    """
    # Implementation...
    pass
```

**Wann welches Pattern?**
- **Klassen-basiert**: Komplexe Datenmodelle mit vielen Methoden (Werkstatt, Teile, Verkauf)
- **Funktions-basiert**: Einfache Datenmodelle (TEK, Budget)

---

## 🔧 KONSUMENTEN-PATTERN

### A) API-Route (Web-UI)

```python
# api/{bereich}_api.py
from flask import Blueprint, jsonify, request
from api.{bereich}_data import {Bereich}Data

{bereich}_bp = Blueprint('{bereich}', __name__)


@{bereich}_bp.route('/api/{bereich}/{entity}/<int:id>')
def api_get_{entity}(id):
    """
    API: Holt {Entity}-Daten

    Query-Params:
        - von: Start-Datum (YYYY-MM-DD)
        - bis: End-Datum (YYYY-MM-DD)
        - firma: Firma-Filter
    """
    # Parameter aus Request
    von = request.args.get('von')
    bis = request.args.get('bis')
    firma = request.args.get('firma')

    # Zeitraum bauen
    zeitraum = (von, bis) if von and bis else None
    filter_dict = {'firma': firma} if firma else None

    # Daten holen (aus Datenmodul!)
    data = {Bereich}Data.get_{entity}(id, zeitraum=zeitraum, filter=filter_dict)

    if not data:
        return jsonify({'error': '{Entity} nicht gefunden'}), 404

    return jsonify({
        'success': True,
        'data': data
    })
```

---

### B) HTML-Route (Templates)

```python
# routes/{bereich}_routes.py
from flask import Blueprint, render_template
from api.{bereich}_data import {Bereich}Data

{bereich}_routes = Blueprint('{bereich}_routes', __name__)


@{bereich}_routes.route('/{bereich}/dashboard')
@login_required
def dashboard():
    """Dashboard mit {Bereich}-Daten"""

    # Daten holen (aus Datenmodul!)
    data = {Bereich}Data.get_{entity}_list(limit=50)

    return render_template(
        '{bereich}_dashboard.html',
        items=data['items'],
        total=data['total']
    )
```

---

### C) Script (Reports, Scheduler)

```python
# scripts/send_daily_{bereich}.py
from api.{bereich}_data import {Bereich}Data
from datetime import date


def generate_report():
    """Generiert täglichen {Bereich}-Report"""

    heute = date.today()

    # Daten holen (aus Datenmodul!)
    data = {Bereich}Data.get_{entity}(
        id='alle',
        zeitraum=(heute.isoformat(), heute.isoformat())
    )

    # PDF generieren
    pdf = generate_pdf(data)

    # E-Mail versenden
    send_email(pdf)


if __name__ == '__main__':
    generate_report()
```

---

## 📊 BEISPIELE AUS DRIVE

### Beispiel 1: controlling_data.py (GOLD-Standard)

**Was gut ist:**
✅ Funktions-basiert (`get_tek_data()`)
✅ Alle Parameter dokumentiert
✅ Wiederverwendbar (Web-UI + Reports)
✅ Isolierte Geschäftslogik

**Was verbessert werden kann:**
⚠️ Könnte Klassen-basiert sein für bessere Struktur
⚠️ Kalkulatorische Lohnkosten waren fehlerhaft (TAG148 Fix)

```python
# api/controlling_data.py
def get_tek_data(monat=None, jahr=None, firma='0', standort='0', modus='teil', umlage='mit'):
    """Holt TEK-Daten aus Locosoft-Datenbank"""
    # ... 260 Zeilen saubere Implementierung
    return {
        'bereiche': bereiche,
        'gesamt': gesamt,
        'vm': vormonat,
        'vj': vorjahr
    }
```

---

### Beispiel 2: preisvergleich_service.py (GOLD-Standard)

**Was gut ist:**
✅ Klassen-basiert mit statischen Methoden
✅ Separiert von API (Service-Layer)
✅ Caching-Logik integriert
✅ Wiederverwendbar (renner_penner_api, teile_api)

```python
# api/preisvergleich_service.py
class PreisvergleichService:
    @staticmethod
    def hole_ebay_preise(teilenummer):
        """Holt Preise von eBay"""
        # ... Scraping-Logik
        return preise

    @staticmethod
    def hole_daparto_preise(teilenummer):
        """Holt Preise von Daparto"""
        # ... API-Call
        return preise
```

---

### Beispiel 3: werkstatt_live_api.py (ANTI-PATTERN!)

**Was schlecht ist:**
❌ 5.532 Zeilen in EINER Datei
❌ 23+ Funktionen gemischt
❌ SQL direkt in Routes
❌ KEINE Wiederverwendung möglich

**Sollte sein:**
```python
# api/werkstatt_data.py (NEU - TAG149)
class WerkstattData:
    @staticmethod
    def get_mechaniker_leistung(mech_nr, von, bis):
        """Leistungsgrad, Produktivität, Stunden"""
        # SQL HIER (aus werkstatt_live_api extrahiert)

    @staticmethod
    def get_auftrag_status(auftrag_nr):
        """Auftragsstatus, Teile, Zeiten"""
        # SQL HIER
```

---

## ✅ QUALITY-CHECKLIST

Bevor ein Datenmodul als "GOLD" gilt:

### Code-Qualität:
- [ ] Klassen- oder Funktions-basiert (konsistent!)
- [ ] Alle Methoden dokumentiert (Docstrings)
- [ ] Type-Hints für Parameter (optional, aber empfohlen)
- [ ] Keine Business-Logik in API-Routes
- [ ] SQL-Queries nur im Datenmodul

### Funktionalität:
- [ ] Mindestens 2 Konsumenten (z.B. API + Script)
- [ ] Filterbar (Zeitraum, Firma, Standort)
- [ ] Paginierung für Listen (limit, offset)
- [ ] Error-Handling (None bei nicht gefunden)

### Testing:
- [ ] Manuelle Tests durchgeführt
- [ ] Validierung gegen Referenz (z.B. Global Cube)
- [ ] Edge-Cases getestet (leere Daten, falsche IDs)

### Performance:
- [ ] Nutzt db_session() Context Manager
- [ ] Effiziente SQL-Queries (kein N+1)
- [ ] Indices vorhanden (bei häufigen Queries)

### Dokumentation:
- [ ] Modul-Docstring (Zweck, Nutzer)
- [ ] Beispiele in Docstrings
- [ ] TAG-Nummer dokumentiert

---

## 🚫 ANTI-PATTERNS (VERMEIDEN!)

### ❌ SQL in API-Routes
```python
# SCHLECHT: werkstatt_api.py
@app.route('/api/werkstatt/leistung')
def get_leistung():
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ... FROM werkstatt_leistung_daily
            WHERE ... GROUP BY ...
        """)  # 50+ Zeilen SQL!
        return jsonify(cursor.fetchall())
```

**Besser:**
```python
# GUT: werkstatt_api.py
from api.werkstatt_data import WerkstattData

@app.route('/api/werkstatt/leistung')
def get_leistung():
    data = WerkstattData.get_mechaniker_leistung(...)
    return jsonify(data)
```

---

### ❌ Duplicate Code
```python
# SCHLECHT: Gleiche SQL-Query in 3 Dateien
# api/controlling_api.py (Zeile 100)
cursor.execute("SELECT ... FROM loco_journal_accountings ...")

# routes/controlling_routes.py (Zeile 600)
cursor.execute("SELECT ... FROM loco_journal_accountings ...")

# scripts/send_daily_tek.py (Zeile 200)
cursor.execute("SELECT ... FROM loco_journal_accountings ...")
```

**Besser:**
```python
# GUT: Eine Query in controlling_data.py
# Alle nutzen: controlling_data.get_tek_data()
```

---

### ❌ Monolithische Dateien
```python
# SCHLECHT: werkstatt_live_api.py (5532 Zeilen!)
def get_leistung_live(): ...      # 300 LOC
def get_offene_auftraege(): ...   # 400 LOC
def get_kapazitaet(): ...         # 500 LOC
# + 20 weitere Funktionen
```

**Besser:**
```python
# GUT: Aufgeteilt in Datenmodule
# werkstatt_data.py: Datenlogik (800 LOC)
# werkstatt_live_api.py: Nur Routing (500 LOC)
```

---

## 📚 MIGRATION-STRATEGIE

Für bestehende monolithische APIs:

### Schritt 1: Analyse
1. API-Datei öffnen (z.B. `werkstatt_live_api.py`)
2. Funktionen identifizieren (z.B. 23 GET-Funktionen)
3. SQL-Queries markieren (wo wird DB abgefragt?)
4. Gruppieren nach Thema (Leistung, Aufträge, Kapazität)

### Schritt 2: Datenmodul erstellen
1. Neue Datei: `api/{bereich}_data.py`
2. Klasse erstellen: `class {Bereich}Data`
3. SQL-Queries migrieren (aus API extrahieren)
4. Methoden dokumentieren

### Schritt 3: API migrieren
1. API-Datei öffnen
2. Import hinzufügen: `from api.{bereich}_data import {Bereich}Data`
3. SQL-Queries entfernen
4. Datenmodul-Methoden aufrufen

### Schritt 4: Testing
1. Manuelle Tests (Web-UI laden)
2. Vergleich: Alte vs. Neue Werte
3. Validierung gegen Referenz

### Schritt 5: Deployment
1. Git Commit (lokal)
2. Server-Sync
3. Gunicorn Restart
4. Produktions-Tests

---

## 🎯 ROADMAP

### TAG 148 (AKTUELL):
- ✅ Pattern-Dokumentation (diese Datei)
- ⏳ TEK Fix (kalkulatorische Lohnkosten)

### TAG 149-150:
- [ ] werkstatt_data.py (800 LOC)
- [ ] teile_data.py (600 LOC)
- [ ] Migration: werkstatt_live_api.py

### TAG 151+:
- [ ] verkauf_data.py
- [ ] bankenspiegel_data.py
- [ ] controlling_bwa_data.py

**Ziel:** Alle 43 DRIVE Features auf GOLD-Status!

---

**Version:** 1.0
**Erstellt von:** Claude Sonnet 4.5 (TAG 148)
**Status:** GÜLTIG ab TAG 148
**Nächstes Update:** TAG 152 (nach ersten Erfahrungen)
