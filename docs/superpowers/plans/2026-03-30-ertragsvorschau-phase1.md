# Ertragsvorschau Phase 1 (MVP) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the "Umsatz- und Ertragsvorschau" module — a dashboard + data layer that consolidates FIBU, sales, workshop, financing, and annual report data for business outlook reporting.

**Architecture:** Central data layer (`ertragsvorschau_data.py`) as SSOT, fed by a daily Celery sync from Locosoft FIBU and a PDF importer for annual reports. Dashboard consumes data via REST API. Follows existing DRIVE 3-layer pattern (data → api → routes/templates).

**Tech Stack:** Flask + Blueprint, PostgreSQL, Celery + Redis, pdfplumber, Bootstrap 5.3, Chart.js, ReportLab (Phase 2)

**Spec:** `docs/superpowers/specs/2026-03-30-ertragsvorschau-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `migrations/add_ertragsvorschau_tables.sql` | DDL for 3 tables + navigation + feature access |
| Create | `scripts/sync/sync_fibu_guv.py` | Celery task: Locosoft GuV → Portal |
| Create | `api/jahresabschluss_import.py` | PDF parser for Steuerberater annual reports |
| Create | `api/ertragsvorschau_data.py` | SSOT data layer (all get_* functions) |
| Create | `api/ertragsvorschau_api.py` | REST endpoints |
| Create | `routes/ertragsvorschau_routes.py` | Dashboard HTML views + admin |
| Create | `templates/controlling/ertragsvorschau_dashboard.html` | Dashboard UI |
| Create | `templates/controlling/ertragsvorschau_admin.html` | JA import admin UI |
| Modify | `app.py` | Register blueprints |
| Modify | `celery_app/__init__.py` | Add sync_fibu_guv to beat schedule |
| Modify | `celery_app/tasks.py` | Add sync_fibu_guv task wrapper |
| Modify | `config/roles_config.py` | Add ertragsvorschau feature |

---

## Task 1: Database Migration

**Files:**
- Create: `migrations/add_ertragsvorschau_tables.sql`

- [ ] **Step 1: Write the migration SQL**

Create file `migrations/add_ertragsvorschau_tables.sql`:

```sql
-- Migration: Ertragsvorschau-Modul (Umsatz- und Ertragsvorschau)
-- Erstellt: 2026-03-30 | Workstream: Controlling
-- Tabellen: fibu_guv_monatswerte, jahresabschluss_daten, ertragsvorschau_snapshots
-- Navigation: Ertragsvorschau unter Controlling
-- Feature: ertragsvorschau (geschaeftsleitung, admin)

-- ============================================================================
-- 1. FIBU GuV Monatswerte (täglicher Sync aus Locosoft)
-- ============================================================================
CREATE TABLE IF NOT EXISTS fibu_guv_monatswerte (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL,
    monat INT NOT NULL,
    bereich VARCHAR(50) NOT NULL,
    betrag_cent BIGINT NOT NULL DEFAULT 0,
    synced_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(geschaeftsjahr, monat, bereich)
);

CREATE INDEX IF NOT EXISTS idx_fibu_guv_gj ON fibu_guv_monatswerte(geschaeftsjahr);
CREATE INDEX IF NOT EXISTS idx_fibu_guv_gj_monat ON fibu_guv_monatswerte(geschaeftsjahr, monat);

-- ============================================================================
-- 2. Jahresabschluss-Daten (aus Steuerberater-PDF importiert)
-- ============================================================================
CREATE TABLE IF NOT EXISTS jahresabschluss_daten (
    id SERIAL PRIMARY KEY,
    geschaeftsjahr VARCHAR(10) NOT NULL UNIQUE,
    stichtag DATE NOT NULL,
    bilanzsumme NUMERIC(12,1),
    anlagevermoegen NUMERIC(12,1),
    umlaufvermoegen NUMERIC(12,1),
    eigenkapital NUMERIC(12,1),
    ek_quote NUMERIC(5,1),
    rueckstellungen NUMERIC(12,1),
    verbindlichkeiten NUMERIC(12,1),
    umsatz NUMERIC(12,1),
    rohertrag_pct NUMERIC(5,1),
    personalaufwand NUMERIC(12,1),
    abschreibungen NUMERIC(12,1),
    investitionen NUMERIC(12,1),
    zinsergebnis NUMERIC(12,1),
    betriebsergebnis NUMERIC(12,1),
    finanzergebnis NUMERIC(12,1),
    neutrales_ergebnis NUMERIC(12,1),
    jahresergebnis NUMERIC(12,1),
    cashflow_geschaeft NUMERIC(12,1),
    cashflow_invest NUMERIC(12,1),
    cashflow_finanz NUMERIC(12,1),
    finanzmittel_jahresende NUMERIC(12,1),
    quelldatei TEXT,
    importiert_am TIMESTAMP DEFAULT NOW(),
    importiert_von TEXT
);

-- ============================================================================
-- 3. Ertragsvorschau Snapshots (monatliche Sicherung)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ertragsvorschau_snapshots (
    id SERIAL PRIMARY KEY,
    stichtag DATE NOT NULL,
    geschaeftsjahr VARCHAR(10) NOT NULL,
    daten_json JSONB NOT NULL,
    erstellt_am TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ev_snapshots_gj ON ertragsvorschau_snapshots(geschaeftsjahr);

-- ============================================================================
-- 4. Feature-Zugriff
-- ============================================================================
INSERT INTO feature_access (feature_name, role_name)
SELECT 'ertragsvorschau', r.role_name
FROM (VALUES ('admin'), ('geschaeftsleitung')) AS r(role_name)
WHERE NOT EXISTS (
    SELECT 1 FROM feature_access fa
    WHERE fa.feature_name = 'ertragsvorschau' AND fa.role_name = r.role_name
);

-- ============================================================================
-- 5. Navigation: Ertragsvorschau unter Controlling
-- ============================================================================
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, category, active)
SELECT c.id, 'Ertragsvorschau', '/controlling/ertragsvorschau', 'bi-graph-up-arrow', 25, 'ertragsvorschau', 'dropdown', true
FROM navigation_items c
WHERE c.label = 'Controlling' AND c.parent_id IS NULL
AND NOT EXISTS (SELECT 1 FROM navigation_items n WHERE n.parent_id = c.id AND n.label = 'Ertragsvorschau')
LIMIT 1;
```

- [ ] **Step 2: Run migration on dev database**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -f /opt/greiner-test/migrations/add_ertragsvorschau_tables.sql
```

Expected: No errors. Tables created, feature access and navigation inserted.

- [ ] **Step 3: Run migration on production database**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f /opt/greiner-test/migrations/add_ertragsvorschau_tables.sql
```

Expected: No errors.

- [ ] **Step 4: Verify tables exist**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "\dt fibu_guv_monatswerte; \dt jahresabschluss_daten; \dt ertragsvorschau_snapshots;"
```

Expected: All 3 tables listed.

- [ ] **Step 5: Commit**

```bash
git add migrations/add_ertragsvorschau_tables.sql
git commit -m "feat(controlling): add ertragsvorschau tables, navigation, feature access"
```

---

## Task 2: Feature Access in roles_config.py

**Files:**
- Modify: `config/roles_config.py`

- [ ] **Step 1: Add ertragsvorschau feature to FEATURE_ACCESS dict**

In `config/roles_config.py`, add to the `FEATURE_ACCESS` dict in the Controlling section:

```python
    'ertragsvorschau': ['admin', 'geschaeftsleitung'],
```

- [ ] **Step 2: Commit**

```bash
git add config/roles_config.py
git commit -m "feat(controlling): add ertragsvorschau feature access"
```

---

## Task 3: Install pdfplumber

**Files:** None (system dependency)

- [ ] **Step 1: Install pdfplumber**

```bash
pip install pdfplumber
```

Expected: Successfully installed pdfplumber and dependencies.

- [ ] **Step 2: Verify import works**

```bash
python3 -c "import pdfplumber; print('pdfplumber', pdfplumber.__version__)"
```

Expected: Version printed without error.

---

## Task 4: FIBU GuV Sync Script

**Files:**
- Create: `scripts/sync/sync_fibu_guv.py`

- [ ] **Step 1: Create the sync script**

Create file `scripts/sync/sync_fibu_guv.py`:

