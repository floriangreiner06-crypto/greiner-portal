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
  830000-839999: sonst_erloese        730000-809999: we_sonstige (inkl. produktive Löhne, Fremdleistungen, VFW-Aufwand)
  840000-899999: fz_erloese           400000-449999: personal
  450000-499999: sonst_aufwand (inkl. 494-499 Fixum/Kulanz/Provisionen)
  230000-242999: zinsen (aufwand+ertrag)
  200000-229999 + 243000-293999: neutral (aufwand+ertrag)
  190000-193999: entnahmen (Bilanzkonten, nicht GuV)

Ausschluss: document_type='A' (Abschluss), Konten 294000-294999 (kalk. Unternehmerlohn/Miete/Zinsen)
WICHTIG: 494000-499999 werden NICHT ausgeschlossen (Fixum, Kulanz, Provisionen sind echte Kosten)
============================================================================
"""

import sys
import os
import logging
import psycopg2
from datetime import datetime, date

sys.path.insert(0, '/opt/greiner-test')
sys.path.insert(0, '/opt/greiner-portal')

# Portal-Datenbanken (beide werden synchronisiert)
_PORTAL_DBS = [
    {
        'host': '127.0.0.1',
        'port': 5432,
        'dbname': 'drive_portal',
        'user': 'drive_user',
        'password': 'DrivePortal2024',
    },
    {
        'host': '127.0.0.1',
        'port': 5432,
        'dbname': 'drive_portal_dev',
        'user': 'drive_user',
        'password': 'DrivePortal2024',
    },
]

logger = logging.getLogger('sync_fibu_guv')

# SKR51 Konten-Mapping: Kontenbereich → Bereich-Name
SKR51_BEREICHE = [
    (810000, 819999, 'werkstatt_erloese'),
    (820000, 829999, 'teile_erloese'),
    (830000, 839999, 'sonst_erloese'),
    (840000, 899999, 'fz_erloese'),
    (710000, 719999, 'we_werkstatt'),
    (720000, 729999, 'we_teile'),
    (730000, 809999, 'we_sonstige'),  # inkl. 74xxxx produktive Löhne, 76xxxx VFW-Aufwand
    (400000, 449999, 'personal'),
    (450000, 499999, 'sonst_aufwand'),  # inkl. 494-499 Fixum/Kulanz/Provisionen
]

# Separate Behandlung für Zinsen (Aufwand vs. Ertrag) und Neutral
ZINSEN_RANGE = (230000, 242999)
NEUTRAL_RANGES = [(200000, 229999), (243000, 299999)]  # inkl. 294xxx kalk. Verrechnungen (BWA-konform)
ENTNAHMEN_RANGE = (190000, 193999)

# Ausschluss: KEINE — 294xxx wird als neutral_ertrag mitgesynct (BWA zählt sie zum Neutralen Ergebnis)
KALK_RANGES = []
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


def _get_portal_connections():
    """Direkte psycopg2-Verbindungen zu BEIDEN Portal-Datenbanken (Prod + Dev).

    Umgeht load_dotenv-Überschreibung in db_connection.py beim Aufruf als Script.
    Beide DBs werden parallel gehalten weil db_connection.py hardcoded /opt/greiner-portal/.env lädt.
    """
    conns = []
    for db_config in _PORTAL_DBS:
        try:
            conns.append(psycopg2.connect(**db_config))
        except Exception as e:
            logger.warning(f"Kann nicht zu {db_config['dbname']} verbinden: {e}")
    return conns


def sync_fibu_guv():
    """Hauptfunktion: Synchronisiert GuV-Daten aus Locosoft ins Portal."""
    from api.db_utils import get_locosoft_connection

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

    UNTERNEHMEN = [
        (1, 'autohaus'),  # Autohaus Greiner, Opel/Leapmotor
        (2, 'auto'),      # Auto Greiner, Hyundai
    ]

    try:
        loco_cursor = loco_conn.cursor()

        for (subsidiary_id, gesellschaft) in UNTERNEHMEN:
            logger.info(f"--- Synchronisiere Gesellschaft: {gesellschaft} (subsidiary_id={subsidiary_id}) ---")

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
                        AND n.subsidiary_to_company_ref = %s
                    WHERE j.subsidiary_to_company_ref = %s
                      AND j.accounting_date >= %s
                      AND j.accounting_date <= %s
                      AND j.document_type != %s
                      AND (
                          (n.is_profit_loss_account = 'J')
                          OR (j.nominal_account_number >= 190000 AND j.nominal_account_number <= 193999)
                      )
                    GROUP BY 1, 2, 3, 4
                    ORDER BY 1, 2, 3
                """

                loco_cursor.execute(sql, (subsidiary_id, subsidiary_id, gj_start, gj_ende, EXCLUDE_DOC_TYPE))
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

                # UPSERT in BEIDE Portal-DBs (Prod + Dev)
                for portal_conn in _get_portal_connections():
                    try:
                        portal_cursor = portal_conn.cursor()

                        for (gj_key, monat, bereich), betrag_cent in aggregiert.items():
                            portal_cursor.execute("""
                                INSERT INTO fibu_guv_monatswerte (geschaeftsjahr, monat, bereich, betrag_cent, gesellschaft, synced_at)
                                VALUES (%s, %s, %s, %s, %s, NOW())
                                ON CONFLICT (geschaeftsjahr, monat, bereich, gesellschaft)
                                DO UPDATE SET betrag_cent = EXCLUDED.betrag_cent, synced_at = NOW()
                            """, (gj_key, monat, bereich, betrag_cent, gesellschaft))

                        portal_conn.commit()
                    finally:
                        portal_conn.close()
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
