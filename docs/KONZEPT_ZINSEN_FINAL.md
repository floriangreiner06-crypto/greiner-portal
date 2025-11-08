# KONZEPT: FAHRZEUGE MIT ZINSEN - FINAL

**Datum:** 08.11.2025  
**Feature:** Fahrzeuge mit laufenden Zinsen (mit Santander-Zinsdaten!)  
**Priorität:** 🔴 HOCH  
**Status:** ✅ READY TO IMPLEMENT

---

## 🎯 DATENQUELLEN-ÜBERSICHT

### ✅ SANTANDER (Komplett):
| Feld | Quelle | Beispiel | Verfügbar |
|------|--------|----------|-----------|
| Zins Startdatum | CSV Spalte 11 | 02.04.2024 | ✅ |
| Zinsen Gesamt | CSV Spalte 27 | 2.736,19 € | ✅ |
| Zinsen letzte Periode | CSV Spalte 26 | 105,69 € | ✅ |
| Endfälligkeit | CSV Spalte 10 | 23.03.2026 | ✅ |
| Tage seit Zinsstart | BERECHNET | 585 Tage | ✅ |

### ⚠️ STELLANTIS (Limitiert):
| Feld | Quelle | Beispiel | Verfügbar |
|------|--------|----------|-----------|
| Zinsfreiheit Tage | Excel Spalte 9 | -45 | ✅ |
| Tage seit Zinsstart | BERECHNET (abs) | 45 Tage | ✅ |
| Zinsen | - | - | ❌ |
| Endfälligkeit | - | - | ❌ |

---

## 🏗️ DATENBANK-SCHEMA UPDATE

### Migration: `007_add_zinsdaten.sql`

```sql
-- Backup erstellen VORHER!
-- cp data/greiner_controlling.db data/greiner_controlling.db.backup_zinsen_$(date +%Y%m%d_%H%M%S)

-- Neue Spalten für Santander-Zinsdaten
ALTER TABLE fahrzeugfinanzierungen ADD COLUMN zins_startdatum DATE;
ALTER TABLE fahrzeugfinanzierungen ADD COLUMN endfaelligkeit DATE;

-- View mit intelligenter Zinsberechnung
DROP VIEW IF EXISTS fahrzeuge_mit_zinsen;

CREATE VIEW fahrzeuge_mit_zinsen AS
SELECT 
    f.*,
    -- Zinsstatus ermitteln
    CASE 
        -- Santander: Hat explizites Zins-Startdatum
        WHEN f.zins_startdatum IS NOT NULL 
             AND date(f.zins_startdatum) <= date('now') THEN 'Zinsen laufen'
        
        -- Stellantis: Hat nur zinsfreiheit_tage
        WHEN f.zinsfreiheit_tage < 0 THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage <= 30 THEN 'Warnung (< 30 Tage)'
        WHEN f.zinsfreiheit_tage <= 60 THEN 'Achtung (< 60 Tage)'
        
        ELSE 'OK'
    END as zinsstatus,
    
    -- Tage seit Zinsstart berechnen
    CASE
        -- Santander: Differenz zu heute
        WHEN f.zins_startdatum IS NOT NULL THEN
            CAST(julianday('now') - julianday(f.zins_startdatum) AS INTEGER)
        
        -- Stellantis: Absoluter Wert von zinsfreiheit_tage
        WHEN f.zinsfreiheit_tage < 0 THEN
            ABS(f.zinsfreiheit_tage)
        
        ELSE 0
    END as tage_seit_zinsstart,
    
    -- Tage bis Endfälligkeit (nur Santander)
    CASE
        WHEN f.endfaelligkeit IS NOT NULL THEN
            CAST(julianday(f.endfaelligkeit) - julianday('now') AS INTEGER)
        ELSE NULL
    END as tage_bis_endfaelligkeit,
    
    -- Tilgung in Prozent
    ROUND(((f.original_betrag - f.aktueller_saldo) / NULLIF(f.original_betrag, 0) * 100), 2) as tilgung_prozent,
    
    -- Geschätzte monatliche Zinskosten (nur Santander mit zinsen_letzte_periode)
    CASE
        WHEN f.zinsen_letzte_periode IS NOT NULL AND f.zinsen_letzte_periode > 0 THEN
            ROUND(f.zinsen_letzte_periode, 2)
        ELSE NULL
    END as zinsen_monatlich_geschaetzt

FROM fahrzeugfinanzierungen f
WHERE 
    -- Nur Fahrzeuge die Zinsen verursachen oder bald verursachen werden
    (f.zins_startdatum IS NOT NULL AND date(f.zins_startdatum) <= date('now'))
    OR f.zinsfreiheit_tage <= 60
ORDER BY 
    -- Sortierung: Schlimmste zuerst
    CASE 
        WHEN f.zinsen_gesamt IS NOT NULL THEN f.zinsen_gesamt  -- Santander: Nach Zinshöhe
        WHEN f.zinsfreiheit_tage < 0 THEN f.zinsfreiheit_tage  -- Stellantis: Nach Tagen
        ELSE 999999
    END ASC;

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_zins_startdatum ON fahrzeugfinanzierungen(zins_startdatum)
    WHERE zins_startdatum IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_endfaelligkeit ON fahrzeugfinanzierungen(endfaelligkeit)
    WHERE endfaelligkeit IS NOT NULL;

-- Test-Query
SELECT 
    finanzinstitut,
    COUNT(*) as anzahl,
    SUM(CASE WHEN zinsstatus = 'Zinsen laufen' THEN 1 ELSE 0 END) as zinsen_laufen,
    ROUND(SUM(CASE WHEN zinsstatus = 'Zinsen laufen' THEN aktueller_saldo ELSE 0 END), 2) as saldo_mit_zinsen,
    ROUND(SUM(CASE WHEN zinsstatus = 'Zinsen laufen' THEN zinsen_gesamt ELSE 0 END), 2) as zinsen_gesamt
FROM fahrzeuge_mit_zinsen
GROUP BY finanzinstitut;
```