```python
#!/usr/bin/env python3
"""
============================================================================
FIBU GuV Sync: Locosoft journal_accountings → Portal fibu_guv_monatswerte
============================================================================
Erstellt: 2026-03-30
Workstream: Controlling / Ertragsvorschau

Synchronisiert monatliche GuV-Daten aus Locosoft (SKR51) ins Portal.
Läuft als Celery-Task täglich 20:15 Mo-Fr (nach Locosoft-Mirror 19:00).

SKR51-Mapping:
  810000-819999: werkstatt_erloese    710000-719999: we_werkstatt
  820000-829999: teile_erloese        720000-729999: we_teile
  830000-839999: sonst_erloese        730000-739999: we_sonstige
  840000-899999: fz_erloese           400000-449999: personal
  450000-493999: sonst_aufwand        230000-242999: zinsen (aufwand+ertrag)
  200000-229999 + 243000-293999: neutral (aufwand+ertrag)
  190000-193999: entnahmen (Bilanzkonten, nicht GuV)

Ausschluss: document_type='A' (Abschluss), Konten 294000-294999/494000-499999 (kalk.)
============================================================================
"""

import sys
import os
import logging
from datetime import datetime, date

sys.path.insert(0, '/opt/greiner-portal')

logger = logging.getLogger('sync_fibu_guv')

# SKR51 Konten-Mapping: Kontenbereich → Bereich-Name
SKR51_BEREICHE = [
    (810000, 819999, 'werkstatt_erloese'),
    (820000, 829999, 'teile_erloese'),
    (830000, 839999, 'sonst_erloese'),
    (840000, 899999, 'fz_erloese'),
    (710000, 719999, 'we_werkstatt'),
    (720000, 729999, 'we_teile'),
    (730000, 739999, 'we_sonstige'),
    (400000, 449999, 'personal'),
    (450000, 493999, 'sonst_aufwand'),
]

# Separate Behandlung für Zinsen (Aufwand vs. Ertrag) und Neutral
ZINSEN_RANGE = (230000, 242999)
NEUTRAL_RANGES = [(200000, 229999), (243000, 293999)]
ENTNAHMEN_RANGE = (190000, 193999)

# Ausschluss
KALK_RANGES = [(294000, 294999), (494000, 499999)]
EXCLUDE_DOC_TYPE = 'A'


def get_geschaeftsjahr(jahr: int, monat: int) -> str:
    """Bestimmt das Geschäftsjahr (Sep-Aug) für ein Datum.

    Monat >= 9: GJ startet in diesem Jahr (z.B. Sep 2025 → '2025/26')
    Monat <= 8: GJ startete im Vorjahr (z.B. Mär 2026 → '2025/26')
    """
    if monat >= 9:
        return f"{jahr}/{str(jahr + 1)[-2:]}"
    else:
        return f"{jahr - 1}/{str(jahr)[-2:]}"


def _bereich_fuer_konto(konto: int, debit_or_credit: str) -> str:
    """Ordnet ein Sachkonto dem passenden Bereich zu.

    Returns: Bereich-Name oder None wenn Konto ausgeschlossen wird.
    """
    # Kalkulatorische Verrechnungen ausschließen
    for kalk_min, kalk_max in KALK_RANGES:
        if kalk_min <= konto <= kalk_max:
            return None

    # Standard-Bereiche
    for konto_min, konto_max, bereich in SKR51_BEREICHE:
        if konto_min <= konto <= konto_max:
            return bereich

    # Zinsen: Aufwand vs. Ertrag trennen
    if ZINSEN_RANGE[0] <= konto <= ZINSEN_RANGE[1]:
        return 'zinsen_ertrag' if debit_or_credit == 'H' else 'zinsen_aufwand'

    # Neutrales Ergebnis
    for n_min, n_max in NEUTRAL_RANGES:
        if n_min <= konto <= n_max:
            return 'neutral_ertrag' if debit_or_credit == 'H' else 'neutral_aufwand'

    # Entnahmen (Bilanzkonten 190-193)
    if ENTNAHMEN_RANGE[0] <= konto <= ENTNAHMEN_RANGE[1]:
        return 'entnahmen'

    return None


def sync_fibu_guv():
    """Hauptfunktion: Synchronisiert GuV-Daten aus Locosoft ins Portal."""
    from api.db_utils import db_session, get_locosoft_connection

    logger.info("=== FIBU GuV Sync gestartet ===")
    start_time = datetime.now()

    # Aktuelles und Vorjahres-GJ bestimmen
    heute = date.today()
    aktuelles_gj = get_geschaeftsjahr(heute.year, heute.month)
    if heute.month >= 9:
        vj_start = heute.year - 1
    else:
        vj_start = heute.year - 2
    vorjahres_gj = f"{vj_start}/{str(vj_start + 1)[-2:]}"

    geschaeftsjahre = [aktuelles_gj, vorjahres_gj]
    logger.info(f"Synchronisiere GJs: {geschaeftsjahre}")

    # Locosoft-Verbindung
    loco_conn = get_locosoft_connection()
    if not loco_conn:
        logger.error("Keine Verbindung zu Locosoft möglich")
        return {'error': 'Locosoft nicht erreichbar'}

    gesamt_zeilen = 0

    try:
        loco_cursor = loco_conn.cursor()

        for gj in geschaeftsjahre:
            # GJ-Zeitraum berechnen
            teile = gj.split('/')
            start_jahr = int(teile[0])
            ende_jahr = start_jahr + 1
            gj_start = f"{start_jahr}-09-01"
            gj_ende = f"{ende_jahr}-08-31"

            logger.info(f"Query Locosoft für GJ {gj} ({gj_start} bis {gj_ende})")

            # Alle GuV-Buchungen + Entnahmen für dieses GJ
            sql = """
                SELECT
                    EXTRACT(YEAR FROM j.accounting_date)::int AS jahr,
                    EXTRACT(MONTH FROM j.accounting_date)::int AS monat,
                    j.nominal_account_number AS konto,
                    j.debit_or_credit,
                    SUM(j.posted_value) AS summe_cent
                FROM journal_accountings j
                LEFT JOIN nominal_accounts n
                    ON j.nominal_account_number = n.nominal_account_number
                    AND n.subsidiary_to_company_ref = 1
                WHERE j.accounting_date >= %s
                  AND j.accounting_date <= %s
                  AND j.document_type != %s
                  AND (
                      (n.is_profit_loss_account = 'J')
                      OR (j.nominal_account_number >= 190000 AND j.nominal_account_number <= 193999)
                  )
                GROUP BY 1, 2, 3, 4
                ORDER BY 1, 2, 3
            """

            loco_cursor.execute(sql, (gj_start, gj_ende, EXCLUDE_DOC_TYPE))
            rows = loco_cursor.fetchall()
            logger.info(f"  {len(rows)} aggregierte Zeilen aus Locosoft")

            # Aggregieren nach (GJ, Monat, Bereich)
            aggregiert = {}
            for row in rows:
                jahr, monat, konto, dc, summe_cent = row

                bereich = _bereich_fuer_konto(konto, dc)
                if bereich is None:
                    continue

                # Vorzeichen: Haben = positiv, Soll = negativ
                betrag = summe_cent if dc == 'H' else -summe_cent

                key = (gj, monat, bereich)
                aggregiert[key] = aggregiert.get(key, 0) + betrag

            logger.info(f"  {len(aggregiert)} Bereich-Monat-Kombinationen")

            # UPSERT ins Portal
            with db_session() as portal_conn:
                portal_cursor = portal_conn.cursor()

                for (gj_key, monat, bereich), betrag_cent in aggregiert.items():
                    portal_cursor.execute("""
                        INSERT INTO fibu_guv_monatswerte (geschaeftsjahr, monat, bereich, betrag_cent, synced_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (geschaeftsjahr, monat, bereich)
                        DO UPDATE SET betrag_cent = EXCLUDED.betrag_cent, synced_at = NOW()
                    """, (gj_key, monat, bereich, betrag_cent))

                portal_conn.commit()
                gesamt_zeilen += len(aggregiert)

    finally:
        loco_conn.close()

    dauer = (datetime.now() - start_time).total_seconds()
    logger.info(f"=== FIBU GuV Sync abgeschlossen: {gesamt_zeilen} Zeilen in {dauer:.1f}s ===")

    return {'zeilen': gesamt_zeilen, 'dauer_s': dauer, 'geschaeftsjahre': geschaeftsjahre}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
    result = sync_fibu_guv()
    print(f"Ergebnis: {result}")
```

- [ ] **Step 2: Test the sync script manually**

```bash
cd /opt/greiner-test && python3 scripts/sync/sync_fibu_guv.py
```

Expected: Output like `=== FIBU GuV Sync abgeschlossen: X Zeilen in Y.Zs ===`

