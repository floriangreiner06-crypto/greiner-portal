# TODO FÜR CLAUDE - SESSION START TAG 149
**Erstellt:** 2025-12-30
**Basis:** Session TAG 148 (Werkstatt-Modularisierung START)
**Strategie:** OPTION A - Werkstatt-zentrierter Ansatz (fortsetzen)

---

## 📋 WICHTIG: VOR BEGINN LESEN!

**Session TAG 148 Ergebnis:**
- ✅ DATENMODUL_PATTERN.md erstellt (550 Zeilen)
- ✅ werkstatt_data.py erstellt (509 Zeilen)
- ✅ Proof-of-Concept: get_leistung_live() migriert
- ✅ werkstatt_live_api.py: 5.532 → 5.367 Zeilen (-165 LOC mit EINER Funktion!)
- ⏳ **NICHT DEPLOYED** - Server-Sync + Test erforderlich!

**Status:** Proof-of-Concept validiert → Jetzt vollständige Migration!

---

## 🎯 ROADMAP (TAG 149-150)

### TAG 149: Werkstatt-Modularisierung Teil 1 (4-5h) ← **DU BIST HIER**
✅ Deployment + Test von TAG148 Code
✅ 5 weitere Funktionen migrieren:
  1. get_offene_auftraege()
  2. get_live_dashboard()
  3. get_stempeluhr_live()
  4. get_kapazitaetsplanung()
  5. get_kapazitaets_forecast()

### TAG 150: Werkstatt-Modularisierung Teil 2 (4-5h)
- Restliche Funktionen migrieren (~17 Funktionen)
- teile_data.py erstellen (600 LOC)
- **Impact:** 9.400 → 3.500 LOC (63% Reduktion)

---

## 📋 AUFGABEN TAG 149

### 1. Deployment + Test (ZUERST!)
**Status:** ⏳ Ausstehend
**Warum:** TAG148 Code muss erst auf Server deployed werden

#### Dateien auf Server syncen:
```bash
# Via SCP (von Windows)
scp "f:\Greiner Portal\Greiner_Portal_NEU\Server\api\werkstatt_data.py" ag-admin@10.80.80.20:/opt/greiner-portal/api/
scp "f:\Greiner Portal\Greiner_Portal_NEU\Server\api\werkstatt_live_api.py" ag-admin@10.80.80.20:/opt/greiner-portal/api/

# Gunicorn Restart
ssh ag-admin@10.80.80.20 "sudo systemctl restart greiner-portal"

# Logs checken (WICHTIG!)
ssh ag-admin@10.80.80.20 "journalctl -u greiner-portal -n 50"
```

#### API-Test durchführen:
```bash
# Test: Leistung Endpoint
curl -s "http://10.80.80.20:5000/api/werkstatt/live/leistung?zeitraum=monat&betrieb=alle" | python3 -m json.tool | head -50

# Sollte enthalten:
# "source": "LIVE_V2"  ← Nutzt werkstatt_data.py!
# "success": true
# "mechaniker": [...]
```

**Erwartetes Ergebnis:**
- ✅ API funktioniert identisch wie vorher
- ✅ `source: 'LIVE_V2'` zeigt werkstatt_data.py wird genutzt
- ✅ Keine Fehler in Logs

**Falls Fehler:**
- Logs analysieren: `journalctl -u greiner-portal -f`
- Import-Fehler? → `import api.werkstatt_data` prüfen
- SQL-Fehler? → Locosoft DB erreichbar prüfen

---

### 2. get_offene_auftraege() migrieren
**Status:** ⏳ Ausstehend
**Datei:** `api/werkstatt_live_api.py` Zeile 366-478 (~113 LOC)

**Aktueller Code:**
```python
@werkstatt_live_bp.route('/auftraege', methods=['GET'])
def get_offene_auftraege():
    """Holt offene Aufträge aus Locosoft"""
    subsidiary = request.args.get('subsidiary')
    tage = int(request.args.get('tage', 7))

    # 100 Zeilen SQL...
    query = """
        SELECT DISTINCT
            o.order_number,
            o.customer_number,
            cs.name1 as customer_name,
            ...
        FROM orders o
        LEFT JOIN customers_suppliers cs ON ...
        WHERE ...
    """
```

**Migration nach werkstatt_data.py:**
```python
# api/werkstatt_data.py
@staticmethod
def get_offene_auftraege(
    betrieb: Optional[int] = None,
    tage_zurueck: int = 7
) -> List[Dict[str, Any]]:
    """
    Holt alle offenen Werkstatt-Aufträge aus Locosoft.

    Args:
        betrieb: Betrieb-ID (1=DEG, 2=HYU, 3=LAN)
        tage_zurueck: Wie viele Tage zurück (default: 7)

    Returns:
        Liste von Dicts mit Auftrags-Details
    """
    with locosoft_session() as conn:
        cursor = conn.cursor()

        betrieb_filter = ""
        params = [tage_zurueck]
        if betrieb is not None:
            betrieb_filter = "AND o.subsidiary = %s"
            params.append(betrieb)

        query = f"""
            SELECT DISTINCT
                o.order_number,
                o.customer_number,
                cs.name1 as customer_name,
                o.order_date,
                o.order_text,
                o.vehicle_reference,
                ...
            FROM orders o
            LEFT JOIN customers_suppliers cs ON o.customer_number = cs.customer_number
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '%s days'
              {betrieb_filter}
            ORDER BY o.order_date DESC
        """

        cursor.execute(query, params)
        return rows_to_list(cursor.fetchall())
```

