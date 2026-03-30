"""
Provisionsmodul – SSOT für Berechnungslogik und Rohdaten.

Alle Provisionsberechnungen (Live-Preview, Vorlauf, Scripts) nutzen ausschließlich:
- provision_config (Sätze, Min/Max, J60/J61)
- sales (Rohdaten; Filter: out_invoice_date im Monat, salesman_number = VKB)

Keine doppelte Logik: Scripts wie provisions_berechnung_kraus_jan2026.py sollen
diese Funktionen importieren statt eigene Konstanten zu definieren.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from api.db_utils import db_session, rows_to_list

try:
    from api.verkaeufer_zielplanung_api import get_nw_ziel_verkaeufer_monat
except ImportError:
    get_nw_ziel_verkaeufer_monat = None


# out_sale_type (sales) → Kategorie (Konzept Kap. 4.2; DRIVE: F/L/B aus Locosoft)
TYP_TO_KAT = {
    'F': 'I_neuwagen',   # Neuwagen
    'N': 'I_neuwagen',
    'D': 'I_neuwagen',
    'L': 'II_testwagen', # Testwagen/VFW
    'T': 'II_testwagen',
    'V': 'II_testwagen',
    'B': 'III_gebrauchtwagen',
    'G': 'III_gebrauchtwagen',
}
# Alle anderen → III (wie im Kraus-Script); IV_gw_bestand später über Kennung


def get_provision_config_for_monat(monat: str) -> Dict[str, Dict[str, Any]]:
    """
    Liest die gültige provision_config für den Abrechnungsmonat.
    monat: 'YYYY-MM'
    Returns: { kategorie: { prozentsatz, min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61, ... } }
    """
    with db_session() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                       min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61,
                       COALESCE(gw_bestand_operator_abzug, 'minus') AS gw_bestand_operator_abzug,
                       COALESCE(gw_bestand_operator_komponenten, 'plus') AS gw_bestand_operator_komponenten,
                       COALESCE(use_zielpraemie, false) AS use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel,
                       COALESCE(zielpraemie_basis, 'auslieferung') AS zielpraemie_basis,
                       memo_p1_kategorie
                FROM provision_config
                WHERE gueltig_ab <= %s
                  AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
                ORDER BY kategorie
            """, (monat + '-01', monat + '-01'))
        except Exception:
            cur.execute("""
                SELECT kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                       min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61
                FROM provision_config
                WHERE gueltig_ab <= %s
                  AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
                ORDER BY kategorie
            """, (monat + '-01', monat + '-01'))
        rows = rows_to_list(cur.fetchall())
    by_kategorie = {}
    for r in rows:
        k = r['kategorie']
        by_kategorie[k] = {
            'bezeichnung': r['bezeichnung'],
            'bemessungsgrundlage': r['bemessungsgrundlage'],
            'prozentsatz': float(r['prozentsatz'] or 0),
            'min_betrag': float(r['min_betrag']) if r.get('min_betrag') is not None else None,
            'max_betrag': float(r['max_betrag']) if r.get('max_betrag') is not None else None,
            'stueck_praemie': float(r['stueck_praemie']) if r.get('stueck_praemie') is not None else None,
            'stueck_max': int(r['stueck_max']) if r.get('stueck_max') is not None else None,
            'param_j60': float(r['param_j60']) if r.get('param_j60') is not None else None,
            'param_j61': float(r['param_j61']) if r.get('param_j61') is not None else None,
            'gw_bestand_operator_abzug': (r.get('gw_bestand_operator_abzug') or 'minus').strip().lower() if isinstance(r.get('gw_bestand_operator_abzug'), str) else 'minus',
            'gw_bestand_operator_komponenten': (r.get('gw_bestand_operator_komponenten') or 'plus').strip().lower() if isinstance(r.get('gw_bestand_operator_komponenten'), str) else 'plus',
            'use_zielpraemie': bool(r.get('use_zielpraemie')),
            'zielerreichung_betrag': float(r['zielerreichung_betrag']) if r.get('zielerreichung_betrag') is not None else None,
            'zielpraemie_fallback_ziel': int(r['zielpraemie_fallback_ziel']) if r.get('zielpraemie_fallback_ziel') is not None else None,
            'zielpraemie_basis': (r.get('zielpraemie_basis') or 'auslieferung').strip().lower() if isinstance(r.get('zielpraemie_basis'), str) else 'auslieferung',
            'memo_p1_kategorie': (r.get('memo_p1_kategorie') or '').strip() or None,
        }
    return by_kategorie