- [ ] **Step 3: Verify data in database**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "
SELECT geschaeftsjahr, monat, bereich, betrag_cent / 100.0 as euro
FROM fibu_guv_monatswerte
WHERE geschaeftsjahr = '2025/26'
ORDER BY monat, bereich
LIMIT 20;
"
```

Expected: Rows with monthly GuV data per bereich.

- [ ] **Step 4: Commit**

```bash
git add scripts/sync/sync_fibu_guv.py
git commit -m "feat(controlling): add FIBU GuV sync from Locosoft"
```

---

## Task 5: Register Celery Task

**Files:**
- Modify: `celery_app/tasks.py`
- Modify: `celery_app/__init__.py`

- [ ] **Step 1: Add task wrapper in celery_app/tasks.py**

Add at the end of `celery_app/tasks.py`:

```python
@shared_task(soft_time_limit=600, bind=True, max_retries=3)
def sync_fibu_guv(self):
    """Synchronisiert FIBU GuV-Daten aus Locosoft ins Portal.

    Täglich 20:15 Mo-Fr (nach Locosoft-Mirror 19:00).
    Erstellt: 2026-03-30 | Workstream: Controlling / Ertragsvorschau
    """
    try:
        from scripts.sync.sync_fibu_guv import sync_fibu_guv as do_sync
        return do_sync()
    except Exception as exc:
        logger.error(f"sync_fibu_guv fehlgeschlagen: {exc}")
        raise self.retry(exc=exc, countdown=300)
```

- [ ] **Step 2: Add beat schedule entry in celery_app/__init__.py**

Add to the `beat_schedule` dict in `celery_app/__init__.py`:

```python
        'sync-fibu-guv': {
            'task': 'celery_app.tasks.sync_fibu_guv',
            'schedule': crontab(minute=15, hour=20, day_of_week='mon-fri'),
            'options': {'queue': 'controlling'}
        },
```

- [ ] **Step 3: Commit**

```bash
git add celery_app/tasks.py celery_app/__init__.py
git commit -m "feat(controlling): register sync_fibu_guv celery task (daily 20:15)"
```

---

## Task 6: JA-PDF-Import Parser

**Files:**
- Create: `api/jahresabschluss_import.py`

- [ ] **Step 1: Create the PDF parser**

Create file `api/jahresabschluss_import.py`:

```python
"""
Jahresabschluss PDF-Import
===========================
Erstellt: 2026-03-30 | Workstream: Controlling / Ertragsvorschau

Parst RAW-Partner Jahresabschluss-PDFs und importiert Kennzahlen
in die Tabelle jahresabschluss_daten.

Quellpfad: /mnt/buchhaltung/Buchhaltung/Jahresabschlussunterlagen/
           Abschluss {YYYY} {YYYY+1}/Abschlüsse RAW/
           Autohaus Greiner GmbH & Co. KG JA {YYYY+1} signiert.pdf

Schlüsselseiten im PDF:
  - Mehrjahresvergleich (enthält Bilanz + GuV + Cashflow als Tabellen)
  - Ertragslage (detaillierte GuV)
"""

import os
import re
import logging
from datetime import date
from typing import Optional

import pdfplumber

logger = logging.getLogger('jahresabschluss_import')

BUCHHALTUNG_PFAD = '/mnt/buchhaltung/Buchhaltung/Jahresabschlussunterlagen'


def _parse_german_number(text: str) -> Optional[float]:
    """Parst deutsches Zahlenformat: '1.234,5' → 1234.5, '-278,8' → -278.8"""
    if not text or text.strip() in ('', '-', '--', 'Negativ'):
        return None
    text = text.strip()
    negativ = text.startswith('-')
    text = text.lstrip('-').strip()
    # Tausender-Punkte entfernen, Dezimalkomma zu Punkt
    text = text.replace('.', '').replace(',', '.')
    try:
        val = float(text)
        return -val if negativ else val
    except ValueError:
        return None


def _finde_mehrjahresvergleich_seite(pdf) -> Optional[int]:
    """Findet die Seite mit dem Mehrjahresvergleich (enthält 'Bilanzstichtag' + 'Bilanzsumme')."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        if 'Bilanzsumme' in text and 'Eigenkapital' in text and ('Bilanzstichtag' in text or 'Mehrjahresvergleich' in text):
            return i
    return None


def _finde_ertragslage_seite(pdf) -> Optional[int]:
    """Findet die Seite mit der Ertragslage (enthält 'Betriebsergebnis' + 'Umsatzerlöse')."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ''
        if 'Betriebsergebnis' in text and 'Umsatzerlöse' in text and 'Ertragslage' in text:
            return i
    return None