**API refactoren:**
```python
# api/werkstatt_live_api.py
@werkstatt_live_bp.route('/auftraege', methods=['GET'])
def get_offene_auftraege():
    """TAG149: Nutzt werkstatt_data.py"""
    from api.werkstatt_data import WerkstattData

    betrieb = request.args.get('subsidiary')
    betrieb_int = int(betrieb) if betrieb else None
    tage = int(request.args.get('tage', 7))

    auftraege = WerkstattData.get_offene_auftraege(
        betrieb=betrieb_int,
        tage_zurueck=tage
    )

    return jsonify({
        'success': True,
        'source': 'LIVE_V2',
        'auftraege': auftraege,
        'anzahl': len(auftraege)
    })
```

**Code-Reduktion:** 113 → ~25 Zeilen (78% kleiner!)

---

### 3. get_live_dashboard() migrieren
**Status:** ⏳ Ausstehend
**Datei:** `api/werkstatt_live_api.py` Zeile 480-625 (~140 LOC)

**Besonderheit:** Dashboard kombiniert mehrere Datenquellen:
- Mechaniker-Leistung (heute)
- Offene Aufträge
- Anwesenheit

**Migration-Strategie:**
```python
@werkstatt_live_bp.route('/dashboard', methods=['GET'])
def get_live_dashboard():
    """TAG149: Kombiniert mehrere werkstatt_data.py Funktionen"""
    from api.werkstatt_data import WerkstattData
    from datetime import date

    heute = date.today()
    betrieb = int(request.args.get('betrieb')) if request.args.get('betrieb') else None

    # Leistung heute
    leistung = WerkstattData.get_mechaniker_leistung(
        von=heute,
        bis=heute,
        betrieb=betrieb
    )

    # Offene Aufträge
    auftraege = WerkstattData.get_offene_auftraege(
        betrieb=betrieb,
        tage_zurueck=7
    )

    # Stempeluhr
    stempeluhr = WerkstattData.get_stempeluhr(
        datum=heute,
        betrieb=betrieb
    )

    return jsonify({
        'success': True,
        'source': 'LIVE_V2',
        'leistung': leistung['gesamt'],
        'auftraege': auftraege[:10],  # Nur Top 10
        'anwesenheit': stempeluhr
    })
```

**Code-Reduktion:** 140 → ~40 Zeilen (71% kleiner!)

---

### 4. get_stempeluhr_live() migrieren
**Status:** ⏳ Ausstehend
**Datei:** `api/werkstatt_live_api.py` Zeile 627-1197 (~570 LOC!)

**Migration:** Siehe werkstatt_data.py Stub `get_stempeluhr()`

**Code-Reduktion:** 570 → ~30 Zeilen (95% kleiner!!!)

---

### 5. get_kapazitaetsplanung() migrieren
**Status:** ⏳ Ausstehend
**Datei:** `api/werkstatt_live_api.py` Zeile 2256-2568 (~312 LOC)

**Migration:** Siehe werkstatt_data.py Stub `get_kapazitaetsplanung()`

**Code-Reduktion:** 312 → ~30 Zeilen (90% kleiner!)

---

### 6. get_kapazitaets_forecast() migrieren
**Status:** ⏳ Ausstehend
**Datei:** `api/werkstatt_live_api.py` Zeile 2670-3228 (~558 LOC)

**Besonderheit:** ML-basierter Forecast (nutzt scikit-learn?)

**Migration:** Komplexe Logik → eigene Methode in werkstatt_data.py

**Code-Reduktion:** 558 → ~40 Zeilen (93% kleiner!)

---

## 📊 ERWARTETE RESULTS TAG 149

### Code-Statistik nach TAG 149:
| Funktion | Vorher | Nachher | Δ |
|----------|--------|---------|---|
| get_leistung_live() | 270 | 97 | -173 ✅ TAG148 |
| get_offene_auftraege() | 113 | 25 | -88 |
| get_live_dashboard() | 140 | 40 | -100 |
| get_stempeluhr_live() | 570 | 30 | -540 |
| get_kapazitaetsplanung() | 312 | 30 | -282 |
| get_kapazitaets_forecast() | 558 | 40 | -518 |
| **GESAMT** | **1.963** | **262** | **-1.701** |