def get_sales_for_provision(vkb: int, monat: str) -> List[Dict[str, Any]]:
    """
    Rohdaten aus sales für einen Verkäufer und Monat (SSOT für Provisions-Rohdaten).
    Filter: out_invoice_date im Monat, salesman_number = VKB.
    Keine Redundanz: dieselbe Quelle wie VerkaufData für Auslieferungen, aber
    explizit für Provision (Rechnungsdatum = Abrechnungsmonat).
    """
    year, month = monat.split('-')
    von = f'{year}-{month}-01'
    # bis = erster Tag Folgemonat
    next_month = int(month) % 12 + 1
    next_year = int(year) + (1 if next_month == 1 else 0)
    bis = f'{next_year}-{next_month:02d}-01'

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.vin, s.out_invoice_number, s.out_invoice_date, s.out_sale_type,
                   s.model_description, s.netto_vk_preis, s.deckungsbeitrag,
                   s.first_registration_date,
                   TRIM(BOTH ', ' FROM (COALESCE(TRIM(c.family_name), '') || ', ' || COALESCE(TRIM(c.first_name), ''))) AS kaeufer_name,
                   s.in_buy_salesman_number,
                   -- Einkäufer nur aktive Verkäufer (Verkaufsmannschaft); nicht GL/VKL/Zukauf Autohaus
                   CASE WHEN COALESCE(e2.provision_aktiv, true) = true
                        THEN TRIM(BOTH ' ' FROM COALESCE(TRIM(e2.first_name), '') || ' ' || COALESCE(TRIM(e2.last_name), ''))
                        ELSE NULL END AS einkaeufer_name,
                   COALESCE(e2.provision_aktiv, true) AS einkaeufer_provision_aktiv,
                   s.memo,
                   s.rechnungsbetrag_netto
            FROM sales s
            LEFT JOIN loco_customers_suppliers c ON c.customer_number::text = NULLIF(TRIM(s.buyer_customer_no::text), '')
            LEFT JOIN employees e2 ON e2.locosoft_id = s.in_buy_salesman_number
            WHERE s.out_invoice_date >= %s AND s.out_invoice_date < %s
              AND s.salesman_number = %s
            ORDER BY s.out_sale_type, s.netto_vk_preis DESC NULLS LAST
        """, (von, bis, vkb))
        rows = rows_to_list(cur.fetchall())

    return rows


def get_sales_where_einkaeufer_only(vkb: int, monat: str) -> List[Dict[str, Any]]:
    """
    Verkäufe im Monat, bei denen vkb nur Einkäufer ist (nicht Verkäufer).
    Für DB2 Prov aus Bestand: diese Provision geht an den Einkäufer-Lauf.
    Nur GW (out_sale_type B/G bzw. Gebrauchtwagen), nur aktiver Einkäufer.
    """
    year, month = monat.split('-')
    von = f'{year}-{month}-01'
    next_month = int(month) % 12 + 1
    next_year = int(year) + (1 if next_month == 1 else 0)
    bis = f'{next_year}-{next_month:02d}-01'

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.vin, s.out_invoice_number, s.out_invoice_date, s.out_sale_type,
                   s.model_description, s.netto_vk_preis, s.deckungsbeitrag,
                   TRIM(BOTH ', ' FROM (COALESCE(TRIM(c.family_name), '') || ', ' || COALESCE(TRIM(c.first_name), ''))) AS kaeufer_name,
                   s.in_buy_salesman_number,
                   TRIM(BOTH ' ' FROM COALESCE(TRIM(e2.first_name), '') || ' ' || COALESCE(TRIM(e2.last_name), '')) AS einkaeufer_name,
                   COALESCE(e2.provision_aktiv, true) AS einkaeufer_provision_aktiv
            FROM sales s
            LEFT JOIN loco_customers_suppliers c ON c.customer_number::text = NULLIF(TRIM(s.buyer_customer_no::text), '')
            LEFT JOIN employees e2 ON e2.locosoft_id = s.in_buy_salesman_number
            WHERE s.out_invoice_date >= %s AND s.out_invoice_date < %s
              AND s.in_buy_salesman_number = %s
              AND (s.salesman_number IS NULL OR s.salesman_number != %s)
              AND COALESCE(e2.provision_aktiv, true) = true
              AND s.out_sale_type IN ('B', 'G', 'D', 'T')
            ORDER BY s.out_invoice_date, s.out_invoice_number
        """, (von, bis, vkb, vkb))
        rows = rows_to_list(cur.fetchall())
    return rows


