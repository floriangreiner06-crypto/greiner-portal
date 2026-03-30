# Kumulierte Zielprämie — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zielprämie (I_neuwagen) um kumulierte Monatsbetrachtung erweitern — Gate ist kumuliertes Ziel (Jan bis aktueller Monat), Übererfüllung rein monatlich.

**Architecture:** Neues Boolean-Feld `use_kumuliert` in `provision_config`. Neue Hilfsfunktion `get_kumulierte_zielpraemie_daten()` in `provision_service.py` berechnet kumulierte Werte on-the-fly. Ergebnisse werden im Result-Dict durchgereicht für Detail-Seite und PDF.

**Tech Stack:** PostgreSQL, Python/Flask, Jinja2/Bootstrap, ReportLab (PDF)

**Spec:** `docs/superpowers/specs/2026-03-30-kumulierte-zielpraemie-design.md`

---

### Task 1: DB-Migration — `use_kumuliert` Spalte

**Files:**
- Create: `migrations/add_provision_config_use_kumuliert.sql`

- [ ] **Step 1: Migration-Datei anlegen**

```sql
-- migrations/add_provision_config_use_kumuliert.sql
-- Kumulierte Zielprämie: Gate ist kumuliertes Monatsziel (Jan bis aktueller Monat)
ALTER TABLE provision_config ADD COLUMN IF NOT EXISTS use_kumuliert BOOLEAN DEFAULT false;

-- Aktivierung für bestehende Zielerfüllung-Zeile (I_neuwagen)
UPDATE provision_config
SET use_kumuliert = true
WHERE kategorie = 'I_neuwagen'
  AND use_zielpraemie = true;
```

- [ ] **Step 2: Migration auf beiden DBs ausführen**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -f migrations/add_provision_config_use_kumuliert.sql
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_provision_config_use_kumuliert.sql
```

Expected: `ALTER TABLE` + `UPDATE 1` (oder ähnlich)

- [ ] **Step 3: Verifizieren**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT id, kategorie, bezeichnung, use_zielpraemie, use_kumuliert FROM provision_config WHERE use_zielpraemie = true"
```

Expected: Zeile `I_neuwagen / Zielerfüllung` mit `use_kumuliert = true`.

- [ ] **Step 4: Commit**

```bash
git add migrations/add_provision_config_use_kumuliert.sql
git commit -m "feat(provision): DB-Migration use_kumuliert für kumulierte Zielprämie"
```

---

### Task 2: Hilfsfunktion `get_stueck_nw_fuer_monat()` in provision_service.py

Kapselt die NW-Stückzählung für einen beliebigen Monat (Auslieferung oder Auftragseingang).

**Files:**
- Modify: `api/provision_service.py` (nach `get_nw_auftragseingang_stueck`, ca. Zeile 240)

- [ ] **Step 1: Funktion einfügen**

In `api/provision_service.py`, nach der bestehenden Funktion `get_nw_auftragseingang_stueck()` (Zeile ~238) und vor `_get_float()` (Zeile ~241), folgende Funktion einfügen:

```python
def get_stueck_nw_fuer_monat(vkb: int, jahr: int, monat_nr: int, basis: str = 'auslieferung') -> int:
    """NW-Stück für VKB in einem bestimmten Monat. Basis: 'auslieferung' oder 'auftragseingang'."""
    monat_str = f"{jahr}-{monat_nr:02d}"
    if basis == 'auftragseingang':
        return get_nw_auftragseingang_stueck(vkb, monat_str)
    # Auslieferung: Zählung über out_invoice_date in sales (gleiche Logik wie in berechne_live_provision)
    with db_session() as conn:
        cur = conn.cursor()
        cfg_i = get_provision_config_for_monat(monat_str).get('I_neuwagen') or {}
        p1_target = (cfg_i.get('memo_p1_kategorie') or '').strip()
        where_p1 = ""
        if p1_target in ('II_testwagen', 'III_gebrauchtwagen'):
            where_p1 = "AND UPPER(COALESCE(TRIM(s.memo), '')) <> 'P1'"
        cur.execute(f"""
            SELECT COUNT(*) AS anzahl FROM sales s
            WHERE EXTRACT(YEAR FROM s.out_invoice_date) = %s
              AND EXTRACT(MONTH FROM s.out_invoice_date) = %s
              AND s.salesman_number = %s
              AND (
                    s.dealer_vehicle_type = 'N'
                    OR (s.dealer_vehicle_type IN ('T', 'V')
                        AND (s.first_registration_date IS NULL
                             OR (s.out_invoice_date::date - s.first_registration_date) <= 365))
              )
              AND NOT EXISTS (
                    SELECT 1 FROM sales s2
                    WHERE s2.vin = s.vin AND s2.out_invoice_date = s.out_invoice_date
                      AND s2.dealer_vehicle_type IN ('T', 'V') AND s.dealer_vehicle_type = 'N'
              )
              {where_p1}
        """, (str(jahr), f"{monat_nr:02d}", vkb))
        row = cur.fetchone()
    return int((row.get('anzahl') if hasattr(row, 'get') else row[0]) or 0)
```

- [ ] **Step 2: Manuell testen**

```bash
cd /opt/greiner-test && .venv/bin/python -c "
from api.provision_service import get_stueck_nw_fuer_monat
# Einen bekannten Verkäufer testen (z.B. VKB aus letztem Vorlauf)
result = get_stueck_nw_fuer_monat(22, 2026, 1, 'auslieferung')
print(f'Jan 2026 Auslieferung: {result} Stk.')
result2 = get_stueck_nw_fuer_monat(22, 2026, 2, 'auslieferung')
print(f'Feb 2026 Auslieferung: {result2} Stk.')
"
```

Expected: Ganzzahlige Werte ohne Fehler.

- [ ] **Step 3: Commit**

```bash
git add api/provision_service.py
git commit -m "feat(provision): Hilfsfunktion get_stueck_nw_fuer_monat für beliebige Monate"
```

---

### Task 3: `get_provision_config_for_monat()` — use_kumuliert laden

**WICHTIG:** Muss vor Task 4 erledigt werden, sonst ist `cfg_i.get('use_kumuliert')` immer `None`.

**Files:**
- Modify: `api/provision_service.py:73-116` (SELECT + Dict-Building)

- [ ] **Step 1: SELECT erweitern**

In `api/provision_service.py`, Zeile ~78-80, im ersten SELECT-Block nach `memo_p1_kategorie` ergänzen:

```sql
                       COALESCE(use_kumuliert, false) AS use_kumuliert
```

Und im Fallback-SELECT (Zeile ~87-94) ebenfalls, falls dort erweiterte Spalten fehlen — dort wird `use_kumuliert` nicht geladen, was OK ist (Fallback = alte Spalten).

- [ ] **Step 2: Dict-Building erweitern**

In der Dict-Zuweisung (Zeile ~99-116), nach `'memo_p1_kategorie':` eine neue Zeile einfügen:

```python
            'use_kumuliert': bool(r.get('use_kumuliert')),
```

- [ ] **Step 3: Testen**

```bash
cd /opt/greiner-test && .venv/bin/python -c "
from api.provision_service import get_provision_config_for_monat
cfg = get_provision_config_for_monat('2026-03')
print('I_neuwagen use_kumuliert:', cfg.get('I_neuwagen', {}).get('use_kumuliert'))
"
```

Expected: `True` (da in Task 1 aktiviert).

- [ ] **Step 4: Commit**

```bash
git add api/provision_service.py
git commit -m "fix(provision): use_kumuliert in get_provision_config_for_monat laden"
```

---

### Task 4: Kernlogik `get_kumulierte_zielpraemie_daten()` in provision_service.py

**Files:**
- Modify: `api/provision_service.py` (nach `get_stueck_nw_fuer_monat`, vor `_get_float`)

- [ ] **Step 1: Funktion einfügen**