**werkstatt_live_api.py:**
- Vorher (TAG148): 5.367 Zeilen
- Nachher (TAG149): ~3.666 Zeilen (-1.701)
- **Reduktion:** 31% kleiner!

**werkstatt_data.py:**
- Vorher (TAG148): 509 Zeilen
- Nachher (TAG149): ~1.600 Zeilen (+1.091)

---

## 📂 DATEIEN-ÜBERSICHT

### Zu ändern (TAG 149):
1. `api/werkstatt_data.py` (509 → ~1.600 LOC)
   - get_offene_auftraege() implementieren
   - get_stempeluhr() implementieren
   - get_kapazitaetsplanung() implementieren
   - get_kapazitaets_forecast() implementieren

2. `api/werkstatt_live_api.py` (5.367 → ~3.666 LOC)
   - 5 Funktionen refactoren

### Zu erstellen (TAG 149):
3. `docs/sessions/SESSION_WRAP_UP_TAG149.md`
4. `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG150.md`

---

## 🧪 VALIDIERUNGS-CHECKLIST

### Nach jeder Migration:
- [ ] Code kompiliert ohne Fehler (`python -m py_compile api/werkstatt_data.py`)
- [ ] API-Endpoint antwortet (`curl http://10.80.80.20:5000/api/werkstatt/live/...`)
- [ ] Response-Format identisch (JSON-Struktur)
- [ ] `source: 'LIVE_V2'` vorhanden
- [ ] Keine Fehler in Logs

### Gesamt-Validierung (Ende TAG149):
- [ ] Alle 6 Endpoints funktionieren
- [ ] Web-UI Werkstatt-Seiten laden korrekt
- [ ] Gunicorn Restart ohne Fehler
- [ ] Git Commit lokal + Server

---

## ⚠️ WICHTIGE HINWEISE

### SQL-Pattern (PostgreSQL):
```python
# Array-Parameter: != ALL() statt NOT IN
WHERE employee_number != ALL(%s)
params.append([5025, 5026, 5028])

# Intervall-Rechnung
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'

# FULL OUTER JOIN für Mechaniker ohne Stempelungen
FROM stempel s
FULL OUTER JOIN anwesenheit a ON s.employee_number = a.employee_number
```

### Locosoft-Tabellen:
- `times`: VIEW mit Stempelungen (type=1/2)
- `orders`: Aufträge (order_number, customer_number, order_date)
- `customers_suppliers`: Kunden-Stammdaten
- `employees_history`: Mitarbeiter (is_latest_record = true!)
- `labours`: Arbeitsleistungen (time_units = AW)
- `invoices`: Rechnungen (invoice_date, is_canceled)

### Context Manager verwenden:
```python
with locosoft_session() as conn:
    cursor = conn.cursor()
    cursor.execute(...)
    # Connection wird automatisch geschlossen!
```

### Error Handling:
```python
try:
    data = WerkstattData.get_xxx()
    return jsonify({'success': True, 'data': data})
except Exception as e:
    logger.exception("Fehler bei xxx")
    return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 📚 REFERENZEN

**PFLICHTLEKTÜRE:**
- `docs/DATENMODUL_PATTERN.md` ⭐ Standard-Pattern
- `docs/sessions/SESSION_WRAP_UP_TAG148.md` - Was wurde gemacht
- `api/werkstatt_data.py` - Bestehende Implementierung
- `api/werkstatt_live_api.py` - Zu migrierende Funktionen

**DB-Schema:**
- `docs/DB_SCHEMA_LOCOSOFT.md` - Tabellen-Struktur

**Strategie:**
- `docs/sessions/TAG147_COMPLETE_DRIVE_ANALYSIS.md` - Gesamtstrategie

---

## 🎯 ERFOLGS-KRITERIEN TAG 149

### Definition of Done:
✅ TAG148 Code deployed + getestet
✅ 5 weitere Funktionen migriert
✅ werkstatt_live_api.py: 5.367 → ~3.666 Zeilen
✅ werkstatt_data.py: 509 → ~1.600 Zeilen
✅ Alle Endpoints funktionieren (API-Tests)
✅ Git Commit erstellt (lokal + Server)
✅ Session-Dokumentation erstellt

---

## 💡 NÄCHSTE SESSION (TAG 150)

**Vorbereitung:**
- Restliche werkstatt_live_api.py Funktionen (~17)
- teile_data.py erstellen (600 LOC)
- Teile-APIs migrieren

**Impact TAG149+150 kombiniert:**
- werkstatt_live_api.py: 5.532 → ~1.500 Zeilen (73% Reduktion!)
- Neue Datenmodule: werkstatt_data.py (~1.600 LOC) + teile_data.py (~600 LOC)
- **37% aller DRIVE Features** profitieren davon!

---

**Erstellt von:** Claude Sonnet 4.5
**Basis:** TAG 148 Proof-of-Concept
**Nächste Session:** TAG 149 - Werkstatt Modularisierung fortsetzen
**Geschätzter Aufwand:** 4-5 Stunden
