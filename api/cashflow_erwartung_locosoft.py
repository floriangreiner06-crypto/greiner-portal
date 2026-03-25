"""
Erwartete Einnahmen für Liquiditätsvorschau aus Locosoft (Fahrzeug + Werkstatt).
Nur datengetrieben: Aufträge/Rechnungen aus Locosoft, Ablöse aus Portal – keine hochgerechneten Schnitte.

Workstream: Controlling / Liquidität
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional

from api.db_utils import locosoft_session, db_session, rows_to_list, row_to_dict
from api.db_connection import sql_placeholder

logger = logging.getLogger(__name__)

# Zahlungsziel Kunde (Tage nach Rechnungsdatum)
ZAHLUNGSZIEL_TAGE = 14
# Bei Auftrag „noch nicht in Rechnung“: geschätzt Rechnung + Zahlungsziel (Tage nach Vertragsdatum)
AUFTRAG_ERWARTET_TAGE_BIS_ZAHLUNG = 28  # z. B. 14 (Rechnung) + 14 (Zahlung)
# Werkstatt: Zahlungseingang = Rechnungsdatum + Zahlungsziel
WST_ZAHLUNGSZIEL_TAGE = 14


def _vin_norm(vin: Optional[str]) -> str:
    if not vin:
        return ""
    return (vin or "").strip().upper()


def get_erwartete_einnahmen_fahrzeug(
    von_datum: date,
    bis_datum: date,
) -> Dict[str, Dict[str, float]]:
    """
    Erwartete Netto-Einnahmen (VK − Ablöse) pro Tag aus Fahrzeugverkauf (Locosoft + Portal).

    - Rechnungen: out_invoice_date + ZAHLUNGSZIEL_TAGE = erwarteter Zahlungseingang.
    - Aufträge (noch nicht in Rechnung): out_sales_contract_date + AUFTRAG_ERWARTET_TAGE_BIS_ZAHLUNG.
    - Deduplizierung: VIN nur einmal (Priorität Rechnungen).
    - Ablöse aus Portal fahrzeugfinanzierungen (aktiv); Netto = VK − Ablöse.

    Returns:
        dict[datum_iso] = {"netto": float, "einnahmen_vk": float, "abloese": float}
    """
    result: Dict[str, Dict[str, float]] = {}
    try:
        with locosoft_session() as conn:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 1. Rechnungen (Rechnungsdatum im Zeitraum) → Zahlung = rechnungsdatum + 14
            cur.execute("""
                SELECT
                    dv.out_invoice_date AS rechnungsdatum,
                    dv.out_sale_price AS vk_preis_eur,
                    v.vin AS vin
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON v.internal_number = dv.vehicle_number
                    AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                    AND v.dealer_vehicle_number = dv.dealer_vehicle_number
                WHERE dv.out_invoice_date IS NOT NULL
                  AND dv.out_invoice_date >= %s AND dv.out_invoice_date <= %s
            """, (von_datum, bis_datum))
            rechnungen = rows_to_list(cur.fetchall(), cur)
            vins_in_rechnungen = {_vin_norm(r.get("vin")) for r in rechnungen if _vin_norm(r.get("vin"))}

            # 2. Aufträge (noch nicht in Rechnung), ohne VINs die schon in Rechnungen sind
            cur.execute("""
                SELECT
                    dv.out_sales_contract_date AS vertragsdatum,
                    dv.out_sale_price AS vk_preis_eur,
                    v.vin AS vin
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON v.internal_number = dv.vehicle_number
                    AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                    AND v.dealer_vehicle_number = dv.dealer_vehicle_number
                WHERE dv.out_sales_contract_date IS NOT NULL
                  AND dv.out_invoice_date IS NULL
            """)
            auftraege_raw = rows_to_list(cur.fetchall(), cur)
            auftraege = [r for r in auftraege_raw if _vin_norm(r.get("vin")) not in vins_in_rechnungen]

        # 3. Ablöse aus Portal
        all_vins = []
        for r in rechnungen + auftraege:
            v = _vin_norm(r.get("vin"))
            if v:
                all_vins.append(v)
        ablöse_map: Dict[str, float] = {}
        if all_vins:
            with db_session() as drive_conn:
                drive_cur = drive_conn.cursor()
                ph = sql_placeholder()
                placeholders = ",".join([ph for _ in all_vins])
                drive_cur.execute(f"""
                    SELECT TRIM(UPPER(vin)) AS vin, COALESCE(SUM(aktueller_saldo), 0) AS ablöse
                    FROM fahrzeugfinanzierungen
                    WHERE aktiv = true AND TRIM(UPPER(vin)) IN ({placeholders})
                    GROUP BY TRIM(UPPER(vin))
                """, all_vins)
                for row in drive_cur.fetchall():
                    d = row_to_dict(row, drive_cur)
                    ablöse_map[d.get("vin") or ""] = float(d.get("ablöse") or 0)

        # 4. Rechnungen: Zahlungsdatum = rechnungsdatum + ZAHLUNGSZIEL_TAGE
        for r in rechnungen:
            rd = r.get("rechnungsdatum")
            if not rd:
                continue
            if hasattr(rd, "date"):
                rd = rd.date()
            zahlung_am = rd + timedelta(days=ZAHLUNGSZIEL_TAGE)
            if von_datum <= zahlung_am <= bis_datum:
                key = zahlung_am.isoformat()
                vk = float(r.get("vk_preis_eur") or 0)
                vin_n = _vin_norm(r.get("vin"))
                abloese = ablöse_map.get(vin_n, 0.0)
                netto = round(vk - abloese, 2)
                if key not in result:
                    result[key] = {"netto": 0.0, "einnahmen_vk": 0.0, "abloese": 0.0}
                result[key]["netto"] += netto
                result[key]["einnahmen_vk"] += vk
                result[key]["abloese"] += abloese

        # 5. Aufträge: Zahlungsdatum = vertragsdatum + AUFTRAG_ERWARTET_TAGE_BIS_ZAHLUNG
        for r in auftraege:
            vd = r.get("vertragsdatum")
            if not vd:
                continue
            if hasattr(vd, "date"):
                vd = vd.date()
            zahlung_am = vd + timedelta(days=AUFTRAG_ERWARTET_TAGE_BIS_ZAHLUNG)
            if von_datum <= zahlung_am <= bis_datum:
                key = zahlung_am.isoformat()
                vk = float(r.get("vk_preis_eur") or 0)
                vin_n = _vin_norm(r.get("vin"))
                abloese = ablöse_map.get(vin_n, 0.0)
                netto = round(vk - abloese, 2)
                if key not in result:
                    result[key] = {"netto": 0.0, "einnahmen_vk": 0.0, "abloese": 0.0}
                result[key]["netto"] += netto
                result[key]["einnahmen_vk"] += vk
                result[key]["abloese"] += abloese

        for k in result:
            result[k]["netto"] = round(result[k]["netto"], 2)
            result[k]["einnahmen_vk"] = round(result[k]["einnahmen_vk"], 2)
            result[k]["abloese"] = round(result[k]["abloese"], 2)
    except Exception as e:
        logger.warning("get_erwartete_einnahmen_fahrzeug: Locosoft/Portal fehlgeschlagen: %s", e)
    return result


def get_erwartete_einnahmen_werkstatt(
    von_datum: date,
    bis_datum: date,
) -> Dict[str, float]:
    """
    Erwartete Einnahmen Werkstatt pro Tag (Locosoft invoices).
    Zahlungseingang = invoice_date + WST_ZAHLUNGSZIEL_TAGE.
    invoice_type 2,3,4,5,6 = Werkstatt.
    """
    result: Dict[str, float] = {}
    try:
        with locosoft_session() as conn:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Rechnungen mit Rechnungsdatum im Zeitraum; Zahlung = invoice_date + 14
            cur.execute("""
                SELECT invoice_date, COALESCE(SUM(total_net), 0) AS summe
                FROM invoices
                WHERE invoice_date >= %s AND invoice_date <= %s
                  AND is_canceled = false
                  AND invoice_type IN (2, 3, 4, 5, 6)
                GROUP BY invoice_date
            """, (von_datum, bis_datum))
            for row in cur.fetchall():
                d = row_to_dict(row, cur)
                inv_date = d.get("invoice_date")
                if not inv_date:
                    continue
                if hasattr(inv_date, "date"):
                    inv_date = inv_date.date()
                zahlung_am = inv_date + timedelta(days=WST_ZAHLUNGSZIEL_TAGE)
                if von_datum <= zahlung_am <= bis_datum:
                    key = zahlung_am.isoformat()
                    result[key] = result.get(key, 0.0) + float(d.get("summe") or 0)
        result = {k: round(v, 2) for k, v in result.items()}
    except Exception as e:
        logger.warning("get_erwartete_einnahmen_werkstatt: Locosoft fehlgeschlagen: %s", e)
    return result


def get_erwartete_einnahmen_gesamt(
    von_datum: date,
    bis_datum: date,
) -> Dict[str, Any]:
    """
    Kombiniert Fahrzeug (Netto) + Werkstatt pro Tag.
    Returns:
        {
            "pro_tag": { datum_iso: { "erwartete_einnahmen": float, "fahrzeug_netto": float, "werkstatt": float } },
            "quelle": "locosoft",
            "fehler": str | None
        }
    """
    fehler = None
    fz = get_erwartete_einnahmen_fahrzeug(von_datum, bis_datum)
    wst = get_erwartete_einnahmen_werkstatt(von_datum, bis_datum)
    alle_daten = set(fz.keys()) | set(wst.keys())
    pro_tag: Dict[str, Dict[str, float]] = {}
    for key in alle_daten:
        fz_netto = fz.get(key, {}).get("netto", 0.0) if isinstance(fz.get(key), dict) else 0.0
        wst_val = wst.get(key, 0.0)
        gesamt = round(fz_netto + wst_val, 2)
        pro_tag[key] = {
            "erwartete_einnahmen": gesamt,
            "fahrzeug_netto": round(fz_netto, 2),
            "werkstatt": round(wst_val, 2),
        }
    return {
        "pro_tag": pro_tag,
        "quelle": "locosoft",
        "fehler": fehler,
    }