```python
def get_kumulierte_zielpraemie_daten(vkb: int, monat: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kumulierte Zielprämie: Gate = kum. IST >= kum. Ziel (Jan bis Monat).
    Übererfüllung = rein monatlich (Monats-IST - Monats-Ziel), nur wenn Gate bestanden.
    """
    jahr_int = int(monat[:4])
    monat_int = int(monat[5:7])
    basis = (config.get('zielpraemie_basis') or 'auslieferung').strip().lower()
    fallback_ziel = int(config.get('zielpraemie_fallback_ziel') or 0)

    kum_ziel = 0
    kum_ist = 0
    monats_ziel = 0
    monats_ist = 0

    for m in range(1, monat_int + 1):
        ziel_m = get_nw_ziel_verkaeufer_monat(vkb, jahr_int, m) if get_nw_ziel_verkaeufer_monat else 0
        if ziel_m == 0 and fallback_ziel:
            ziel_m = fallback_ziel
        ist_m = get_stueck_nw_fuer_monat(vkb, jahr_int, m, basis)
        kum_ziel += ziel_m
        kum_ist += ist_m
        if m == monat_int:
            monats_ziel = ziel_m
            monats_ist = ist_m

    gate = kum_ziel > 0 and kum_ist >= kum_ziel
    ziel_eur = float(config.get('zielerreichung_betrag') or 0) if gate else 0.0
    monats_ueber = max(0, monats_ist - monats_ziel) if gate else 0
    ueber_eur_pro_stueck = float(config.get('stueck_praemie') or 0)
    uebererfuellung_betrag = monats_ueber * ueber_eur_pro_stueck
    stueckpraemie_gesamt = ziel_eur + uebererfuellung_betrag

    return {
        'kum_ziel': kum_ziel,
        'kum_ist': kum_ist,
        'kum_erfuellt': gate,
        'monats_ziel': monats_ziel,
        'monats_ist': monats_ist,
        'monats_ueber': monats_ueber,
        'zielerreichung_betrag': ziel_eur,
        'uebererfuellung_betrag': round(uebererfuellung_betrag, 2),
        'ueber_eur_pro_stueck': ueber_eur_pro_stueck,
        'stueckpraemie_gesamt': round(stueckpraemie_gesamt, 2),
    }
```

- [ ] **Step 2: Manuell testen**

```bash
cd /opt/greiner-test && .venv/bin/python -c "
from api.provision_service import get_kumulierte_zielpraemie_daten, get_provision_config_for_monat
cfg = get_provision_config_for_monat('2026-03').get('I_neuwagen') or {}
print('Config use_kumuliert:', cfg.get('use_kumuliert'))
result = get_kumulierte_zielpraemie_daten(22, '2026-03', cfg)
for k, v in result.items():
    print(f'  {k}: {v}')
"
```

Expected: Dict mit allen kumulierten Werten, kein Fehler.

- [ ] **Step 3: Commit**

```bash
git add api/provision_service.py
git commit -m "feat(provision): Kernlogik get_kumulierte_zielpraemie_daten (kumuliertes Gate + monatliche Übererfüllung)"
```

---

### Task 5: Integration in `berechne_live_provision()` + Result-Dict

**Files:**
- Modify: `api/provision_service.py:478-497` (Zielprämie-Block)
- Modify: `api/provision_service.py:513-537` (Return-Dict)

- [ ] **Step 1: Zielprämie-Block anpassen**

In `api/provision_service.py`, den Block ab Zeile 478 ersetzen. Der alte Code:

```python
    zielpraemie_basis = (cfg_i.get('zielpraemie_basis') or 'auslieferung').strip().lower()
    stueck_nw_zielpraemie = stueck_nw
    if zielpraemie_basis == 'auftragseingang':
        stueck_nw_zielpraemie = get_nw_auftragseingang_stueck(vkb, monat)

    # Zielprämie (NW): Ziel aus Verkäufer-Zielplanung; Basis konfigurierbar (Auslieferung/Auftragseingang)
    if cfg_i.get('use_zielpraemie') and get_nw_ziel_verkaeufer_monat:
        jahr_int = int(monat[:4])
        monat_int = int(monat[5:7])
        nw_ziel = get_nw_ziel_verkaeufer_monat(vkb, jahr_int, monat_int)
        if nw_ziel == 0 and cfg_i.get('zielpraemie_fallback_ziel'):
            nw_ziel = int(cfg_i['zielpraemie_fallback_ziel'])
        if nw_ziel and stueck_nw_zielpraemie >= nw_ziel:
            ziel_eur = float(cfg_i.get('zielerreichung_betrag') or 100)
            ueber_eur = float(cfg_i.get('stueck_praemie') or 50)
            stueck_praemie_anteil = ziel_eur + max(0, stueck_nw_zielpraemie - nw_ziel) * ueber_eur
        else:
            stueck_praemie_anteil = 0.0
    else:
        stueck_praemie_anteil = (cfg_i.get('stueck_praemie') or 50) * min(stueck_nw, (cfg_i.get('stueck_max') or 15))
```

Wird ersetzt durch:

```python
    zielpraemie_basis = (cfg_i.get('zielpraemie_basis') or 'auslieferung').strip().lower()
    stueck_nw_zielpraemie = stueck_nw
    if zielpraemie_basis == 'auftragseingang':
        stueck_nw_zielpraemie = get_nw_auftragseingang_stueck(vkb, monat)

    kum_daten = None  # Kumulierte Daten für Detail/PDF

    # Zielprämie (NW): Ziel aus Verkäufer-Zielplanung; Basis konfigurierbar (Auslieferung/Auftragseingang)
    if cfg_i.get('use_zielpraemie') and get_nw_ziel_verkaeufer_monat:
        if cfg_i.get('use_kumuliert'):
            # Kumulierte Zielprämie: Gate = kum. IST >= kum. Ziel (Jan..Monat)
            kum_daten = get_kumulierte_zielpraemie_daten(vkb, monat, cfg_i)
            stueck_praemie_anteil = kum_daten['stueckpraemie_gesamt']
            stueck_nw_zielpraemie = kum_daten['monats_ist']
        else:
            # Bestehende Einzel-Monats-Logik
            jahr_int = int(monat[:4])
            monat_int = int(monat[5:7])
            nw_ziel = get_nw_ziel_verkaeufer_monat(vkb, jahr_int, monat_int)
            if nw_ziel == 0 and cfg_i.get('zielpraemie_fallback_ziel'):
                nw_ziel = int(cfg_i['zielpraemie_fallback_ziel'])
            if nw_ziel and stueck_nw_zielpraemie >= nw_ziel:
                ziel_eur = float(cfg_i.get('zielerreichung_betrag') or 100)
                ueber_eur = float(cfg_i.get('stueck_praemie') or 50)
                stueck_praemie_anteil = ziel_eur + max(0, stueck_nw_zielpraemie - nw_ziel) * ueber_eur
            else:
                stueck_praemie_anteil = 0.0
    else:
        stueck_praemie_anteil = (cfg_i.get('stueck_praemie') or 50) * min(stueck_nw, (cfg_i.get('stueck_max') or 15))
```

- [ ] **Step 2: Return-Dict erweitern**

Im Return-Dict (Zeile ~513), nach `'config'` und vor der schließenden Klammer, `kum_daten` ergänzen:

```python
        'config': {
            'I': cfg_i,
            'II': cfg_ii,
            'III': cfg_iii,
            'IV': cfg_iv,
        },
        'kum_daten': kum_daten,  # None wenn nicht kumuliert
```

- [ ] **Step 3: Manuell testen (Live-Preview)**

```bash
cd /opt/greiner-test && .venv/bin/python -c "
from api.provision_service import berechne_live_provision
result = berechne_live_provision(22, '2026-03')
print('Stückprämie:', result.get('summe_stueckpraemie'))
kum = result.get('kum_daten')
if kum:
    print('Kumuliert:')
    for k, v in kum.items():
        print(f'  {k}: {v}')
else:
    print('Keine Kumulierung (use_kumuliert=false)')
"
```

Expected: `kum_daten` ist ein Dict mit allen Feldern wenn `use_kumuliert=true`.

- [ ] **Step 4: Commit**