---

## 📋 IMPORT-SCRIPT UPDATE

### Santander-Import erweitern (`import_santander_bestand.py`):

```python
# In der parse_row() Funktion HINZUFÜGEN:

# NEU: Zinsdaten extrahieren (Spalten 11, 26, 27)
zins_startdatum = row.get('Zins Startdatum', '').strip()
endfaelligkeit = row.get('Endfälligkeit', '').strip()
zinsen_letzte_periode = row.get('Zinsen letzte Periode', '').strip()

# Datum-Parsing (Format: DD.MM.YYYY)
if zins_startdatum and zins_startdatum != '':
    try:
        zins_startdatum_parsed = datetime.strptime(zins_startdatum, '%d.%m.%Y').strftime('%Y-%m-%d')
    except:
        zins_startdatum_parsed = None
else:
    zins_startdatum_parsed = None

if endfaelligkeit and endfaelligkeit != '':
    try:
        endfaelligkeit_parsed = datetime.strptime(endfaelligkeit, '%d.%m.%Y').strftime('%Y-%m-%d')
    except:
        endfaelligkeit_parsed = None
else:
    endfaelligkeit_parsed = None

# Zinsen parsen (Format: 1.234,56)
if zinsen_letzte_periode and zinsen_letzte_periode != '':
    try:
        zinsen_letzte_periode_parsed = parse_german_decimal(zinsen_letzte_periode)
    except:
        zinsen_letzte_periode_parsed = None
else:
    zinsen_letzte_periode_parsed = None

# INSERT-Statement ERWEITERN:
c.execute("""
    INSERT INTO fahrzeugfinanzierungen 
    (..., zins_startdatum, endfaelligkeit, zinsen_letzte_periode, ...)
    VALUES (?, ?, ?, ...)
""", (..., zins_startdatum_parsed, endfaelligkeit_parsed, zinsen_letzte_periode_parsed, ...))
```