def get_nw_auftragseingang_stueck(vkb: int, monat: str) -> int:
    """
    NW-Auftragseingang (Stück) für Verkäufer und Monat auf Basis Vertragsdatum.
    SSOT-konform zur T-Regel aus Verkauf (T nur bis 1 Jahr nach EZ = NW) inkl. Dedup N→T/V.
    """
    year, month = monat.split('-')
    cfg_i = get_provision_config_for_monat(monat).get('I_neuwagen') or {}
    p1_target = (cfg_i.get('memo_p1_kategorie') or '').strip()
    where_p1 = ""
    if p1_target in ('II_testwagen', 'III_gebrauchtwagen'):
        where_p1 = "AND UPPER(COALESCE(TRIM(s.memo), '')) <> 'P1'"

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT COUNT(*) AS anzahl
            FROM sales s
            WHERE EXTRACT(YEAR FROM s.out_sales_contract_date) = %s
              AND EXTRACT(MONTH FROM s.out_sales_contract_date) = %s
              AND s.salesman_number = %s
              AND (
                    s.dealer_vehicle_type = 'N'
                    OR (
                        s.dealer_vehicle_type IN ('T', 'V')
                        AND (
                            s.first_registration_date IS NULL
                            OR (s.out_sales_contract_date::date - s.first_registration_date) <= 365
                        )
                    )
              )
              AND NOT EXISTS (
                    SELECT 1
                    FROM sales s2
                    WHERE s2.vin = s.vin
                      AND s2.out_sales_contract_date = s.out_sales_contract_date
                      AND s2.dealer_vehicle_type IN ('T', 'V')
                      AND s.dealer_vehicle_type = 'N'
              )
              {where_p1}
        """, (str(year), f"{int(month):02d}", vkb))
        row = cur.fetchone()
    return int((row.get('anzahl') if hasattr(row, 'get') else row[0]) or 0)


def _get_float(r: Dict, key: str) -> float:
    v = r.get(key)
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def calc_neuwagen(db_summe: float, stueck: int, config: Dict[str, Any]) -> float:
    """
    Kat. I: DB × prozentsatz; Stückanteil kommt separat (Zielprämie oder Stückprämie).
    Bei use_zielpraemie: nur DB-Anteil; Stück = Zielprämie (wird in berechne_live_provision gesetzt).
    Sonst: DB + stueck_praemie × min(stueck, stueck_max) (alte Stückprämie).
    """
    pct = config.get('prozentsatz') or 0.12
    if config.get('use_zielpraemie'):
        return db_summe * pct
    praemie = config.get('stueck_praemie') or 50.0
    max_stueck = config.get('stueck_max') or 15
    return (db_summe * pct) + (praemie * min(stueck, max_stueck))


def calc_rg_netto_clamp(netto: float, config: Dict[str, Any]) -> float:
    """Kat. II/III: netto × prozentsatz, geclampt auf min_betrag..max_betrag."""
    pct = config.get('prozentsatz') or 0.01
    mn = config.get('min_betrag')
    mx = config.get('max_betrag')
    raw = netto * pct
    if mn is not None and raw < mn:
        raw = mn
    if mx is not None and raw > mx:
        raw = mx
    return round(raw, 2)


def calc_gw_bestand(db_betrag: float, config: Dict[str, Any]) -> float:
    """
    Kat. IV (GW aus Bestand): DB2 = DB1 minus GW-Umsatzprovision (Anteil) minus Verkaufskostenpauschale;
    Provision = Prozentsatz auf DB2. Operatoren konfigurierbar (provision_config).
    """
    anteil = config.get('param_j60') or 0
    pauschale = config.get('param_j61') or 0
    op_komponenten = (config.get('gw_bestand_operator_komponenten') or 'plus').strip().lower()
    op_abzug = (config.get('gw_bestand_operator_abzug') or 'minus').strip().lower()
    # Abzug = (DB × Anteil) [Operator] Pauschale (Stelle: zwischen Anteil und Pauschale)
    if op_komponenten == 'minus':
        abzug = round((db_betrag * anteil) - pauschale, 2)
    else:
        abzug = round((db_betrag * anteil) + pauschale, 2)
    # DB2 = DB [Operator] Abzug (Stelle: zwischen Deckungsbeitrag und Abzug)
    if op_abzug == 'plus':
        basis = db_betrag + abzug
    else:
        basis = db_betrag - abzug
    if basis <= 0:
        return 0.0
    pct = config.get('prozentsatz') or 0.12
    return round(basis * pct, 2)


def berechne_live_provision(vkb: int, monat: str) -> Dict[str, Any]:
    """
    Live-Berechnung für einen Verkäufer und Monat (kein DB-Write).
    Nutzt ausschließlich get_provision_config_for_monat + get_sales_for_provision
    und die calc_*-Funktionen (SSOT).
    Returns: Struktur für API/Frontend (Summen pro Kategorie, Positionen pro Kategorie).
    """
    config = get_provision_config_for_monat(monat)
    rows = get_sales_for_provision(vkb, monat)

    cfg_i = config.get('I_neuwagen') or {}
    cfg_ii = config.get('II_testwagen') or {}
    cfg_iii = config.get('III_gebrauchtwagen') or {}
    cfg_iv = config.get('IV_gw_bestand') or {}

    summe_i = 0.0
    summe_ii = 0.0
    summe_iii = 0.0
    summe_iv = 0.0
    positionen_i = []
    positionen_ii = []
    positionen_iii = []
    positionen_iv = []

    db_sum_nw = 0.0
    stueck_nw = 0

    for r in rows:
        typ = (r.get('out_sale_type') or '').strip().upper() or None
        kat = TYP_TO_KAT.get(typ, 'III_gebrauchtwagen')
        # VFW/NW älter als 1 Jahr nach EZ → unter GW führen und abrechnen (gleicher Satz, Kategorie III)
        ez = r.get('first_registration_date')
        inv = r.get('out_invoice_date')
        if kat in ('I_neuwagen', 'II_testwagen') and ez is not None and inv is not None:
            try:
                ez_d = ez.date() if isinstance(ez, datetime) else (ez if isinstance(ez, date) else datetime.strptime(str(ez)[:10], '%Y-%m-%d').date())
                inv_d = inv.date() if isinstance(inv, datetime) else (inv if isinstance(inv, date) else datetime.strptime(str(inv)[:10], '%Y-%m-%d').date())
                if (inv_d - ez_d).days > 365:
                    kat = 'III_gebrauchtwagen'
            except (TypeError, ValueError):
                pass
        # Provisionsbasis: Rechnungsnetto (I rg_netto, II/VFW) = Rechnungsbetrag netto (invoices.total_net).
        # Für GW (III): Fahrzeugnetto (netto_vk_preis), da Rechnung Zusätze enthalten kann (z. B. Garantie).
        netto_invoice = _get_float(r, 'rechnungsbetrag_netto') if r.get('rechnungsbetrag_netto') is not None else _get_float(r, 'netto_vk_preis')
        netto_vehicle = _get_float(r, 'netto_vk_preis') if r.get('netto_vk_preis') is not None else netto_invoice
        db = _get_float(r, 'deckungsbeitrag')
        vin = (r.get('vin') or '').strip()
        rg_nr = r.get('out_invoice_number')
        if rg_nr is not None:
            rg_nr = str(rg_nr).strip()
        else:
            rg_nr = ''
        desc = (r.get('model_description') or '')[:50]
        rg_datum = r.get('out_invoice_date')
        if hasattr(rg_datum, 'isoformat'):
            rg_datum = rg_datum.isoformat()[:10]
        else:
            rg_datum = str(rg_datum)[:10] if rg_datum else None

        kaeufer = (r.get('kaeufer_name') or '').strip() or None
        in_buy = r.get('in_buy_salesman_number')
        einkaeufer_aktiv = r.get('einkaeufer_provision_aktiv') is not False
        einkaeufer = (r.get('einkaeufer_name') or '').strip() or (('VKB ' + str(in_buy)) if (in_buy is not None and einkaeufer_aktiv) else None)
        # DB2 Prov aus Bestand (Kat. IV): zusätzlich zur Umsatzprovision, wenn aktueller VKB = Einkäufer (antauschender VB)
        is_einkaeufer_this_vkb = (in_buy == vkb and einkaeufer_aktiv)
        # P1-Handling ist konfigurierbar über provision_config.memo_p1_kategorie.
        memo_p1 = (r.get('memo') or '').strip().upper() == 'P1'
        p1_target = (cfg_i.get('memo_p1_kategorie') or '').strip()
        if kat == 'I_neuwagen' and memo_p1 and p1_target in ('II_testwagen', 'III_gebrauchtwagen'):
            if p1_target == 'III_gebrauchtwagen':
                prov = calc_rg_netto_clamp(netto_vehicle, cfg_iii)
                summe_iii += prov
                positionen_iii.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'rg_netto': netto_vehicle, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })
            else:
                prov = calc_rg_netto_clamp(netto_invoice, cfg_ii)
                summe_ii += prov
                positionen_ii.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'rg_netto': netto_invoice, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })
        elif kat == 'I_neuwagen':
            stueck_nw += 1
            bemessung = (cfg_i.get('bemessungsgrundlage') or 'db').strip().lower()
            if bemessung == 'rg_netto':
                prov = calc_rg_netto_clamp(netto_invoice, cfg_i)
                summe_i += prov
                positionen_i.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'rg_netto': netto_invoice, 'deckungsbeitrag': db, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })
            else:
                db_sum_nw += db
                positionen_i.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'deckungsbeitrag': db, 'provision': None, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })
        elif kat == 'II_testwagen':
            prov = calc_rg_netto_clamp(netto_invoice, cfg_ii)
            summe_ii += prov
            positionen_ii.append({
                'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                'rg_netto': netto_invoice, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
            })
        elif kat == 'III_gebrauchtwagen':
            prov = calc_rg_netto_clamp(netto_vehicle, cfg_iii)
            summe_iii += prov
            positionen_iii.append({
                'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                'rg_netto': netto_vehicle, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
            })
            # DB2 Prov aus Bestand: zusätzlich für Einkäufer (antauschender VB), gleiches Geschäft
            if is_einkaeufer_this_vkb:
                prov_iv = calc_gw_bestand(db, cfg_iv)
                summe_iv += prov_iv
                positionen_iv.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'deckungsbeitrag': db, 'provision': prov_iv, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })
        elif kat == 'IV_gw_bestand':
            prov = calc_gw_bestand(db, cfg_iv)
            summe_iv += prov
            positionen_iv.append({
                'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                'deckungsbeitrag': db, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
            })
        else:
            prov = calc_rg_netto_clamp(netto_vehicle, cfg_iii)
            summe_iii += prov
            positionen_iii.append({
                'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                'rg_netto': netto_vehicle, 'provision': prov, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
            })
            if is_einkaeufer_this_vkb:
                prov_iv = calc_gw_bestand(db, cfg_iv)
                summe_iv += prov_iv
                positionen_iv.append({
                    'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
                    'deckungsbeitrag': db, 'provision': prov_iv, 'fahrzeugart': typ or '', 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
                })

    # DB2 Prov aus Bestand: Verkäufe, bei denen vkb nur Einkäufer ist (Verkäufer ist jemand anderes)
    for r in get_sales_where_einkaeufer_only(vkb, monat):
        vin = (r.get('vin') or '').strip()
        rg_nr = str(r.get('out_invoice_number') or '').strip()
        desc = (r.get('model_description') or '')[:50]
        rg_datum = r.get('out_invoice_date')
        if hasattr(rg_datum, 'isoformat'):
            rg_datum = rg_datum.isoformat()[:10]
        else:
            rg_datum = str(rg_datum)[:10] if rg_datum else None
        kaeufer = (r.get('kaeufer_name') or '').strip() or None
        einkaeufer = (r.get('einkaeufer_name') or '').strip() or ('VKB ' + str(r.get('in_buy_salesman_number')) if r.get('in_buy_salesman_number') is not None else None)
        db = _get_float(r, 'deckungsbeitrag')
        prov_iv = calc_gw_bestand(db, cfg_iv)
        summe_iv += prov_iv
        positionen_iv.append({
            'vin': vin, 'rg_nr': rg_nr, 'modell': desc, 'rg_datum': rg_datum,
            'deckungsbeitrag': db, 'provision': prov_iv, 'fahrzeugart': (r.get('out_sale_type') or ''), 'kaeufer_name': kaeufer, 'einkaeufer_name': einkaeufer,
        })

    bemessung_i = (cfg_i.get('bemessungsgrundlage') or 'db').strip().lower()
    if bemessung_i != 'rg_netto':
        summe_i = calc_neuwagen(db_sum_nw, stueck_nw, cfg_i)
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

    summe_kat_v = 0.0  # Phase 3: aus provision_zusatzleistungen
    positionen_v = []

    # Bei Zielprämie ist summe_i nur DB-Anteil, Stück kommt separat; sonst ist Stück schon in summe_i
    gesamt = summe_i + summe_ii + summe_iii + summe_iv + summe_kat_v
    if cfg_i.get('use_zielpraemie'):
        gesamt += stueck_praemie_anteil

    return {
        'monat': monat,
        'verkaufer_id': vkb,
        'verkaufer_name': get_verkaufer_name(vkb),
        'summe_kat_i': round(summe_i, 2),
        'summe_kat_ii': round(summe_ii, 2),
        'summe_kat_iii': round(summe_iii, 2),
        'summe_kat_iv': round(summe_iv, 2),
        'summe_kat_v': round(summe_kat_v, 2),
        'summe_stueckpraemie': round(stueck_praemie_anteil, 2),
        'summe_gesamt': round(gesamt, 2),
        'positionen_i': positionen_i,
        'positionen_ii': positionen_ii,
        'positionen_iii': positionen_iii,
        'positionen_iv': positionen_iv,
        'positionen_v': positionen_v,
        'stueck_neuwagen': stueck_nw,
        'stueck_neuwagen_zielpraemie_basis': stueck_nw_zielpraemie,
        'config': {
            'I': cfg_i,
            'II': cfg_ii,
            'III': cfg_iii,
            'IV': cfg_iv,
        },
    }


def get_verkaufer_name(vkb: int) -> str:
    """Verkäufer-Anzeigename aus employees (locosoft_id = VKB)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT first_name, last_name FROM employees
            WHERE locosoft_id = %s
            LIMIT 1
        """, (vkb,))
        row = cur.fetchone()
    if row and row.get('first_name') is not None:
        return f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
    return f"Verkäufer {vkb}"


def create_vorlauf(vkb: int, monat: str, erstellt_von: str) -> Dict[str, Any]:
    """
    Erstellt einen Provisions-Vorlauf: provision_laeufe + provision_positionen.
    Nutzt ausschließlich berechne_live_provision (SSOT). Kein doppelter Lauf für (vkb, monat).
    Returns: { 'lauf_id': int, 'error': str | None }
    """
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, status FROM provision_laeufe
            WHERE verkaufer_id = %s AND abrechnungsmonat = %s
        """, (vkb, monat))
        existing = cur.fetchone()
    if existing:
        return {'lauf_id': existing.get('id'), 'error': f'Bereits ein Lauf für Verkäufer {vkb}, Monat {monat} (Status: {existing.get("status")})'}

    result = berechne_live_provision(vkb, monat)
    verkaufer_name = get_verkaufer_name(vkb)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO provision_laeufe (
                verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                summe_stueckpraemie, summe_gesamt,
                vorlauf_am, vorlauf_von
            ) VALUES (%s, %s, %s, 'VORLAUF', %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            RETURNING id
        """, (
            vkb, verkaufer_name, monat,
            result['summe_kat_i'], result['summe_kat_ii'], result['summe_kat_iii'],
            result['summe_kat_iv'], result['summe_kat_v'],
            result['summe_stueckpraemie'], result['summe_gesamt'],
            erstellt_von
        ))
        row = cur.fetchone()
        lauf_id = (row.get('id') if hasattr(row, 'get') else row[0]) if row else None
        if not lauf_id:
            return {'lauf_id': None, 'error': 'Lauf konnte nicht angelegt werden.'}

        cfg_i = result['config'].get('I') or {}
        pct_i = cfg_i.get('prozentsatz') or 0.12
        stueck_nw = result['stueck_neuwagen']

        def insert_pos(kategorie: str, pos: Dict, rg_netto: Optional[float], deckungsbeitrag: Optional[float], provision: float, satz: float):
            bem = (deckungsbeitrag if deckungsbeitrag is not None else rg_netto) or 0
            cur.execute("""
                INSERT INTO provision_positionen (
                    lauf_id, kategorie, vin, modell, fahrzeugart, kaeufer_name, einkaeufer_name,
                    rg_netto, deckungsbeitrag, bemessungsgrundlage, provisionssatz,
                    provision_berechnet, provision_final, locosoft_rg_nr, rg_datum
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lauf_id, kategorie, pos.get('vin'), pos.get('modell'), pos.get('fahrzeugart'), pos.get('kaeufer_name'), pos.get('einkaeufer_name'),
                rg_netto, deckungsbeitrag, bem, satz, provision, provision,
                pos.get('rg_nr'), pos.get('rg_datum') or None
            ))

        bemessung_i = (cfg_i.get('bemessungsgrundlage') or 'db').strip().lower()
        for p in result['positionen_i']:
            if bemessung_i == 'rg_netto':
                # Einzelne NW-Position: bereits aus rg_netto × Satz berechnet (mit Min/Max); Basis = rg_netto
                insert_pos('I_neuwagen', p, p.get('rg_netto'), None, p.get('provision') or 0, pct_i)
            else:
                # Einzelne NW-Position: Anteil DB * Satz (Stückprämie wird auf Lauf-Ebene geführt)
                db_val = p.get('deckungsbeitrag') or 0
                prov_anteil = round(db_val * pct_i, 2) if stueck_nw else 0
                insert_pos('I_neuwagen', p, None, db_val, prov_anteil, pct_i)
        for p in result['positionen_ii']:
            insert_pos('II_testwagen', p, p.get('rg_netto'), None, p['provision'], (result['config'].get('II') or {}).get('prozentsatz') or 0.01)
        for p in result['positionen_iii']:
            insert_pos('III_gebrauchtwagen', p, p.get('rg_netto'), None, p['provision'], (result['config'].get('III') or {}).get('prozentsatz') or 0.01)
        for p in result['positionen_iv']:
            insert_pos('IV_gw_bestand', p, None, p.get('deckungsbeitrag'), p['provision'], (result['config'].get('IV') or {}).get('prozentsatz') or 0.12)

        conn.commit()

    # PDF erstellen (optional; wenn Modul fehlt, lauf_id trotzdem zurückgeben)
    pdf_path = None
    try:
        from api.provision_pdf import generate_provision_pdf
        pdf_path = generate_provision_pdf(lauf_id, typ='vorlauf')
        if pdf_path:
            with db_session() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE provision_laeufe SET pdf_vorlauf = %s WHERE id = %s", (pdf_path, lauf_id))
                conn.commit()
    except Exception:
        pass

    return {'lauf_id': lauf_id, 'error': None, 'pdf_vorlauf': pdf_path}