```bash
git add api/provision_service.py
git commit -m "feat(provision): Kumulierte Zielprämie in berechne_live_provision integriert"
```

---

### Task 6: API — `use_kumuliert` in Config-Endpoints

**Files:**
- Modify: `api/provision_api.py:905-906` (GET config — SELECT-Spalten)
- Modify: `api/provision_api.py:918-938` (GET config — Defaults/Typen)
- Modify: `api/provision_api.py:1049` (POST config — Feld lesen)
- Modify: `api/provision_api.py:1062-1073` (POST config — INSERT)
- Modify: `api/provision_api.py:1121-1139` (PUT config — Update-Logik)

- [ ] **Step 1: GET — SELECT erweitern**

In `api/provision_api.py`, Zeile ~906, `ext_cols` erweitern:

Alte Zeile:
```python
ext_cols = ", COALESCE(use_zielpraemie, false) AS use_zielpraemie, ziererreichung_betrag, zielpraemie_fallback_ziel, COALESCE(zielpraemie_basis, 'auslieferung') AS zielpraemie_basis, memo_p1_kategorie"
```

Neue Zeile:
```python
ext_cols = ", COALESCE(use_zielpraemie, false) AS use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, COALESCE(zielpraemie_basis, 'auslieferung') AS zielpraemie_basis, memo_p1_kategorie, COALESCE(use_kumuliert, false) AS use_kumuliert"
```

- [ ] **Step 2: GET — Defaults hinzufügen**

Nach Zeile ~923 (`r.setdefault('memo_p1_kategorie', None)`) einfügen:

```python
            r.setdefault('use_kumuliert', False)
```

Nach Zeile ~938 (`r['use_zielpraemie'] = bool(r.get('use_zielpraemie'))`) einfügen:

```python
            r['use_kumuliert'] = bool(r.get('use_kumuliert'))
```

- [ ] **Step 3: POST — Feld lesen und in INSERT**

Nach Zeile ~1049 (`use_zielpraemie = data.get('use_zielpraemie') in (True, 'true', 1, '1')`) einfügen:

```python
    use_kumuliert = data.get('use_kumuliert') in (True, 'true', 1, '1')
```

INSERT-Statement (Zeile ~1062-1073) erweitern: Spalte `use_kumuliert` und Wert `%s` ergänzen, `use_kumuliert` in die Parameterliste.

Spalten-Zeile wird:
```python
                    gueltig_ab, erstellt_von, use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, zielpraemie_basis, memo_p1_kategorie, use_kumuliert
```

VALUES bekommt ein zusätzliches `%s`, und die Parameter-Tuple wird um `use_kumuliert` erweitert:
```python
                  gueltig_ab, erstellt_von, use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, zielpraemie_basis, memo_p1_kategorie, use_kumuliert))
```

- [ ] **Step 4: PUT — Update-Logik**

In der `for key, col in [...]`-Liste (Zeile ~1114-1124), nach `('use_zielpraemie', 'use_zielpraemie')` eine neue Zeile einfügen:

```python
        ('use_kumuliert', 'use_kumuliert'),
```

Und im `if key == 'use_zielpraemie':`-Block (Zeile ~1135-1139) eine analoge Behandlung für `use_kumuliert` ergänzen. Direkt nach dem `use_zielpraemie`-Block:

```python
        if key == 'use_kumuliert':
            val = v in (True, 'true', 1, '1')
            updates.append("use_kumuliert = %s")
            params.append(val)
            continue
```

- [ ] **Step 5: Testen — API aufrufen**

```bash
curl -s http://localhost:5002/api/provision/config -H "Cookie: $(cat /tmp/test_cookie 2>/dev/null)" | python3 -m json.tool | grep -A2 kumuliert || echo "Cookie benötigt — im Browser testen"
```

Alternativ: Direkte DB-Prüfung:
```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT id, kategorie, use_kumuliert FROM provision_config WHERE use_zielpraemie = true"
```

- [ ] **Step 6: Commit**

```bash
git add api/provision_api.py
git commit -m "feat(provision): API GET/POST/PUT für use_kumuliert Feld"
```