def _extrahiere_mehrjahresvergleich(page) -> dict:
    """Extrahiert Bilanz- und GuV-Kennzahlen aus der Mehrjahresvergleich-Seite.

    Die Seite enthält 2 Tabellen:
    1. Bilanzstichtag-Tabelle: Bilanzsumme, AV, UV, EK, EK-Quote, Rückstellungen, Verbindlichkeiten
    2. Geschäftsjahr-Tabelle: Umsatz, Rohertrag, Personal, AfA, Investitionen, Zinsergebnis, Jahresergebnis, Cashflow

    Wir extrahieren jeweils die aktuellste Spalte (= erstes GJ / erster Stichtag).
    """
    text = page.extract_text() or ''
    lines = text.split('\n')

    result = {}

    # Zeilen-basiertes Parsing (robuster als Tabellen-Extraktion bei diesem Format)
    for line in lines:
        # Zahlen am Zeilenende extrahieren (TEUR-Werte, durch Whitespace getrennt)
        # Format: "Bilanzsumme TEUR 9.472,6 9.522,9 8.722,5 ..."
        # Wir wollen den ersten TEUR-Wert nach dem Label

        parts = line.strip().split()
        if len(parts) < 3:
            continue

        # Bilanz-Kennzahlen
        if line.strip().startswith('Bilanzsumme') and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['bilanzsumme'] = vals[0]
        elif line.strip().startswith('Anlagevermögen') and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['anlagevermoegen'] = vals[0]
        elif line.strip().startswith('Umlaufvermögen') and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['umlaufvermoegen'] = vals[0]
        elif line.strip().startswith('Eigenkapital') and 'TEUR' in line and 'quote' not in line.lower() and 'rentab' not in line.lower():
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['eigenkapital'] = vals[0]
        elif line.strip().startswith('Eigenkapitalquote'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['ek_quote'] = vals[0]
        elif line.strip().startswith('Rückstellungen') and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['rueckstellungen'] = vals[0]
        elif line.strip().startswith('Verbindlichkeiten') and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['verbindlichkeiten'] = vals[0]

        # GuV-Kennzahlen
        elif line.strip().startswith('Umsatz') and 'TEUR' in line and 'rentab' not in line.lower():
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['umsatz'] = vals[0]
        elif line.strip().startswith('Rohertrag'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['rohertrag_pct'] = vals[0]
        elif line.strip().startswith('Personalaufwand'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['personalaufwand'] = vals[0]
        elif line.strip().startswith('Abschreibungen') and 'Anlageverm' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['abschreibungen'] = vals[0]
        elif line.strip().startswith('Investitionen'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['investitionen'] = vals[0]
        elif line.strip().startswith('Zinsergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['zinsergebnis'] = vals[0]
        elif line.strip().startswith('Jahresergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['jahresergebnis'] = vals[0]

        # Cashflow
        elif 'Geschäftstätigkeit' in line and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_geschaeft'] = vals[0]
        elif 'Investitionstätigkeit' in line and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_invest'] = vals[0]
        elif 'Finanzierungstätigkeit' in line and 'TEUR' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['cashflow_finanz'] = vals[0]
        elif 'Finanzmittelbestand am' in line and 'Jahresende' in line:
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['finanzmittel_jahresende'] = vals[0]

    return result


def _extrahiere_ertragslage(page) -> dict:
    """Extrahiert Betriebsergebnis, Finanzergebnis, Neutrales Ergebnis aus Ertragslage-Seite."""
    text = page.extract_text() or ''
    lines = text.split('\n')

    result = {}

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue

        if line.strip().startswith('Betriebsergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['betriebsergebnis'] = vals[0]
        elif line.strip().startswith('Finanzergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['finanzergebnis'] = vals[0]
        elif line.strip().startswith('Neutrales Ergebnis'):
            vals = [_parse_german_number(p) for p in parts if _parse_german_number(p) is not None]
            if vals:
                result['neutrales_ergebnis'] = vals[0]

    return result


def _gj_aus_dateiname(dateiname: str) -> Optional[str]:
    """Extrahiert das Geschäftsjahr aus dem Dateinamen.

    'Autohaus Greiner GmbH & Co. KG JA 2025 signiert.pdf' → '2024/25'
    Die Jahreszahl im Dateinamen ist das END-Jahr des GJ.
    """
    match = re.search(r'JA\s+(\d{4})', dateiname)
    if not match:
        return None
    end_jahr = int(match.group(1))
    start_jahr = end_jahr - 1
    return f"{start_jahr}/{str(end_jahr)[-2:]}"


def _stichtag_aus_gj(gj: str) -> date:
    """Berechnet den Bilanzstichtag (31.08.) aus dem GJ.

    '2024/25' → 2025-08-31
    """
    teile = gj.split('/')
    start_jahr = int(teile[0])
    return date(start_jahr + 1, 8, 31)


def import_jahresabschluss(dateipfad: str, importiert_von: str = 'system') -> dict:
    """Importiert einen Jahresabschluss aus einem RAW-Partner PDF.

    Returns: Dict mit importierten Werten + Zusammenfassung.
    """
    if not os.path.exists(dateipfad):
        return {'error': f'Datei nicht gefunden: {dateipfad}'}

    dateiname = os.path.basename(dateipfad)
    gj = _gj_aus_dateiname(dateiname)
    if not gj:
        return {'error': f'Geschäftsjahr nicht aus Dateiname erkennbar: {dateiname}'}

    stichtag = _stichtag_aus_gj(gj)

    logger.info(f"Importiere JA {gj} aus {dateiname}")

    with pdfplumber.open(dateipfad) as pdf:
        # Mehrjahresvergleich finden und parsen
        mjv_seite = _finde_mehrjahresvergleich_seite(pdf)
        if mjv_seite is None:
            return {'error': 'Mehrjahresvergleich-Seite nicht gefunden'}

        daten = _extrahiere_mehrjahresvergleich(pdf.pages[mjv_seite])
        logger.info(f"  Mehrjahresvergleich (S. {mjv_seite + 1}): {len(daten)} Werte")

        # Ertragslage finden und parsen
        el_seite = _finde_ertragslage_seite(pdf)
        if el_seite is not None:
            el_daten = _extrahiere_ertragslage(pdf.pages[el_seite])
            daten.update(el_daten)
            logger.info(f"  Ertragslage (S. {el_seite + 1}): {len(el_daten)} Werte")

    if not daten:
        return {'error': 'Keine Werte aus PDF extrahiert'}

    # In DB speichern
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()

        # UPSERT
        felder = ['geschaeftsjahr', 'stichtag', 'quelldatei', 'importiert_von']
        werte = [gj, stichtag, dateiname, importiert_von]

        db_felder = [
            'bilanzsumme', 'anlagevermoegen', 'umlaufvermoegen', 'eigenkapital',
            'ek_quote', 'rueckstellungen', 'verbindlichkeiten', 'umsatz',
            'rohertrag_pct', 'personalaufwand', 'abschreibungen', 'investitionen',
            'zinsergebnis', 'betriebsergebnis', 'finanzergebnis', 'neutrales_ergebnis',
            'jahresergebnis', 'cashflow_geschaeft', 'cashflow_invest', 'cashflow_finanz',
            'finanzmittel_jahresende'
        ]

        for feld in db_felder:
            felder.append(feld)
            werte.append(daten.get(feld))

        placeholders = ', '.join(['%s'] * len(felder))
        spalten = ', '.join(felder)
        update_clause = ', '.join([f"{f} = EXCLUDED.{f}" for f in felder if f != 'geschaeftsjahr'])

        sql = f"""
            INSERT INTO jahresabschluss_daten ({spalten})
            VALUES ({placeholders})
            ON CONFLICT (geschaeftsjahr) DO UPDATE SET {update_clause}, importiert_am = NOW()
        """

        cursor.execute(sql, werte)
        conn.commit()

    zusammenfassung = {
        'geschaeftsjahr': gj,
        'stichtag': str(stichtag),
        'quelldatei': dateiname,
        'werte': daten,
        'anzahl_werte': len(daten)
    }

    logger.info(f"  JA {gj} importiert: {len(daten)} Werte (EK: {daten.get('eigenkapital')} TEUR, Ergebnis: {daten.get('jahresergebnis')} TEUR)")

    return zusammenfassung


def get_verfuegbare_jahresabschluesse() -> list:
    """Listet alle verfügbaren JA-PDFs mit Import-Status."""
    from api.db_utils import db_session

    ergebnis = []

    if not os.path.exists(BUCHHALTUNG_PFAD):
        return ergebnis

    # Alle Abschluss-Verzeichnisse scannen
    for ordner in sorted(os.listdir(BUCHHALTUNG_PFAD)):
        if not ordner.startswith('Abschluss '):
            continue

        raw_pfad = os.path.join(BUCHHALTUNG_PFAD, ordner, 'Abschlüsse RAW')
        if not os.path.exists(raw_pfad):
            continue

        for datei in os.listdir(raw_pfad):
            if not datei.startswith('Autohaus Greiner') or not datei.endswith('.pdf'):
                continue
            if 'JA' not in datei:
                continue

            gj = _gj_aus_dateiname(datei)
            if not gj:
                continue

            vollpfad = os.path.join(raw_pfad, datei)

            ergebnis.append({
                'geschaeftsjahr': gj,
                'dateiname': datei,
                'pfad': vollpfad,
                'importiert': False,
                'importiert_am': None
            })

    # Import-Status aus DB prüfen
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT geschaeftsjahr, importiert_am FROM jahresabschluss_daten")
        importiert = {row[0]: row[1] for row in cursor.fetchall()}

    for eintrag in ergebnis:
        if eintrag['geschaeftsjahr'] in importiert:
            eintrag['importiert'] = True
            eintrag['importiert_am'] = str(importiert[eintrag['geschaeftsjahr']])

    return sorted(ergebnis, key=lambda x: x['geschaeftsjahr'], reverse=True)


def import_alle_jahresabschluesse(importiert_von: str = 'system') -> list:
    """Importiert alle noch nicht importierten JAs."""
    verfuegbar = get_verfuegbare_jahresabschluesse()
    ergebnisse = []

    for ja in verfuegbar:
        if not ja['importiert']:
            result = import_jahresabschluss(ja['pfad'], importiert_von)
            ergebnisse.append(result)

    return ergebnisse


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    print("Verfügbare JAs:")
    for ja in get_verfuegbare_jahresabschluesse():
        status = "✅ importiert" if ja['importiert'] else "❌ nicht importiert"
        print(f"  {ja['geschaeftsjahr']}: {status} — {ja['dateiname']}")

    print("\nImportiere alle...")
    results = import_alle_jahresabschluesse()
    for r in results:
        if 'error' in r:
            print(f"  ❌ {r['error']}")
        else:
            print(f"  ✅ {r['geschaeftsjahr']}: {r['anzahl_werte']} Werte")
```

- [ ] **Step 2: Test the parser**

```bash
cd /opt/greiner-test && python3 api/jahresabschluss_import.py
```

Expected: Lists available JAs and imports them. Should show EK and Jahresergebnis values.

- [ ] **Step 3: Verify imported data**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "
SELECT geschaeftsjahr, eigenkapital, umsatz, jahresergebnis, ek_quote
FROM jahresabschluss_daten ORDER BY geschaeftsjahr;
"
```

Expected: Rows for each imported GJ with correct values (e.g. GJ 2024/25: EK 775.8, Umsatz 18639.8, Ergebnis -193.2).

- [ ] **Step 4: Commit**

```bash
git add api/jahresabschluss_import.py
git commit -m "feat(controlling): add JA PDF parser for RAW-Partner annual reports"
```

---

## Task 7: Data Layer (SSOT)

**Files:**
- Create: `api/ertragsvorschau_data.py`

This is the largest task. The file contains all `get_*` functions that both the dashboard and the future PDF report will use.

- [ ] **Step 1: Create the data layer**

Create file `api/ertragsvorschau_data.py`:

```python
"""
Ertragsvorschau Data Layer (SSOT)
==================================
Erstellt: 2026-03-30 | Workstream: Controlling

Zentrale Datenquelle für Dashboard und Bank-Report.
Alle Funktionen liefern fertig aufbereitete Dicts.
"""

import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger('ertragsvorschau_data')


def _aktuelles_gj() -> str:
    """Bestimmt das aktuelle Geschäftsjahr."""
    heute = date.today()
    if heute.month >= 9:
        return f"{heute.year}/{str(heute.year + 1)[-2:]}"
    return f"{heute.year - 1}/{str(heute.year)[-2:]}"


def _vorjahres_gj(gj: str) -> str:
    """Bestimmt das Vorjahres-GJ."""
    start = int(gj.split('/')[0])
    return f"{start - 1}/{str(start)[-2:]}"


def _gj_monate(gj: str) -> list:
    """Liefert die 12 Kalendermonate eines GJ als (jahr, monat)-Tupel.

    '2025/26' → [(2025,9), (2025,10), ..., (2025,12), (2026,1), ..., (2026,8)]
    """
    start = int(gj.split('/')[0])
    monate = []
    for m in range(9, 13):
        monate.append((start, m))
    for m in range(1, 9):
        monate.append((start + 1, m))
    return monate


def _gj_start_ende(gj: str) -> tuple:
    """Liefert Start- und End-Datum eines GJ."""
    start = int(gj.split('/')[0])
    return date(start, 9, 1), date(start + 1, 8, 31)


def get_guv_daten(geschaeftsjahr: str = None) -> dict:
    """Monatliche GuV aus fibu_guv_monatswerte.

    Returns:
        {
            'geschaeftsjahr': '2025/26',
            'monate': [
                {'monat': 9, 'jahr': 2025, 'label': 'Sep 25',
                 'erloese': 123456, 'we': -98765, 'rohertrag': 24691,
                 'personal': -21000, 'sonst_aufwand': -5000,
                 'ebit': -1309, 'zinsen': -1500, 'ebt': -2809,
                 'rohertrag_marge': 20.0},
                ...
            ],
            'kumuliert': { ... gleiche Felder, summiert ... },
            'vj_kumuliert': { ... Vorjahreszeitraum ... },
            'delta_vj': { ... Differenz zum VJ ... }
        }
    """
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    vj = _vorjahres_gj(geschaeftsjahr)

    with db_session() as conn:
        cursor = conn.cursor()

        # Alle Monatswerte für aktuelles + Vorjahres-GJ
        cursor.execute("""
            SELECT geschaeftsjahr, monat, bereich, betrag_cent
            FROM fibu_guv_monatswerte
            WHERE geschaeftsjahr IN (%s, %s)
            ORDER BY geschaeftsjahr, monat, bereich
        """, (geschaeftsjahr, vj))

        rows = cursor.fetchall()

    # Daten strukturieren: {(gj, monat): {bereich: betrag_cent}}
    daten = {}
    for row in rows:
        key = (row[0], row[1])
        if key not in daten:
            daten[key] = {}
        daten[key][row[2]] = row[3]

    def _berechne_monat(monat_daten: dict) -> dict:
        ws = monat_daten.get('werkstatt_erloese', 0)
        te = monat_daten.get('teile_erloese', 0)
        se = monat_daten.get('sonst_erloese', 0)
        fe = monat_daten.get('fz_erloese', 0)
        erloese = ws + te + se + fe

        ww = monat_daten.get('we_werkstatt', 0)
        wt = monat_daten.get('we_teile', 0)
        wso = monat_daten.get('we_sonstige', 0)
        we = ww + wt + wso

        rohertrag = erloese + we  # we ist negativ
        personal = monat_daten.get('personal', 0)
        sonst = monat_daten.get('sonst_aufwand', 0)

        na = monat_daten.get('neutral_aufwand', 0)
        ne = monat_daten.get('neutral_ertrag', 0)

        ebit = rohertrag + personal + sonst + na + ne

        za = monat_daten.get('zinsen_aufwand', 0)
        ze = monat_daten.get('zinsen_ertrag', 0)
        zinsen = za + ze

        ebt = ebit + zinsen

        marge = round(rohertrag / erloese * 100, 1) if erloese else 0

        return {
            'erloese': round(erloese / 100),
            'we': round(we / 100),
            'rohertrag': round(rohertrag / 100),
            'rohertrag_marge': marge,
            'personal': round(personal / 100),
            'sonst_aufwand': round(sonst / 100),
            'ebit': round(ebit / 100),
            'zinsen': round(zinsen / 100),
            'ebt': round(ebt / 100),
            # Detail-Erlöse
            'werkstatt_erloese': round(ws / 100),
            'teile_erloese': round(te / 100),
            'fz_erloese': round(fe / 100),
            'sonst_erloese': round(se / 100),
        }

    # Aktuelle Monate aufbauen
    gj_monate = _gj_monate(geschaeftsjahr)
    monate = []
    monatslabels = ['', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

    for jahr, monat in gj_monate:
        key = (geschaeftsjahr, monat)
        if key in daten:
            m = _berechne_monat(daten[key])
            m['monat'] = monat
            m['jahr'] = jahr
            m['label'] = f"{monatslabels[monat]} {str(jahr)[-2:]}"
            monate.append(m)

    # Kumuliert
    kum_felder = ['erloese', 'we', 'rohertrag', 'personal', 'sonst_aufwand', 'ebit', 'zinsen', 'ebt',
                  'werkstatt_erloese', 'teile_erloese', 'fz_erloese', 'sonst_erloese']
    kumuliert = {f: sum(m.get(f, 0) for m in monate) for f in kum_felder}
    kumuliert['rohertrag_marge'] = round(kumuliert['rohertrag'] / kumuliert['erloese'] * 100, 1) if kumuliert['erloese'] else 0
    kumuliert['anzahl_monate'] = len(monate)

    # Vorjahr gleicher Zeitraum
    bisherige_monate_nummern = [m['monat'] for m in monate]
    vj_monate_data = []
    for jahr, monat in _gj_monate(vj):
        if monat not in bisherige_monate_nummern:
            continue
        key = (vj, monat)
        if key in daten:
            vj_monate_data.append(_berechne_monat(daten[key]))

    vj_kumuliert = {f: sum(m.get(f, 0) for m in vj_monate_data) for f in kum_felder}
    vj_kumuliert['rohertrag_marge'] = round(vj_kumuliert['rohertrag'] / vj_kumuliert['erloese'] * 100, 1) if vj_kumuliert['erloese'] else 0

    # Delta
    delta = {}
    for f in kum_felder:
        delta[f] = kumuliert.get(f, 0) - vj_kumuliert.get(f, 0)
    delta['erloese_pct'] = round(delta['erloese'] / vj_kumuliert['erloese'] * 100, 1) if vj_kumuliert.get('erloese') else 0

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'monate': monate,
        'kumuliert': kumuliert,
        'vj_kumuliert': vj_kumuliert,
        'delta_vj': delta
    }


def get_verkauf_daten(geschaeftsjahr: str = None) -> dict:
    """Fahrzeugverkauf aus Portal sales-Tabelle."""
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    gj_start, gj_ende = _gj_start_ende(geschaeftsjahr)
    vj = _vorjahres_gj(geschaeftsjahr)
    vj_start, vj_ende = _gj_start_ende(vj)

    with db_session() as conn:
        cursor = conn.cursor()

        # Auslieferungen pro Monat
        cursor.execute("""
            SELECT
                EXTRACT(YEAR FROM out_invoice_date)::int AS jahr,
                EXTRACT(MONTH FROM out_invoice_date)::int AS monat,
                COUNT(*) AS stueck,
                SUM(COALESCE(rechnungsbetrag_netto, 0))::bigint AS umsatz_netto,
                SUM(COALESCE(deckungsbeitrag, 0))::bigint AS db,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_invoice_date >= %s AND out_invoice_date <= %s
              AND out_invoice_date IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 2
        """, (gj_start, gj_ende))
        auslieferungen = [dict(zip(['jahr', 'monat', 'stueck', 'umsatz_netto', 'db', 'nw', 'gw'], row)) for row in cursor.fetchall()]

        # Auftragseingang pro Monat
        cursor.execute("""
            SELECT
                EXTRACT(YEAR FROM out_sales_contract_date)::int AS jahr,
                EXTRACT(MONTH FROM out_sales_contract_date)::int AS monat,
                COUNT(*) AS auftraege,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_sales_contract_date >= %s AND out_sales_contract_date <= %s
            GROUP BY 1, 2
            ORDER BY 1, 2
        """, (gj_start, gj_ende))
        auftragseingang = [dict(zip(['jahr', 'monat', 'auftraege', 'nw', 'gw'], row)) for row in cursor.fetchall()]

        # Auftragsbestand (Pipeline)
        cursor.execute("""
            SELECT
                COUNT(*) AS gesamt,
                SUM(CASE WHEN dealer_vehicle_type IN ('N','T') THEN 1 ELSE 0 END) AS nw,
                SUM(CASE WHEN dealer_vehicle_type = 'G' THEN 1 ELSE 0 END) AS gw
            FROM sales
            WHERE out_sales_contract_date IS NOT NULL
              AND out_invoice_date IS NULL
              AND out_sales_contract_date >= %s
        """, (str(gj_start.year - 1) + '-01-01',))
        pipeline_row = cursor.fetchone()
        pipeline = {'gesamt': pipeline_row[0] or 0, 'nw': pipeline_row[1] or 0, 'gw': pipeline_row[2] or 0}

        # VJ Auslieferungen (gleicher Zeitraum)
        bisherige_monate = [a['monat'] for a in auslieferungen]
        if bisherige_monate:
            # Gleiche Monate im VJ
            cursor.execute("""
                SELECT
                    COUNT(*) AS stueck,
                    SUM(COALESCE(rechnungsbetrag_netto, 0))::bigint AS umsatz_netto,
                    SUM(COALESCE(deckungsbeitrag, 0))::bigint AS db
                FROM sales
                WHERE out_invoice_date >= %s AND out_invoice_date <= %s
                  AND out_invoice_date IS NOT NULL
                  AND EXTRACT(MONTH FROM out_invoice_date)::int = ANY(%s)
            """, (vj_start, vj_ende, bisherige_monate))
            vj_row = cursor.fetchone()
            vj_auslieferungen = {'stueck': vj_row[0] or 0, 'umsatz_netto': vj_row[1] or 0, 'db': vj_row[2] or 0}
        else:
            vj_auslieferungen = {'stueck': 0, 'umsatz_netto': 0, 'db': 0}

    # Kumuliert
    kum = {
        'stueck': sum(a['stueck'] for a in auslieferungen),
        'umsatz_netto': sum(a['umsatz_netto'] for a in auslieferungen),
        'db': sum(a['db'] for a in auslieferungen),
        'nw': sum(a['nw'] for a in auslieferungen),
        'gw': sum(a['gw'] for a in auslieferungen),
    }

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'auslieferungen': auslieferungen,
        'auftragseingang': auftragseingang,
        'pipeline': pipeline,
        'kumuliert': kum,
        'vj_kumuliert': vj_auslieferungen,
        'delta_stueck_pct': round((kum['stueck'] - vj_auslieferungen['stueck']) / vj_auslieferungen['stueck'] * 100, 1) if vj_auslieferungen['stueck'] else 0
    }


def get_service_daten(geschaeftsjahr: str = None) -> dict:
    """Werkstatt + Teile: Erlöse/Rohertrag aus FIBU + Aufträge aus Locosoft."""
    from api.db_utils import db_session, get_locosoft_connection

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    vj = _vorjahres_gj(geschaeftsjahr)
    gj_start, gj_ende = _gj_start_ende(geschaeftsjahr)
    vj_start, vj_ende = _gj_start_ende(vj)

    # FIBU-Daten (Erlöse/WE) aus Sync-Tabelle
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT geschaeftsjahr, monat, bereich, betrag_cent
            FROM fibu_guv_monatswerte
            WHERE geschaeftsjahr IN (%s, %s)
              AND bereich IN ('werkstatt_erloese', 'teile_erloese', 'we_werkstatt', 'we_teile')
        """, (geschaeftsjahr, vj))
        fibu_rows = cursor.fetchall()

    # Strukturieren
    fibu = {}
    for row in fibu_rows:
        key = (row[0], row[1])
        if key not in fibu:
            fibu[key] = {}
        fibu[key][row[2]] = row[3]

    # Monate aufbauen
    monate = []
    for jahr, monat in _gj_monate(geschaeftsjahr):
        key = (geschaeftsjahr, monat)
        if key not in fibu:
            continue
        d = fibu[key]
        ws_e = d.get('werkstatt_erloese', 0)
        ws_we = d.get('we_werkstatt', 0)
        te_e = d.get('teile_erloese', 0)
        te_we = d.get('we_teile', 0)

        monate.append({
            'monat': monat, 'jahr': jahr,
            'ws_erloese': round(ws_e / 100),
            'ws_rohertrag': round((ws_e + ws_we) / 100),
            'ws_marge': round((ws_e + ws_we) / ws_e * 100, 1) if ws_e else 0,
            'teile_erloese': round(te_e / 100),
            'teile_rohertrag': round((te_e + te_we) / 100),
            'teile_marge': round((te_e + te_we) / te_e * 100, 1) if te_e else 0,
        })

    # Werkstatt-Aufträge aus Locosoft (live)
    auftraege = []
    try:
        loco_conn = get_locosoft_connection()
        if loco_conn:
            loco_cursor = loco_conn.cursor()
            loco_cursor.execute("""
                SELECT
                    EXTRACT(YEAR FROM order_date)::int AS jahr,
                    EXTRACT(MONTH FROM order_date)::int AS monat,
                    COUNT(DISTINCT number || '-' || subsidiary) AS auftraege
                FROM orders
                WHERE order_date >= %s AND order_date <= %s
                GROUP BY 1, 2
                ORDER BY 1, 2
            """, (gj_start, gj_ende))
            auftraege = [dict(zip(['jahr', 'monat', 'auftraege'], row)) for row in loco_cursor.fetchall()]
            loco_conn.close()
    except Exception as e:
        logger.warning(f"Locosoft-Aufträge nicht abrufbar: {e}")

    # VJ-Kumuliert
    bisherige_monate = [m['monat'] for m in monate]
    vj_ws_e = vj_ws_re = vj_te_e = vj_te_re = 0
    for jahr, monat in _gj_monate(vj):
        if monat not in bisherige_monate:
            continue
        key = (vj, monat)
        if key in fibu:
            d = fibu[key]
            vj_ws_e += d.get('werkstatt_erloese', 0)
            vj_ws_re += d.get('werkstatt_erloese', 0) + d.get('we_werkstatt', 0)
            vj_te_e += d.get('teile_erloese', 0)
            vj_te_re += d.get('teile_erloese', 0) + d.get('we_teile', 0)

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'monate': monate,
        'auftraege': auftraege,
        'kumuliert': {
            'ws_erloese': sum(m['ws_erloese'] for m in monate),
            'ws_rohertrag': sum(m['ws_rohertrag'] for m in monate),
            'teile_erloese': sum(m['teile_erloese'] for m in monate),
            'teile_rohertrag': sum(m['teile_rohertrag'] for m in monate),
            'auftraege': sum(a['auftraege'] for a in auftraege),
        },
        'vj_kumuliert': {
            'ws_erloese': round(vj_ws_e / 100),
            'ws_rohertrag': round(vj_ws_re / 100),
            'teile_erloese': round(vj_te_e / 100),
            'teile_rohertrag': round(vj_te_re / 100),
        }
    }


def get_standzeiten_daten() -> dict:
    """Standzeiten + Finanzierungsvolumen aus fahrzeugfinanzierungen."""
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()

        # Aktive Finanzierungen nach Bank
        cursor.execute("""
            SELECT
                COALESCE(finanzinstitut, import_quelle, 'Unbekannt') AS bank,
                COUNT(*) AS anzahl,
                SUM(COALESCE(aktueller_saldo, 0))::bigint AS saldo,
                AVG(COALESCE(alter_tage, alter_finanzierung_tage, 0))::int AS avg_standzeit,
                SUM(COALESCE(zinsen_gesamt, 0))::bigint AS zinsen
            FROM fahrzeugfinanzierungen
            WHERE aktiv = true
            GROUP BY 1
            ORDER BY 3 DESC
        """)
        nach_bank = [dict(zip(['bank', 'anzahl', 'saldo', 'avg_standzeit', 'zinsen'], row)) for row in cursor.fetchall()]

        # Standzeit-Verteilung
        cursor.execute("""
            SELECT
                CASE
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 30 THEN '0-30'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 60 THEN '31-60'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 90 THEN '61-90'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 180 THEN '91-180'
                    WHEN COALESCE(alter_tage, alter_finanzierung_tage, 0) <= 365 THEN '181-365'
                    ELSE '>365'
                END AS klasse,
                COUNT(*) AS anzahl,
                SUM(COALESCE(aktueller_saldo, 0))::bigint AS saldo
            FROM fahrzeugfinanzierungen
            WHERE aktiv = true
            GROUP BY 1
            ORDER BY MIN(COALESCE(alter_tage, alter_finanzierung_tage, 0))
        """)
        verteilung = [dict(zip(['klasse', 'anzahl', 'saldo'], row)) for row in cursor.fetchall()]

    gesamt_anzahl = sum(b['anzahl'] for b in nach_bank)
    gesamt_saldo = sum(b['saldo'] for b in nach_bank)

    return {
        'nach_bank': nach_bank,
        'verteilung': verteilung,
        'gesamt': {'anzahl': gesamt_anzahl, 'saldo': gesamt_saldo}
    }


def get_eigenkapital_entwicklung(geschaeftsjahr: str = None) -> dict:
    """EK-Entwicklung: Letzter JA + laufendes Ergebnis - Entnahmen."""
    from api.db_utils import db_session

    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    with db_session() as conn:
        cursor = conn.cursor()

        # Letzter JA (Vorjahr)
        vj = _vorjahres_gj(geschaeftsjahr)
        cursor.execute("""
            SELECT eigenkapital, ek_quote, jahresergebnis
            FROM jahresabschluss_daten
            WHERE geschaeftsjahr = %s
        """, (vj,))
        ja_row = cursor.fetchone()

        ek_letzter_ja = ja_row[0] if ja_row else None

        # Laufendes Ergebnis (EBT aus GuV)
        cursor.execute("""
            SELECT SUM(betrag_cent)
            FROM fibu_guv_monatswerte
            WHERE geschaeftsjahr = %s
              AND bereich NOT IN ('entnahmen')
        """, (geschaeftsjahr,))
        ebt_row = cursor.fetchone()
        laufendes_ergebnis = round((ebt_row[0] or 0) / 100) if ebt_row else 0

        # Entnahmen
        cursor.execute("""
            SELECT SUM(betrag_cent)
            FROM fibu_guv_monatswerte
            WHERE geschaeftsjahr = %s AND bereich = 'entnahmen'
        """, (geschaeftsjahr,))
        ent_row = cursor.fetchone()
        entnahmen = round(abs(ent_row[0] or 0) / 100) if ent_row else 0

        # Historische EK-Zeitreihe
        cursor.execute("""
            SELECT geschaeftsjahr, eigenkapital, ek_quote
            FROM jahresabschluss_daten
            ORDER BY geschaeftsjahr
        """)
        zeitreihe = [dict(zip(['geschaeftsjahr', 'eigenkapital', 'ek_quote'], row)) for row in cursor.fetchall()]

    # EK-Schätzung: EK_JA + laufendes_ergebnis - Entnahmen (in TEUR)
    ek_schaetzung = None
    if ek_letzter_ja is not None:
        ek_schaetzung = round(float(ek_letzter_ja) + laufendes_ergebnis / 1000 - entnahmen / 1000, 1)

    return {
        'ek_letzter_ja': float(ek_letzter_ja) if ek_letzter_ja else None,
        'laufendes_ergebnis_eur': laufendes_ergebnis,
        'entnahmen_eur': entnahmen,
        'ek_schaetzung_teur': ek_schaetzung,
        'zeitreihe': zeitreihe,
        'basis_gj': vj
    }


def get_prognose(geschaeftsjahr: str = None) -> dict:
    """Lineare Hochrechnung auf 12 Monate."""
    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    guv = get_guv_daten(geschaeftsjahr)
    verkauf = get_verkauf_daten(geschaeftsjahr)

    anz_monate = guv['kumuliert'].get('anzahl_monate', 0)
    if anz_monate == 0:
        return {'hinweis': 'Noch keine Daten für Hochrechnung'}

    faktor = 12 / anz_monate

    return {
        'methode': 'linear',
        'basis_monate': anz_monate,
        'umsatz_prognose': round(guv['kumuliert']['erloese'] * faktor),
        'ebit_prognose': round(guv['kumuliert']['ebit'] * faktor),
        'ebt_prognose': round(guv['kumuliert']['ebt'] * faktor),
        'fz_stueck_prognose': round(verkauf['kumuliert']['stueck'] * faktor),
    }


def get_mehrjahresvergleich() -> list:
    """Alle importierten Jahresabschlüsse als Zeitreihe."""
    from api.db_utils import db_session

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT geschaeftsjahr, stichtag, bilanzsumme, eigenkapital, ek_quote,
                   umsatz, rohertrag_pct, personalaufwand, abschreibungen,
                   zinsergebnis, betriebsergebnis, jahresergebnis,
                   cashflow_geschaeft, cashflow_invest, cashflow_finanz,
                   finanzmittel_jahresende, verbindlichkeiten, rueckstellungen
            FROM jahresabschluss_daten
            ORDER BY geschaeftsjahr DESC
        """)
        spalten = ['geschaeftsjahr', 'stichtag', 'bilanzsumme', 'eigenkapital', 'ek_quote',
                   'umsatz', 'rohertrag_pct', 'personalaufwand', 'abschreibungen',
                   'zinsergebnis', 'betriebsergebnis', 'jahresergebnis',
                   'cashflow_geschaeft', 'cashflow_invest', 'cashflow_finanz',
                   'finanzmittel_jahresende', 'verbindlichkeiten', 'rueckstellungen']

        return [dict(zip(spalten, row)) for row in cursor.fetchall()]


def get_gesamtbild(geschaeftsjahr: str = None) -> dict:
    """Orchestriert alle Datenquellen zu einem Gesamtpaket (SSOT)."""
    if not geschaeftsjahr:
        geschaeftsjahr = _aktuelles_gj()

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'stichtag': str(date.today()),
        'guv': get_guv_daten(geschaeftsjahr),
        'verkauf': get_verkauf_daten(geschaeftsjahr),
        'service': get_service_daten(geschaeftsjahr),
        'standzeiten': get_standzeiten_daten(),
        'eigenkapital': get_eigenkapital_entwicklung(geschaeftsjahr),
        'prognose': get_prognose(geschaeftsjahr),
        'mehrjahresvergleich': get_mehrjahresvergleich(),
    }
```

- [ ] **Step 2: Test the data layer**

```bash
cd /opt/greiner-test && python3 -c "
from api.ertragsvorschau_data import get_gesamtbild
import json
data = get_gesamtbild('2025/26')
print('GuV Monate:', len(data['guv']['monate']))
print('Verkauf Auslieferungen:', len(data['verkauf']['auslieferungen']))
print('Service Monate:', len(data['service']['monate']))
print('Standzeiten Banken:', len(data['standzeiten']['nach_bank']))
print('EK letzter JA:', data['eigenkapital']['ek_letzter_ja'])
print('Mehrjahresvergleich:', len(data['mehrjahresvergleich']))
print('Prognose Umsatz:', data['prognose'].get('umsatz_prognose'))
"
```

Expected: All sections populated with data counts > 0.

- [ ] **Step 3: Commit**

```bash
git add api/ertragsvorschau_data.py
git commit -m "feat(controlling): add ertragsvorschau data layer (SSOT)"
```

---

## Task 8: REST API

**Files:**
- Create: `api/ertragsvorschau_api.py`

- [ ] **Step 1: Create the API blueprint**

Create file `api/ertragsvorschau_api.py`:

```python
"""
Ertragsvorschau REST-API
=========================
Erstellt: 2026-03-30 | Workstream: Controlling
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

ertragsvorschau_api = Blueprint('ertragsvorschau_api', __name__, url_prefix='/api/ertragsvorschau')


def _check_access():
    """Prüft ob User Zugriff auf Ertragsvorschau hat."""
    if not current_user.is_authenticated:
        return False
    return hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')


@ertragsvorschau_api.route('/gesamtbild')
@login_required
def api_gesamtbild():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_gesamtbild
    gj = request.args.get('gj')
    return jsonify(get_gesamtbild(gj))


@ertragsvorschau_api.route('/guv')
@login_required
def api_guv():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_guv_daten
    gj = request.args.get('gj')
    return jsonify(get_guv_daten(gj))


@ertragsvorschau_api.route('/verkauf')
@login_required
def api_verkauf():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_verkauf_daten
    gj = request.args.get('gj')
    return jsonify(get_verkauf_daten(gj))


@ertragsvorschau_api.route('/service')
@login_required
def api_service():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_service_daten
    gj = request.args.get('gj')
    return jsonify(get_service_daten(gj))


@ertragsvorschau_api.route('/standzeiten')
@login_required
def api_standzeiten():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_standzeiten_daten
    return jsonify(get_standzeiten_daten())


@ertragsvorschau_api.route('/eigenkapital')
@login_required
def api_eigenkapital():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_eigenkapital_entwicklung
    gj = request.args.get('gj')
    return jsonify(get_eigenkapital_entwicklung(gj))


@ertragsvorschau_api.route('/mehrjahresvergleich')
@login_required
def api_mehrjahresvergleich():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_mehrjahresvergleich
    return jsonify(get_mehrjahresvergleich())


@ertragsvorschau_api.route('/prognose')
@login_required
def api_prognose():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_prognose
    gj = request.args.get('gj')
    return jsonify(get_prognose(gj))


@ertragsvorschau_api.route('/jahresabschluss/verfuegbar')
@login_required
def api_ja_verfuegbar():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import get_verfuegbare_jahresabschluesse
    return jsonify(get_verfuegbare_jahresabschluesse())


@ertragsvorschau_api.route('/jahresabschluss/import', methods=['POST'])
@login_required
def api_ja_import():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import import_jahresabschluss

    pfad = request.json.get('pfad')
    if not pfad:
        return jsonify({'error': 'Pfad fehlt'}), 400

    user = getattr(current_user, 'username', 'unknown')
    result = import_jahresabschluss(pfad, importiert_von=user)

    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@ertragsvorschau_api.route('/jahresabschluss/import-alle', methods=['POST'])
@login_required
def api_ja_import_alle():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import import_alle_jahresabschluesse

    user = getattr(current_user, 'username', 'unknown')
    results = import_alle_jahresabschluesse(importiert_von=user)
    return jsonify(results)
```

- [ ] **Step 2: Commit**

```bash
git add api/ertragsvorschau_api.py
git commit -m "feat(controlling): add ertragsvorschau REST API"
```

---

## Task 9: Routes + Dashboard Template

**Files:**
- Create: `routes/ertragsvorschau_routes.py`
- Create: `templates/controlling/ertragsvorschau_dashboard.html`
- Create: `templates/controlling/ertragsvorschau_admin.html`

This task creates the frontend. The dashboard loads data via AJAX from the API endpoints.

- [ ] **Step 1: Create routes**

Create file `routes/ertragsvorschau_routes.py`:

```python
"""
Ertragsvorschau Routes — Dashboard + Admin
============================================
Erstellt: 2026-03-30 | Workstream: Controlling
"""

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

ertragsvorschau_bp = Blueprint('ertragsvorschau', __name__, url_prefix='/controlling/ertragsvorschau')


@ertragsvorschau_bp.route('/')
@login_required
def dashboard():
    """Ertragsvorschau Dashboard."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')):
        abort(403)
    return render_template('controlling/ertragsvorschau_dashboard.html')


@ertragsvorschau_bp.route('/admin')
@login_required
def admin():
    """JA-Import Admin."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')):
        abort(403)
    return render_template('controlling/ertragsvorschau_admin.html')
```

- [ ] **Step 2: Create dashboard template**

Create file `templates/controlling/ertragsvorschau_dashboard.html`. This is a large template — the agent implementing this task should create it with:
- Extends `base.html`
- GJ-Dropdown selector in header
- 5 KPI cards (Umsatz, EBIT, EK, Fz-Auslieferungen, Auftragsbestand)
- 7 collapsible sections (GuV, Verkauf, Service, Standzeiten, EK, Mehrjahr, Prognose)
- Chart.js charts for Verkauf (bar chart NW/GW), EK (bar chart), GuV (line chart EBIT trend)
- AJAX calls to `/api/ertragsvorschau/gesamtbild?gj=...` on load and GJ change
- Format helpers: `fmtTeur(val)` for "1.234 T€", `fmtPct(val)` for "12,3%", `fmtDelta(val)` for "+5,4%"
- Color coding: green for positive deltas, red for negative
- Follow existing DRIVE patterns (TEK dashboard style: stat boxes with left-border colors, Bootstrap tables, collapsible cards)

- [ ] **Step 3: Create admin template**

Create file `templates/controlling/ertragsvorschau_admin.html`. Simple admin page with:
- Extends `base.html`
- Table of available JA-PDFs (from `/api/ertragsvorschau/jahresabschluss/verfuegbar`)
- Import button per row, "Alle importieren" button
- Status display (importiert / nicht importiert, Datum)
- After import: show summary of recognized values

- [ ] **Step 4: Commit**

```bash
git add routes/ertragsvorschau_routes.py templates/controlling/ertragsvorschau_dashboard.html templates/controlling/ertragsvorschau_admin.html
git commit -m "feat(controlling): add ertragsvorschau dashboard + admin templates"
```

---

## Task 10: Wire Blueprints into app.py

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Register both blueprints in app.py**

Add in the Blueprint registration section of `app.py` (near other controlling-related registrations):

```python
# Ertragsvorschau API + Routes (TAG Ertragsvorschau)
try:
    from api.ertragsvorschau_api import ertragsvorschau_api
    app.register_blueprint(ertragsvorschau_api)
    print("✅ Ertragsvorschau API registriert: /api/ertragsvorschau/")
except Exception as e:
    print(f"⚠️  Ertragsvorschau API nicht geladen: {e}")

try:
    from routes.ertragsvorschau_routes import ertragsvorschau_bp
    app.register_blueprint(ertragsvorschau_bp)
    print("✅ Ertragsvorschau Routes registriert: /controlling/ertragsvorschau/")
except Exception as e:
    print(f"⚠️  Ertragsvorschau Routes nicht geladen: {e}")
```

- [ ] **Step 2: Restart dev service**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 3: Test the dashboard loads**

Open `http://drive:5002/controlling/ertragsvorschau` in browser (as admin/GL user).
Expected: Dashboard page renders with KPI cards and sections.

- [ ] **Step 4: Test API endpoint**

```bash
curl -s http://localhost:5002/api/ertragsvorschau/mehrjahresvergleich | python3 -m json.tool | head -20
```

Note: This will return 401/403 without auth. Test in browser while logged in.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat(controlling): wire ertragsvorschau blueprints into app"
```

---

## Task 11: Run Initial JA Import + FIBU Sync

**Files:** None (operational task)

- [ ] **Step 1: Run FIBU sync to populate GuV data**

```bash
cd /opt/greiner-test && python3 scripts/sync/sync_fibu_guv.py
```

Expected: Sync completes with rows for GJ 2025/26 and 2024/25.

- [ ] **Step 2: Run JA import for all available annual reports**

```bash
cd /opt/greiner-test && python3 -c "
from api.jahresabschluss_import import import_alle_jahresabschluesse
results = import_alle_jahresabschluesse()
for r in results:
    if 'error' in r:
        print(f'  ❌ {r[\"error\"]}')
    else:
        print(f'  ✅ {r[\"geschaeftsjahr\"]}: {r[\"anzahl_werte\"]} Werte (EK: {r[\"werte\"].get(\"eigenkapital\")} TEUR)')
"
```

Expected: Multiple GJs imported (2020/21 through 2024/25).

- [ ] **Step 3: Verify dashboard shows data**

Open `http://drive:5002/controlling/ertragsvorschau` — KPI cards should show real values.

- [ ] **Step 4: Run migration + sync on production**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f /opt/greiner-test/migrations/add_ertragsvorschau_tables.sql
cd /opt/greiner-portal && python3 scripts/sync/sync_fibu_guv.py
cd /opt/greiner-portal && python3 -c "from api.jahresabschluss_import import import_alle_jahresabschluesse; import_alle_jahresabschluesse()"
```

- [ ] **Step 5: Final commit with all files**

```bash
git add -A
git commit -m "feat(controlling): ertragsvorschau module Phase 1 complete

- FIBU GuV sync from Locosoft (daily Celery task)
- JA PDF parser for RAW-Partner annual reports
- SSOT data layer (GuV, Verkauf, Service, Standzeiten, EK, Prognose)
- REST API with 8 endpoints
- Dashboard with 7 sections + KPI cards
- Admin UI for JA import
- Navigation + feature access (geschaeftsleitung, admin)"
```

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] `/controlling/ertragsvorschau` loads with real data
- [ ] `/controlling/ertragsvorschau/admin` shows JA-PDFs and import status
- [ ] GJ dropdown switches between fiscal years
- [ ] KPI cards show Umsatz, EBIT, EK, Fz-Stück, Pipeline
- [ ] GuV section shows monthly table with VJ comparison
- [ ] Verkauf section shows deliveries + order intake
- [ ] Service section shows Werkstatt + Teile
- [ ] Standzeiten section shows financing by bank
- [ ] EK section shows historical chart
- [ ] Mehrjahresvergleich shows imported JA data
- [ ] Prognose shows linear forecast
- [ ] Menu item appears under Controlling (only for GL/Admin)
- [ ] Celery task `sync_fibu_guv` is registered in beat schedule