def get_dashboard_daten(monat: str) -> Dict[str, Any]:
    """Läufe für einen Monat + Verkäufer mit Verkäufen (für Vorlauf-Erstellung)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v, summe_gesamt,
                   vorlauf_am, pdf_vorlauf, endlauf_am, endlauf_von, belegnummer
            FROM provision_laeufe WHERE abrechnungsmonat = %s ORDER BY verkaufer_name
        """, (monat,))
        laeufe = rows_to_list(cur.fetchall())
        # Verkäufer mit Verkäufen in dem Monat (für "Vorlauf erstellen")
        year, month = monat.split('-')
        von = f'{year}-{month}-01'
        next_m = int(month) % 12 + 1
        next_y = int(year) + (1 if next_m == 1 else 0)
        bis = f'{next_y}-{next_m:02d}-01'
        cur.execute("""
            SELECT DISTINCT s.salesman_number,
                   COALESCE(e.first_name || ' ' || e.last_name, 'VKB ' || s.salesman_number) as name
            FROM sales s
            LEFT JOIN employees e ON e.locosoft_id = s.salesman_number
            WHERE s.out_invoice_date >= %s AND s.out_invoice_date < %s AND s.salesman_number IS NOT NULL
              AND (e.id IS NULL OR COALESCE(e.provision_aktiv, true) = true)
            ORDER BY name
        """, (von, bis))
        verkaeufer = rows_to_list(cur.fetchall())
        # KPIs: Fahrzeuge = Anzahl Positionen in allen Läufen des Monats
        cur.execute("""
            SELECT COUNT(*) FROM provision_positionen p
            INNER JOIN provision_laeufe l ON p.lauf_id = l.id
            WHERE l.abrechnungsmonat = %s
        """, (monat,))
        fahrzeuge = (cur.fetchone() or (0,))[0]
    provision_gesamt = sum(float(l.get('summe_gesamt') or 0) for l in laeufe)
    status_upper = lambda s: (s or '').strip().upper()
    abgeschlossen = sum(1 for l in laeufe if status_upper(l.get('status')) == 'ENDLAUF')
    offen = len(laeufe) - abgeschlossen
    kpis = {
        'provision_gesamt': round(provision_gesamt, 2),
        'fahrzeuge': fahrzeuge,
        'abgeschlossen': abgeschlossen,
        'offen': offen,
    }
    return {'laeufe': laeufe, 'verkaeufer': verkaeufer, 'monat': monat, 'kpis': kpis}