---

## 🌐 API-ENDPOINT

```python
@bankenspiegel_bp.route('/api/bankenspiegel/fahrzeuge-mit-zinsen', methods=['GET'])
def get_fahrzeuge_mit_zinsen():
    """
    GET /api/bankenspiegel/fahrzeuge-mit-zinsen
    
    Query-Parameter:
    - status: 'zinsen_laufen', 'warnung', 'alle' (default: 'zinsen_laufen')
    - institut: 'Stellantis', 'Santander', 'alle' (default: 'alle')
    - limit: Anzahl (default: 100)
    
    Response:
    {
        "fahrzeuge": [
            {
                "vin": "VXKUKZKXZPW051923",
                "modell": "Mokka-e",
                "finanzinstitut": "Santander",
                "zinsstatus": "Zinsen laufen",
                "tage_seit_zinsstart": 585,
                "aktueller_saldo": -24483.44,
                "zinsen_gesamt": 2736.19,          ← Santander!
                "zinsen_letzte_periode": 105.69,    ← Santander!
                "zinsen_monatlich_geschaetzt": 105.69,
                "endfaelligkeit": "2026-03-23",    ← Santander!
                "tage_bis_endfaelligkeit": 501,
                "tilgung_prozent": 28.5,
                "alter_tage": 950
            },
            {
                "vin": "S1039787",
                "modell": "Corsa",
                "finanzinstitut": "Stellantis",
                "zinsstatus": "Zinsen laufen",
                "tage_seit_zinsstart": 45,
                "aktueller_saldo": 25000.00,
                "zinsen_gesamt": null,              ← Stellantis!
                "zinsen_letzte_periode": null,      ← Stellantis!
                "endfaelligkeit": null,             ← Stellantis!
                "tilgung_prozent": 16.7
            }
        ],
        "statistik": {
            "anzahl_fahrzeuge": 15,
            "gesamt_saldo": 450000.00,
            "gesamt_zinsen": 12500.50,  ← Nur Santander summiert!
            "durchschnitt_tage_seit_zinsstart": 145.3,
            "santander": {
                "anzahl": 8,
                "zinsen_gesamt": 12500.50,
                "zinsen_monatlich": 850.45
            },
            "stellantis": {
                "anzahl": 7,
                "zinsen_gesamt": null
            }
        }
    }
    """
    conn = get_db()
    c = conn.cursor()
    
    status = request.args.get('status', 'zinsen_laufen')
    institut = request.args.get('institut', 'alle')
    limit = int(request.args.get('limit', 100))
    
    query = "SELECT * FROM fahrzeuge_mit_zinsen WHERE 1=1"
    params = []
    
    if status == 'zinsen_laufen':
        query += " AND zinsstatus = 'Zinsen laufen'"
    elif status == 'warnung':
        query += " AND zinsstatus LIKE '%Warnung%'"
    
    if institut != 'alle':
        query += " AND finanzinstitut = ?"
        params.append(institut)
    
    query += " LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    columns = [description[0] for description in c.description]
    rows = c.fetchall()
    
    fahrzeuge = [dict(zip(columns, row)) for row in rows]
    
    # Statistik berechnen
    gesamt_saldo = sum(f['aktueller_saldo'] or 0 for f in fahrzeuge)
    
    # Zinsen-Summe (nur Santander hat echte Werte)
    gesamt_zinsen = sum(f['zinsen_gesamt'] or 0 for f in fahrzeuge)
    
    # Nach Institut aufschlüsseln
    santander_fz = [f for f in fahrzeuge if f['finanzinstitut'] == 'Santander']
    stellantis_fz = [f for f in fahrzeuge if f['finanzinstitut'] == 'Stellantis']
    
    santander_zinsen = sum(f['zinsen_gesamt'] or 0 for f in santander_fz)
    santander_zinsen_monatlich = sum(f['zinsen_monatlich_geschaetzt'] or 0 for f in santander_fz)
    
    avg_tage = sum(f['tage_seit_zinsstart'] or 0 for f in fahrzeuge) / len(fahrzeuge) if fahrzeuge else 0
    
    return jsonify({
        'fahrzeuge': fahrzeuge,
        'statistik': {
            'anzahl_fahrzeuge': len(fahrzeuge),
            'gesamt_saldo': round(gesamt_saldo, 2),
            'gesamt_zinsen': round(gesamt_zinsen, 2) if gesamt_zinsen > 0 else None,
            'durchschnitt_tage_seit_zinsstart': round(avg_tage, 1),
            'santander': {
                'anzahl': len(santander_fz),
                'zinsen_gesamt': round(santander_zinsen, 2) if santander_zinsen > 0 else None,
                'zinsen_monatlich': round(santander_zinsen_monatlich, 2) if santander_zinsen_monatlich > 0 else None
            },
            'stellantis': {
                'anzahl': len(stellantis_fz),
                'zinsen_gesamt': None  # Stellantis hat keine Zinsdaten
            }
        }
    })
```