---

### Task 7: Config-Modal — Checkbox für Kumulierung

**Files:**
- Modify: `templates/admin/provision_config.html:146-180` (Formular)
- Modify: `templates/admin/provision_config.html:406-410` (JS Load)
- Modify: `templates/admin/provision_config.html:431-434` (JS Save)

- [ ] **Step 1: Checkbox ins Formular einfügen**

In `templates/admin/provision_config.html`, nach dem `use_zielpraemie`-Checkbox-Block (Zeile ~152, nach `</small>`) und vor `</div>` des col-md-4, einen untergeordneten Checkbox einfügen:

```html
                            <div class="form-check ms-4 mt-1" id="kumuliert-wrapper" style="display:none;">
                                <input class="form-check-input" type="checkbox" id="edit-use-kumuliert" name="use_kumuliert">
                                <label class="form-check-label" for="edit-use-kumuliert">Kumulierte Zielerreichung</label>
                                <br><small class="text-muted">Monatsziel muss kumuliert (Jan bis aktueller Monat) erreicht sein.</small>
                            </div>
```

- [ ] **Step 2: JS — Sichtbarkeit steuern**

Im JavaScript-Block, beim Event-Listener für `edit-use-zielpraemie` (oder am Ende des Lade-Codes), Logik für Sichtbarkeit hinzufügen:

```javascript
        // Kumuliert-Checkbox nur anzeigen wenn Zielprämie aktiv
        function toggleKumuliert() {
            var show = document.getElementById('edit-use-zielpraemie').checked;
            document.getElementById('kumuliert-wrapper').style.display = show ? 'block' : 'none';
            if (!show) document.getElementById('edit-use-kumuliert').checked = false;
        }
        document.getElementById('edit-use-zielpraemie').addEventListener('change', toggleKumuliert);
```

- [ ] **Step 3: JS — Wert laden (Load)**

Nach Zeile ~409 (`document.getElementById('edit-zielpraemie-basis').value = ...`) einfügen:

```javascript
        document.getElementById('edit-use-kumuliert').checked = !!item.use_kumuliert;
        toggleKumuliert();
```

- [ ] **Step 4: JS — Wert speichern (Save)**

Nach Zeile ~434 (`zielpraemie_basis: ...`) einfügen:

```javascript
            use_kumuliert: document.getElementById('edit-use-kumuliert').checked,
```

- [ ] **Step 5: Browser-Test**

1. http://drive:5002 öffnen → Provision → Provisionsarten
2. I_neuwagen / Zielerfüllung bearbeiten
3. ☑ Zielprämie (NW) aktiviert → Checkbox „Kumulierte Zielerreichung" sichtbar
4. ☑ Kumulierte Zielerreichung an/aus → Speichern → Reload → Wert bleibt

- [ ] **Step 6: Commit**

```bash
git add templates/admin/provision_config.html
git commit -m "feat(provision): Config-Modal Checkbox für kumulierte Zielerreichung"
```

---

### Task 8: Detail-Seite — Kumulierungs-Info anzeigen

**Files:**
- Modify: `templates/provision/provision_detail.html:1002-1010` (Summentabelle)
- Modify: `routes/provision_routes.py` (kum_daten an Template/API durchreichen)

- [ ] **Step 1: Route/API — kum_daten durchreichen**

Die Detail-Seite holt ihre Daten über die bestehende API. Prüfen ob `get_lauf_detail()` in `provision_service.py` die Live-Daten nutzt oder aus der DB liest. Wenn aus DB: `kum_daten` muss im API-Endpoint `/api/provision/vorlauf/<id>` separat berechnet und angehängt werden.

In `api/provision_api.py`, im GET-Endpoint für Lauf-Detail (der die Daten für die Detail-Seite liefert), nach dem Laden der Lauf-Daten, `kum_daten` berechnen und ins Response einfügen:

```python
    # Kumulierte Zielprämie-Daten berechnen (wenn aktiv)
    kum_daten = None
    if lauf.get('abrechnungsmonat') and lauf.get('verkaufer_id'):
        cfg = get_provision_config_for_monat(lauf['abrechnungsmonat']).get('I_neuwagen') or {}
        if cfg.get('use_kumuliert') and cfg.get('use_zielpraemie'):
            from api.provision_service import get_kumulierte_zielpraemie_daten
            kum_daten = get_kumulierte_zielpraemie_daten(
                lauf['verkaufer_id'], lauf['abrechnungsmonat'], cfg
            )
    # Im Response-Dict:
    result['kum_daten'] = kum_daten
```

- [ ] **Step 2: Detail-Template — Kumulierungs-Info-Block**

In `templates/provision/provision_detail.html`, im JavaScript nach der Summentabelle (Zeile ~1021, nach `sumBody.innerHTML = sumHtml`), einen Info-Block einfügen:

```javascript
        // Kumulierte Zielprämie Info-Block
        var kumBlock = document.getElementById('kumInfo');
        if (kumBlock && l.kum_daten) {
            var kd = l.kum_daten;
            var monatLabel = l.abrechnungsmonat || '';
            var kumHtml = '<div class="card border-0 shadow-sm mb-3">';
            kumHtml += '<div class="card-body py-2 px-3">';
            kumHtml += '<h6 class="mb-2" style="font-size:.85rem;">Kumulierte Zielerreichung (Jan–' + monatLabel.substring(5) + '/' + monatLabel.substring(0,4) + ')</h6>';
            kumHtml += '<div class="row g-2" style="font-size:.82rem;">';
            kumHtml += '<div class="col-auto"><span class="text-muted">Kum. Ziel:</span> <strong>' + kd.kum_ziel + ' Stk.</strong></div>';
            kumHtml += '<div class="col-auto"><span class="text-muted">Kum. IST:</span> <strong>' + kd.kum_ist + ' Stk.</strong></div>';
            kumHtml += '<div class="col-auto">' + (kd.kum_erfuellt ? '<span class="badge bg-success">Erfüllt</span>' : '<span class="badge bg-danger">Nicht erfüllt</span>') + '</div>';
            kumHtml += '</div>';
            if (kd.kum_erfuellt) {
                kumHtml += '<div class="row g-2 mt-1" style="font-size:.82rem;">';
                kumHtml += '<div class="col-auto"><span class="text-muted">Monat:</span> Ziel ' + kd.monats_ziel + ', IST ' + kd.monats_ist;
                if (kd.monats_ueber > 0) kumHtml += ' <span class="text-success">(+' + kd.monats_ueber + ' Übererfüllung)</span>';
                kumHtml += '</div></div>';
                kumHtml += '<div class="mt-1" style="font-size:.82rem;">';
                kumHtml += 'Zielerreichung: ' + fmtEuro(kd.zielerreichung_betrag);
                if (kd.uebererfuellung_betrag > 0) kumHtml += ' + Übererfüllung: ' + fmtEuro(kd.uebererfuellung_betrag) + ' (' + kd.monats_ueber + ' × ' + fmtEuro(kd.ueber_eur_pro_stueck) + ')';
                kumHtml += '</div>';
            } else {
                kumHtml += '<div class="text-muted mt-1" style="font-size:.82rem;">Keine Stückprämie in diesem Monat (kum. Ziel nicht erreicht).</div>';
            }
            kumHtml += '</div></div>';
            kumBlock.innerHTML = kumHtml;
        }
```

- [ ] **Step 3: HTML-Container einfügen**

Im HTML-Teil der Detail-Seite, direkt über der Summentabelle, einen Container einfügen:

```html
<div id="kumInfo"></div>
```

- [ ] **Step 4: Browser-Test**

1. http://drive:5002 → Provision → Dashboard → einen Lauf mit Zielprämie öffnen
2. Kumulierungs-Info-Block sollte über der Summentabelle erscheinen
3. Prüfen: Kum. Ziel/IST, Erfüllt/Nicht erfüllt, Monatswerte, Beträge

- [ ] **Step 5: Commit**