def get_lauf_detail(lauf_id: int) -> Optional[Dict[str, Any]]:
    """Ein Lauf inkl. aller Positionen. Fehlende Käufernamen werden aus sales + loco_customers_suppliers nachgeladen."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                   summe_stueckpraemie, summe_gesamt,
                   vorlauf_am, vorlauf_von, pdf_vorlauf, pdf_endlauf,
                   endlauf_am, endlauf_von, belegnummer
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return None
        cur.execute("""
            SELECT id, kategorie, vin, modell, fahrzeugart, kaeufer_name, einkaeufer_name,
                   rg_netto, deckungsbeitrag, bemessungsgrundlage, kosten_abzug,
                   provisionssatz, provision_berechnet, provision_final,
                   locosoft_rg_nr, rg_datum, einspruch_flag, einspruch_text
            FROM provision_positionen WHERE lauf_id = %s
            ORDER BY CASE kategorie
                WHEN 'I_neuwagen' THEN 1 WHEN 'II_testwagen' THEN 2
                WHEN 'III_gebrauchtwagen' THEN 3 WHEN 'IV_gw_bestand' THEN 4 ELSE 5 END,
                provision_final DESC NULLS LAST
        """, (lauf_id,))
        positionen = rows_to_list(cur.fetchall())

    lauf_d = dict(lauf)
    vkb = lauf_d.get('verkaufer_id')
    monat = (lauf_d.get('abrechnungsmonat') or '').strip()
    if vkb and monat and len(monat) == 7 and monat[4] == '-':
        need_names = [p for p in positionen if not (p.get('kaeufer_name') or '').strip()]
        if need_names:
            year, month = monat.split('-')
            von = f'{year}-{month}-01'
            next_m = int(month) % 12 + 1
            next_y = int(year) + (1 if next_m == 1 else 0)
            bis = f'{next_y}-{next_m:02d}-01'
            vins = list({(p.get('vin') or '') for p in need_names})
            with db_session() as conn2:
                cur2 = conn2.cursor()
                cur2.execute("""
                    SELECT s.vin, s.out_invoice_number::text,
                           TRIM(BOTH ', ' FROM (COALESCE(TRIM(c.family_name), '') || ', ' || COALESCE(TRIM(c.first_name), ''))) AS kaeufer_name
                    FROM sales s
                    LEFT JOIN loco_customers_suppliers c ON c.customer_number::text = NULLIF(TRIM(s.buyer_customer_no::text), '')
                    WHERE s.salesman_number = %s AND s.out_invoice_date >= %s AND s.out_invoice_date < %s
                      AND COALESCE(s.vin, '') = ANY(%s)
                """, (vkb, von, bis, vins))
                rows = cur2.fetchall()
            key_to_name = {}
            for r in rows:
                vin = (r[0] or '').strip()
                rg = (r[1] or '').strip()
                name = (r[2] or '').strip() if r[2] else ''
                key_to_name[(vin, rg)] = name or None
            for p in positionen:
                if (p.get('kaeufer_name') or '').strip():
                    continue
                key = ((p.get('vin') or '').strip(), (p.get('locosoft_rg_nr') or '').strip())
                if key in key_to_name:
                    p['kaeufer_name'] = key_to_name[key]

        need_einkaeufer = [p for p in positionen if not (p.get('einkaeufer_name') or '').strip()]
        if need_einkaeufer:
            year, month = monat.split('-')
            von = f'{year}-{month}-01'
            next_m = int(month) % 12 + 1
            next_y = int(year) + (1 if next_m == 1 else 0)
            bis = f'{next_y}-{next_m:02d}-01'
            vins = list({(p.get('vin') or '') for p in need_einkaeufer})
            with db_session() as conn2:
                cur2 = conn2.cursor()
                cur2.execute("""
                    SELECT s.vin, s.out_invoice_number::text, s.in_buy_salesman_number,
                           TRIM(BOTH ' ' FROM COALESCE(TRIM(e.first_name), '') || ' ' || COALESCE(TRIM(e.last_name), '')) AS einkaeufer_name,
                           COALESCE(e.provision_aktiv, true) AS einkaeufer_provision_aktiv
                    FROM sales s
                    LEFT JOIN employees e ON e.locosoft_id = s.in_buy_salesman_number
                    WHERE s.salesman_number = %s AND s.out_invoice_date >= %s AND s.out_invoice_date < %s
                      AND COALESCE(s.vin, '') = ANY(%s)
                """, (vkb, von, bis, vins))
                rows = cur2.fetchall()
            key_to_einkaeufer = {}
            for r in rows:
                vin = (r[0] or '').strip()
                rg = (r[1] or '').strip()
                in_buy = r[2]
                name = (r[3] or '').strip() if r[3] else ''
                aktiv = r[4] is not False
                key_to_einkaeufer[(vin, rg)] = (name or (('VKB ' + str(in_buy)) if in_buy is not None else None)) if aktiv else None
            for p in positionen:
                if (p.get('einkaeufer_name') or '').strip():
                    continue
                key = ((p.get('vin') or '').strip(), (p.get('locosoft_rg_nr') or '').strip())
                if key in key_to_einkaeufer:
                    p['einkaeufer_name'] = key_to_einkaeufer[key]
            # Persistieren: alte Positionen ohne einkaeufer_name in DB nachziehen
            if key_to_einkaeufer:
                with db_session() as conn3:
                    cur3 = conn3.cursor()
                    for p in positionen:
                        ename = p.get('einkaeufer_name')
                        if not (ename or '').strip():
                            continue
                        cur3.execute("""
                            UPDATE provision_positionen SET einkaeufer_name = %s
                            WHERE lauf_id = %s AND vin IS NOT DISTINCT FROM %s AND locosoft_rg_nr IS NOT DISTINCT FROM %s
                        """, (ename, lauf_id, p.get('vin'), p.get('locosoft_rg_nr')))
                    conn3.commit()
    return {'lauf': lauf_d, 'positionen': positionen}


def delete_vorlauf(lauf_id: int) -> Dict[str, Any]:
    """
    Löscht einen Vorlauf (nur Status VORLAUF).
    provision_positionen werden durch ON DELETE CASCADE mit entfernt.
    Returns: {'success': True} oder {'success': False, 'error': '...'}
    """
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM provision_laeufe WHERE id = %s", (lauf_id,))
        row = cur.fetchone()
        if not row:
            return {'success': False, 'error': 'Lauf nicht gefunden.'}
        status = (row.get('status') or '').strip().upper()
        if status != 'VORLAUF':
            return {'success': False, 'error': f'Nur Vorläufe können gelöscht werden (aktueller Status: {status}).'}
        cur.execute("DELETE FROM provision_laeufe WHERE id = %s", (lauf_id,))
        conn.commit()
    return {'success': True}


def get_aktive_verkaeufer() -> List[Dict[str, Any]]:
    """Alle Verkäufer mit provision_aktiv=true für Einkäufer-Dropdown."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT locosoft_id,
                   TRIM(BOTH ' ' FROM COALESCE(TRIM(first_name), '') || ' ' || COALESCE(TRIM(last_name), '')) AS name
            FROM employees
            WHERE COALESCE(provision_aktiv, true) = true
              AND locosoft_id IS NOT NULL
            ORDER BY last_name, first_name
        """)
        return rows_to_list(cur.fetchall())