---

## 🎨 FRONTEND HTML

**Erweiterte Statistik-Karten:**

```html
<div class="row g-3 mb-3">
    <!-- Bestehende Karten -->
    <div class="col-md-3">
        <div class="card bg-danger bg-opacity-10">
            <div class="card-body text-center">
                <small class="text-muted d-block mb-1">Betroffene Fahrzeuge</small>
                <h3 id="zinsenAnzahl" class="mb-0 text-danger">-</h3>
                <small class="text-muted mt-1">
                    <span id="zinsenSantanderCount">-</span> Santander | 
                    <span id="zinsenStellantisCount">-</span> Stellantis
                </small>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card bg-danger bg-opacity-10">
            <div class="card-body text-center">
                <small class="text-muted d-block mb-1">Gesamt-Finanzierung</small>
                <h3 id="zinsenSaldo" class="mb-0 text-danger">-</h3>
            </div>
        </div>
    </div>
    
    <!-- NEU: Zinsen-Karten (nur für Santander) -->
    <div class="col-md-3">
        <div class="card bg-warning bg-opacity-10">
            <div class="card-body text-center">
                <small class="text-muted d-block mb-1">
                    <i class="bi bi-cash-coin me-1"></i>Zinsen Gesamt
                </small>
                <h3 id="zinsenGesamt" class="mb-0 text-warning">-</h3>
                <small class="text-muted mt-1">Nur Santander</small>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="card bg-info bg-opacity-10">
            <div class="card-body text-center">
                <small class="text-muted d-block mb-1">
                    <i class="bi bi-calendar-month me-1"></i>Zinsen/Monat Ø
                </small>
                <h3 id="zinsenMonatlich" class="mb-0 text-info">-</h3>
                <small class="text-muted mt-1">Nur Santander</small>
            </div>
        </div>
    </div>
</div>
```

**Erweiterte Tabelle:**

```html
<table class="table table-hover table-sm mb-0" id="zinsenTable">
    <thead class="table-light">
        <tr>
            <th>Institut</th>
            <th>VIN</th>
            <th>Modell</th>
            <th class="text-end">
                <i class="bi bi-clock-history me-1"></i>
                Tage seit Zinsstart
            </th>
            <th class="text-end">
                <i class="bi bi-wallet2 me-1"></i>
                Saldo
            </th>
            <th class="text-end">
                <i class="bi bi-cash-coin me-1"></i>
                Zinsen Gesamt
            </th>
            <th class="text-end">
                <i class="bi bi-calendar-month me-1"></i>
                Zinsen/Monat
            </th>
            <th class="text-end">
                <i class="bi bi-calendar-event me-1"></i>
                Endfälligkeit
            </th>
            <th class="text-end">Tilgung</th>
        </tr>
    </thead>
    <tbody id="zinsenTableBody">
        <!-- Dynamisch via JS -->
    </tbody>
</table>
```