```bash
git add api/provision_api.py templates/provision/provision_detail.html
git commit -m "feat(provision): Kumulierungs-Info in Detail-Seite anzeigen"
```

---

### Task 9: PDF — Kumulierungs-Info im Deckblatt

**Files:**
- Modify: `api/provision_pdf.py:174-181` (Zielprämie-Zeile im Deckblatt)

- [ ] **Step 1: kum_daten an PDF-Funktion durchreichen**

In `api/provision_pdf.py`, in der Funktion `_lauf_daten()` oder `generate_provision_pdf()`: Die `kum_daten` müssen berechnet und verfügbar gemacht werden. Nach dem Laden der Lauf-Daten:

```python
    # Kumulierte Zielprämie-Daten
    kum_daten = None
    if lauf.get('abrechnungsmonat') and vkb:
        from api.provision_service import get_provision_config_for_monat, get_kumulierte_zielpraemie_daten
        cfg_i = get_provision_config_for_monat(lauf['abrechnungsmonat']).get('I_neuwagen') or {}
        if cfg_i.get('use_kumuliert') and cfg_i.get('use_zielpraemie'):
            kum_daten = get_kumulierte_zielpraemie_daten(vkb, lauf['abrechnungsmonat'], cfg_i)
```

- [ ] **Step 2: Deckblatt-Zeile erweitern**

Den bestehenden Block (Zeile ~174-181) ersetzen:

```python
    stueck_prov = float(lauf.get('summe_stueckpraemie') or 0)
    if kum_daten:
        # Kumulierte Zielprämie: erweiterte Info
        if kum_daten['kum_erfuellt']:
            ziel_stk = f"Kum. {kum_daten['kum_ist']}/{kum_daten['kum_ziel']} Stk. erfüllt"
            if kum_daten['monats_ueber'] > 0:
                ziel_stk += f" / +{kum_daten['monats_ueber']} Monat"
        else:
            ziel_stk = f"Kum. {kum_daten['kum_ist']}/{kum_daten['kum_ziel']} Stk. nicht erfüllt"
    else:
        if stueck_prov > 0:
            ziel_stk = f'erfüllt / {len(nw)}'
        else:
            ziel_stk = 'nicht erfüllt'
    t, _ = summary_row(ACCENT, 'Ia. Zielprämie NW', ziel_stk, 'Zielprämie', stueck_prov)
    elements.append(t)
    totals.append(stueck_prov)
```

- [ ] **Step 3: Browser-Test — PDF generieren**

1. Im Dashboard einen Lauf auswählen → PDF-Download
2. Deckblatt prüfen: Zeile "Ia. Zielprämie NW" sollte kumulierte Werte zeigen
3. Bei erfülltem Gate: "Kum. 31/30 Stk. erfüllt / +1 Monat"
4. Bei nicht erfülltem Gate: "Kum. 19/20 Stk. nicht erfüllt"

- [ ] **Step 4: Commit**

```bash
git add api/provision_pdf.py
git commit -m "feat(provision): Kumulierungs-Info im PDF-Deckblatt"
```

---

### Task 10: Service neustarten + Integrations-Test

**Files:** Keine Änderungen, nur Test.

- [ ] **Step 1: Service neustarten**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 2: Integrations-Test im Browser**

1. http://drive:5002 → Provision → Config prüfen (Checkbox sichtbar + gespeichert)
2. Live-Preview für Verkäufer öffnen → Kumulierungs-Info prüfen
3. Dashboard → Lauf-Detail → Kumulierungs-Block sichtbar
4. PDF → Kumulierte Werte im Deckblatt

- [ ] **Step 3: Randfall-Test**

Verschiedene Monate testen:
- Januar (kum = monatlich, kein Unterschied)
- Monat wo Gate nicht erreicht → 0€ Stückprämie + "Nicht erfüllt"
- Monat wo Gate erreicht + Übererfüllung → korrekte Beträge

- [ ] **Step 4: Finaler Commit**

```bash
git add -A
git commit -m "feat(provision): Kumulierte Zielprämie komplett (Gate + monatliche Übererfüllung + Detail + PDF)"
```