---

## 💻 FRONTEND JAVASCRIPT

```javascript
async function loadFahrzeugeMitZinsen() {
    try {
        const institut = document.getElementById('zinsenInstitutFilter')?.value || 'alle';
        const response = await fetch(`/api/bankenspiegel/fahrzeuge-mit-zinsen?status=zinsen_laufen&institut=${institut}`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if (data.fahrzeuge && data.fahrzeuge.length > 0) {
            document.getElementById('zinsenSection').classList.remove('d-none');
            
            // Statistik
            document.getElementById('zinsenAnzahl').textContent = data.statistik.anzahl_fahrzeuge;
            document.getElementById('zinsenSaldo').textContent = formatCurrency(data.statistik.gesamt_saldo);
            
            // Santander/Stellantis Split
            document.getElementById('zinsenSantanderCount').textContent = data.statistik.santander.anzahl;
            document.getElementById('zinsenStellantisCount').textContent = data.statistik.stellantis.anzahl;
            
            // Zinsen (nur wenn Santander-Daten vorhanden)
            if (data.statistik.gesamt_zinsen) {
                document.getElementById('zinsenGesamt').textContent = formatCurrency(data.statistik.gesamt_zinsen);
            } else {
                document.getElementById('zinsenGesamt').textContent = 'N/A';
            }
            
            if (data.statistik.santander.zinsen_monatlich) {
                document.getElementById('zinsenMonatlich').textContent = formatCurrency(data.statistik.santander.zinsen_monatlich);
            } else {
                document.getElementById('zinsenMonatlich').textContent = 'N/A';
            }
            
            // Tabelle
            const tbody = document.getElementById('zinsenTableBody');
            tbody.innerHTML = data.fahrzeuge.map(fz => {
                const tage = fz.tage_seit_zinsstart || 0;
                const severity = tage > 90 ? 'danger' : tage > 60 ? 'warning' : 'info';
                
                // Zinsen-Spalten (nur bei Santander)
                const zinsenGesamt = fz.zinsen_gesamt 
                    ? `<span class="text-danger fw-bold">${formatCurrency(fz.zinsen_gesamt)}</span>`
                    : '<span class="text-muted">N/A</span>';
                
                const zinsenMonatlich = fz.zinsen_monatlich_geschaetzt
                    ? `<span class="text-warning">${formatCurrency(fz.zinsen_monatlich_geschaetzt)}</span>`
                    : '<span class="text-muted">N/A</span>';
                
                // Endfälligkeit (nur bei Santander)
                let endfaelligkeit = '<span class="text-muted">N/A</span>';
                if (fz.endfaelligkeit) {
                    const tage_bis = fz.tage_bis_endfaelligkeit || 0;
                    const datum = new Date(fz.endfaelligkeit).toLocaleDateString('de-DE');
                    const color = tage_bis < 180 ? 'danger' : tage_bis < 365 ? 'warning' : 'info';
                    endfaelligkeit = `
                        <div class="small">
                            ${datum}<br>
                            <span class="badge bg-${color}">${tage_bis} Tage</span>
                        </div>
                    `;
                }
                
                return `
                    <tr>
                        <td><span class="badge bg-${severity}">${fz.finanzinstitut}</span></td>
                        <td><code class="small">${fz.vin}</code></td>
                        <td>${fz.modell || 'N/A'}</td>
                        <td class="text-end">
                            <span class="badge bg-${severity} px-3">
                                <strong>${tage}</strong> Tage
                            </span>
                        </td>
                        <td class="text-end text-danger fw-bold">
                            ${formatCurrency(fz.aktueller_saldo)}
                        </td>
                        <td class="text-end">${zinsenGesamt}</td>
                        <td class="text-end">${zinsenMonatlich}</td>
                        <td class="text-end">${endfaelligkeit}</td>
                        <td class="text-end">
                            <div class="progress" style="height: 8px; width: 80px; display: inline-block;">
                                <div class="progress-bar bg-success" 
                                     style="width: ${fz.tilgung_prozent || 0}%"></div>
                            </div>
                            <small class="ms-2">${(fz.tilgung_prozent || 0).toFixed(1)}%</small>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            document.getElementById('zinsenSection').classList.add('d-none');
        }
    } catch (error) {
        console.error('Fehler beim Laden der Fahrzeuge mit Zinsen:', error);
    }
}
```

---

## 🚀 UMSETZUNGS-PLAN

### SCHRITT 1: Migration (10 Min)
```bash
cd /opt/greiner-portal

# Backup
cp data/greiner_controlling.db data/greiner_controlling.db.backup_zinsen_$(date +%Y%m%d_%H%M%S)

# Migration
sqlite3 data/greiner_controlling.db < migrations/007_add_zinsdaten.sql

# Test
sqlite3 data/greiner_controlling.db "SELECT COUNT(*) FROM fahrzeuge_mit_zinsen WHERE zinsstatus = 'Zinsen laufen';"
```

### SCHRITT 2: Santander-Import erweitern (15 Min)
```bash
nano scripts/imports/import_santander_bestand.py
# Zinsdaten-Parsing hinzufügen
# Speichern & Test-Import
python3 scripts/imports/import_santander_bestand.py
```

### SCHRITT 3: API-Endpoint (10 Min)
```bash
nano api/bankenspiegel_api.py
# Endpoint hinzufügen
```

### SCHRITT 4: Frontend HTML (15 Min)
```bash
nano templates/einkaufsfinanzierung.html
# HTML-Section hinzufügen
```

### SCHRITT 5: Frontend JS (15 Min)
```bash
nano static/js/einkaufsfinanzierung.js
# JavaScript-Funktion hinzufügen
```

### SCHRITT 6: Flask Restart & Test (5 Min)
```bash
# Flask neu starten
kill <PID1> <PID2>
nohup python app.py > logs/flask.log 2>&1 &

# Browser testen
# http://10.80.80.20:5000/bankenspiegel/einkaufsfinanzierung
```

---

## ⏱️ ZEIT-SCHÄTZUNG

| Schritt | Zeit | Status |
|---------|------|--------|
| Migration | 10 Min | ✅ Ready |
| Santander-Import | 15 Min | ✅ Ready |
| API-Endpoint | 10 Min | ✅ Ready |
| Frontend HTML | 15 Min | ✅ Ready |
| Frontend JS | 15 Min | ✅ Ready |
| Test & Deploy | 5 Min | ✅ Ready |
| **GESAMT** | **~70 Min** | 🎯 |

---

## 🎉 ERGEBNIS

### Was du bekommen wirst:

**Santander-Fahrzeuge:**
- ✅ Tage seit Zinsstart
- ✅ **Zinsen Gesamt (€)** ← NEU!
- ✅ **Zinsen/Monat (€)** ← NEU!
- ✅ **Endfälligkeit** ← NEU!
- ✅ Tilgung in %

**Stellantis-Fahrzeuge:**
- ✅ Tage seit Zinsstart
- ⚠️ Zinsen: N/A (nicht verfügbar)
- ✅ Tilgung in %

**Statistik:**
- ✅ Gesamt-Anzahl (beide Institute)
- ✅ Gesamt-Saldo (beide Institute)
- ✅ **Zinsen Gesamt (nur Santander)**
- ✅ **Zinsen/Monat Ø (nur Santander)**
- ✅ Split Santander vs. Stellantis

---

## 📋 BEREIT ZUM START?

Alle Code-Snippets sind fertig!

Möchtest du:
**A)** JETZT sofort mit SCHRITT 1 (Migration) starten?
**B)** Alle Code-Dateien als Downloads haben?
**C)** Erst mal Fragen klären?

🚀 **Let's go!**
