#!/usr/bin/env python3
"""
Profitabilitäts-Data – SSOT für Fahrzeug-Profitabilitätsanalyse (TAG 219)
=========================================================================
Nutzt dieselbe Datenquelle wie Auslieferung (Detail): DRIVE-Tabelle „sales“.
DB1/DB% kommen aus dem Sync (sync_sales.py) – keine redundante Berechnung.
Standzeit wird aus Locosoft ergänzt (ein Batch-Abruf pro Monat).

Verwendet von: api/profitabilitaet_api.py
Siehe: docs/PROFITABILITAET_VS_AUSLIEFERUNG_VERGLEICH.md
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal

from api.db_utils import db_session, locosoft_session
from psycopg2.extras import RealDictCursor

from api.standort_utils import STANDORT_NAMEN, build_locosoft_filter_verkauf
from api.kalkulation_helpers import ZINSSATZ_JAHR

logger = logging.getLogger(__name__)

# Standkosten-Parameter (konfigurierbar)
TAGESSATZ_PAUSCHAL = 12.00  # €/Tag (Versicherung, Platz, Marketing, Aufbereitung)

# Benchmark-Schwellen (Branchenwerte)
BENCHMARK_STANDZEIT_GUT = 65
BENCHMARK_STANDZEIT_MAX = 90
BENCHMARK_DB_PCT_GUT = 10.0
BENCHMARK_DB_PCT_MIN = 5.0
BENCHMARK_DB_PRO_FZG_GUT = 1500
BENCHMARK_DB_PRO_FZG_MIN = 500

# Marken-Mapping (out_make_number)
MARKEN = {27: "Hyundai", 40: "Opel", 41: "Leapmotor"}


def _float_or_zero(val: Any) -> float:
    """Decimal/None sicher in float umwandeln."""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _standzeit_bewertung(tage: float) -> str:
    if tage < BENCHMARK_STANDZEIT_GUT:
        return "gut"
    if tage <= BENCHMARK_STANDZEIT_MAX:
        return "ok"
    return "kritisch"


def _db_pct_bewertung(pct: float) -> str:
    if pct >= BENCHMARK_DB_PCT_GUT:
        return "gut"
    if pct >= BENCHMARK_DB_PCT_MIN:
        return "ok"
    return "schwach"


class ProfitabilitaetData:
    """
    SSOT für Fahrzeug-Profitabilitätsanalyse.
    Kombiniert Verkaufsdaten, Kalkulationen und Standkosten.
    """

    @staticmethod
    def _sales_subsidiary_filter(standort: Optional[int]) -> str:
        """SQL-Teil für out_subsidiary (wie build_locosoft_filter_verkauf, für Tabelle sales)."""
        if not standort:
            return "TRUE"
        if standort == 1:
            return "(s.out_subsidiary = 1 OR s.out_subsidiary = 2)"
        if standort == 2:
            return "s.out_subsidiary = 2"
        if standort == 3:
            return "s.out_subsidiary = 3"
        return "TRUE"

    @staticmethod
    def _fetch_standzeit_loco(
        month: int, year: int, standort: Optional[int], fahrzeugtyp: Optional[str]
    ) -> Dict[Tuple[str, str], float]:
        """Holt Standzeit (Tage) aus Locosoft für verkaufte Fz des Monats. Key: (dealer_vehicle_number, dealer_vehicle_type)."""
        where_parts = [
            "dv.out_invoice_date IS NOT NULL",
            "EXTRACT(YEAR FROM dv.out_invoice_date) = %s",
            "EXTRACT(MONTH FROM dv.out_invoice_date) = %s",
        ]
        params: List[Any] = [year, month]
        if standort:
            standort_filter = build_locosoft_filter_verkauf(int(standort), nur_stellantis=False)
            if standort_filter:
                filter_sql = standort_filter.replace("AND ", "").replace("out_subsidiary", "dv.out_subsidiary")
                where_parts.append(filter_sql)
        if fahrzeugtyp:
            where_parts.append("dv.dealer_vehicle_type = %s")
            params.append(fahrzeugtyp)
        where_clause = " AND ".join(where_parts)
        query = f"""
            SELECT dv.dealer_vehicle_number, dv.dealer_vehicle_type,
                   dv.in_arrival_date, dv.created_date, dv.out_invoice_date
            FROM dealer_vehicles dv
            WHERE {where_clause}
        """
        result: Dict[Tuple[str, str], float] = {}
        try:
            with locosoft_session() as conn:
                cur = conn.cursor()
                cur.execute(query, params)
                for row in cur.fetchall():
                    num, typ = str(row[0] or ""), str(row[1] or "")
                    in_arr, created, out_inv = row[2], row[3], row[4]
                    if not out_inv:
                        continue
                    start = in_arr or (created if isinstance(created, date) else None)
                    if start:
                        delta = (out_inv - start).days if hasattr(out_inv, "__sub__") else 0
                        result[(num, typ)] = max(0, delta)
                    else:
                        result[(num, typ)] = 0.0
        except Exception as e:
            logger.warning("Standzeit aus Locosoft nicht verfügbar: %s", e)
        return result

    @staticmethod
    def get_verkaufte_fahrzeuge_profitabilitaet(
        month: int,
        year: int,
        standort: Optional[int] = None,
        fahrzeugtyp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Holt verkaufte Fahrzeuge aus DRIVE-Tabelle „sales“ (gleiche Quelle wie Auslieferung).
        DB1/VKU aus sales; Standzeit aus Locosoft (ein Batch-Abruf).
        """
        try:
            subs_filter = ProfitabilitaetData._sales_subsidiary_filter(standort)
            standzeit_map = ProfitabilitaetData._fetch_standzeit_loco(month, year, standort, fahrzeugtyp)

            where_parts = [
                "s.out_invoice_date IS NOT NULL",
                "EXTRACT(YEAR FROM s.out_invoice_date) = %s",
                "EXTRACT(MONTH FROM s.out_invoice_date) = %s",
                subs_filter,
            ]
            params: List[Any] = [year, month]
            if fahrzeugtyp:
                where_parts.append("s.dealer_vehicle_type = %s")
                params.append(fahrzeugtyp)
            where_sql = " AND ".join(where_parts)

            with db_session() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(f"""
                    SELECT
                        s.dealer_vehicle_number,
                        s.dealer_vehicle_type,
                        s.vin,
                        s.model_description as modell,
                        s.out_invoice_date,
                        s.out_subsidiary as in_subsidiary,
                        s.salesman_number,
                        COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number) as verkaufer_name,
                        s.make_number,
                        COALESCE(s.out_sale_price, 0) as vk_brutto,
                        COALESCE(s.deckungsbeitrag, 0) as db1,
                        COALESCE(s.db_prozent, 0) as db_prozent,
                        COALESCE(s.fahrzeuggrundpreis, 0) + COALESCE(s.zubehoer, 0) + COALESCE(s.fracht_brief_neben, 0)
                            + COALESCE(s.einsatz_erhoehung_intern, 0) as ek_netto,
                        COALESCE(s.kosten_intern_rg, 0) + COALESCE(s.sonstige_kosten, 0) as variable_kosten,
                        COALESCE(s.verkaufsunterstuetzung, 0) as vku
                    FROM sales s
                    LEFT JOIN employees e ON s.salesman_number = e.locosoft_id
                    WHERE {where_sql}
                    ORDER BY s.out_invoice_date DESC, s.dealer_vehicle_number
                """, params)
                rows = cursor.fetchall()

            fahrzeuge: List[Dict[str, Any]] = []
            for row in rows:
                num, typ = str(row.get("dealer_vehicle_number") or ""), str(row.get("dealer_vehicle_type") or "")
                standzeit_tage = standzeit_map.get((num, typ), 0.0)
                ek = _float_or_zero(row.get("ek_netto"))
                vk_brutto = _float_or_zero(row.get("vk_brutto"))
                db1 = _float_or_zero(row.get("db1"))
                vku = _float_or_zero(row.get("vku"))

                standkosten_zins = ek * ZINSSATZ_JAHR * (standzeit_tage / 365) if standzeit_tage else 0
                standkosten_pauschal = standzeit_tage * TAGESSATZ_PAUSCHAL
                standkosten_gesamt = standkosten_zins + standkosten_pauschal
                db_nach_standkosten = db1 - standkosten_gesamt
                db_nach_standkosten_pct = (db_nach_standkosten / vk_brutto * 100) if vk_brutto else 0

                out_inv = row.get("out_invoice_date")
                fahrzeuge.append({
                    "dealer_vehicle_number": row.get("dealer_vehicle_number"),
                    "dealer_vehicle_type": row.get("dealer_vehicle_type"),
                    "vin": row.get("vin"),
                    "license_plate": None,
                    "modell": row.get("modell"),
                    "ez": None,
                    "in_arrival_date": None,
                    "out_invoice_date": out_inv.isoformat() if getattr(out_inv, "isoformat", None) else str(out_inv or ""),
                    "standzeit_tage": round(standzeit_tage, 0),
                    "ek_netto": round(ek, 2),
                    "vk_brutto": round(vk_brutto, 2),
                    "vk_netto": round(vk_brutto / 1.19, 2),
                    "variable_kosten": round(_float_or_zero(row.get("variable_kosten")), 2),
                    "vku": round(vku, 2),
                    "db1": round(db1, 2),
                    "standkosten_zins": round(standkosten_zins, 2),
                    "standkosten_pauschal": round(standkosten_pauschal, 2),
                    "standkosten_gesamt": round(standkosten_gesamt, 2),
                    "db_nach_standkosten": round(db_nach_standkosten, 2),
                    "db_nach_standkosten_pct": round(db_nach_standkosten_pct, 2),
                    "standzeit_bewertung": _standzeit_bewertung(standzeit_tage),
                    "db_pct_bewertung": _db_pct_bewertung(db_nach_standkosten_pct),
                    "salesman_number": row.get("salesman_number"),
                    "verkaufer_name": row.get("verkaufer_name") or f"Verkäufer #{row.get('salesman_number') or '?'}",
                    "in_subsidiary": row.get("in_subsidiary"),
                    "standort_name": STANDORT_NAMEN.get(row.get("in_subsidiary"), "Unbekannt"),
                    "make_number": row.get("make_number"),
                    "marke": MARKEN.get(row.get("make_number"), "Sonstige"),
                })

            logger.info(
                "ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet (sales): "
                "%s Fz, %s/%s, Standort=%s", len(fahrzeuge), month, year, standort
            )
            return {
                "success": True,
                "data": fahrzeuge,
                "meta": {"month": month, "year": year, "standort": standort, "typ": fahrzeugtyp},
            }
        except Exception as e:
            logger.exception("get_verkaufte_fahrzeuge_profitabilitaet: %s", e)
            return {"success": False, "data": [], "meta": {}, "error": str(e)}

    @staticmethod
    def get_profitabilitaet_summary(
        month: int,
        year: int,
        standort: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Aggregierte Profitabilitäts-KPIs für den Zeitraum."""
        out = ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet(month, year, standort)
        if not out.get("success") or not out.get("data"):
            return {
                "success": out.get("success", False),
                "data": {
                    "anzahl_verkauft": 0,
                    "summe_umsatz": 0,
                    "summe_db1": 0,
                    "summe_standkosten": 0,
                    "summe_db_netto": 0,
                    "avg_db1_pro_fzg": 0,
                    "avg_standzeit": 0,
                    "avg_standkosten_pro_fzg": 0,
                    "avg_db_netto_pro_fzg": 0,
                    "nach_typ": {},
                    "nach_marke": {},
                    "anteil_db_positiv": 0,
                    "anteil_standzeit_unter_65": 0,
                },
                "meta": out.get("meta", {}),
            }

        data = out["data"]
        n = len(data)
        summe_umsatz = sum(f["vk_brutto"] for f in data)
        summe_db1 = sum(f["db1"] for f in data)
        summe_standkosten = sum(f["standkosten_gesamt"] for f in data)
        summe_db_netto = sum(f["db_nach_standkosten"] for f in data)
        summe_standzeit = sum(f["standzeit_tage"] for f in data)

        nach_typ: Dict[str, Dict[str, float]] = {}
        for f in data:
            typ = f.get("dealer_vehicle_type") or "?"
            if typ not in nach_typ:
                nach_typ[typ] = {"anzahl": 0, "summe_db1": 0, "summe_standzeit": 0, "summe_db_netto": 0}
            nach_typ[typ]["anzahl"] += 1
            nach_typ[typ]["summe_db1"] += f["db1"]
            nach_typ[typ]["summe_standzeit"] += f["standzeit_tage"]
            nach_typ[typ]["summe_db_netto"] += f["db_nach_standkosten"]
        for typ, agg in nach_typ.items():
            k = agg["anzahl"]
            agg["avg_db"] = round(agg["summe_db1"] / k, 2) if k else 0
            agg["avg_standzeit"] = round(agg["summe_standzeit"] / k, 1) if k else 0
            agg["avg_db_netto"] = round(agg["summe_db_netto"] / k, 2) if k else 0

        nach_marke: Dict[str, Dict[str, float]] = {}
        for f in data:
            marke = f.get("marke") or "Sonstige"
            if marke not in nach_marke:
                nach_marke[marke] = {"anzahl": 0, "summe_db1": 0, "summe_standzeit": 0}
            nach_marke[marke]["anzahl"] += 1
            nach_marke[marke]["summe_db1"] += f["db1"]
            nach_marke[marke]["summe_standzeit"] += f["standzeit_tage"]
        for marke, agg in nach_marke.items():
            k = agg["anzahl"]
            agg["avg_db"] = round(agg["summe_db1"] / k, 2) if k else 0
            agg["avg_standzeit"] = round(agg["summe_standzeit"] / k, 1) if k else 0

        anteil_db_positiv = (sum(1 for f in data if f["db_nach_standkosten"] > 0) / n * 100) if n else 0
        anteil_standzeit_unter_65 = (sum(1 for f in data if f["standzeit_tage"] < BENCHMARK_STANDZEIT_GUT) / n * 100) if n else 0

        return {
            "success": True,
            "data": {
                "anzahl_verkauft": n,
                "summe_umsatz": round(summe_umsatz, 2),
                "summe_db1": round(summe_db1, 2),
                "summe_standkosten": round(summe_standkosten, 2),
                "summe_db_netto": round(summe_db_netto, 2),
                "avg_db1_pro_fzg": round(summe_db1 / n, 2) if n else 0,
                "avg_standzeit": round(summe_standzeit / n, 1) if n else 0,
                "avg_standkosten_pro_fzg": round(summe_standkosten / n, 2) if n else 0,
                "avg_db_netto_pro_fzg": round(summe_db_netto / n, 2) if n else 0,
                "nach_typ": nach_typ,
                "nach_marke": nach_marke,
                "anteil_db_positiv": round(anteil_db_positiv, 1),
                "anteil_standzeit_unter_65": round(anteil_standzeit_unter_65, 1),
            },
            "meta": out.get("meta", {}),
        }

    @staticmethod
    def get_verkaeufer_profitabilitaet(
        month: int,
        year: int,
        standort: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Profitabilität pro Verkäufer, sortiert nach DB netto absteigend."""
        out = ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet(month, year, standort)
        if not out.get("success") or not out.get("data"):
            return {"success": out.get("success", False), "data": [], "meta": out.get("meta", {})}

        by_vk: Dict[Any, Dict[str, Any]] = {}
        for f in out["data"]:
            key = (f.get("salesman_number"), f.get("verkaufer_name"))
            if key not in by_vk:
                by_vk[key] = {
                    "salesman_number": f.get("salesman_number"),
                    "name": f.get("verkaufer_name"),
                    "anzahl_verkauft": 0,
                    "summe_db1": 0,
                    "summe_standkosten": 0,
                    "summe_db_netto": 0,
                    "summe_standzeit": 0,
                }
            by_vk[key]["anzahl_verkauft"] += 1
            by_vk[key]["summe_db1"] += f["db1"]
            by_vk[key]["summe_standkosten"] += f["standkosten_gesamt"]
            by_vk[key]["summe_db_netto"] += f["db_nach_standkosten"]
            by_vk[key]["summe_standzeit"] += f["standzeit_tage"]

        liste = []
        for v in by_vk.values():
            k = v["anzahl_verkauft"]
            liste.append({
                "salesman_number": v["salesman_number"],
                "name": v["name"],
                "anzahl_verkauft": k,
                "summe_db1": round(v["summe_db1"], 2),
                "avg_db_pro_fzg": round(v["summe_db1"] / k, 2) if k else 0,
                "summe_standkosten": round(v["summe_standkosten"], 2),
                "summe_db_netto": round(v["summe_db_netto"], 2),
                "avg_standzeit": round(v["summe_standzeit"] / k, 1) if k else 0,
            })
        liste.sort(key=lambda x: x["summe_db_netto"], reverse=True)

        return {"success": True, "data": liste, "meta": out.get("meta", {})}

    @staticmethod
    def get_profitabilitaet_trend(
        year: int,
        standort: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Monatlicher Trend (12 Monate) für Charts."""
        monate = []
        for month in range(1, 13):
            out = ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet(month, year, standort)
            if not out.get("success"):
                monate.append({
                    "month": month,
                    "year": year,
                    "anzahl": 0,
                    "summe_db1": 0,
                    "avg_db_pro_fzg": 0,
                    "avg_standzeit": 0,
                    "summe_standkosten": 0,
                    "summe_db_netto": 0,
                })
                continue
            data = out.get("data") or []
            n = len(data)
            summe_db1 = sum(f["db1"] for f in data)
            summe_standzeit = sum(f["standzeit_tage"] for f in data)
            summe_standkosten = sum(f["standkosten_gesamt"] for f in data)
            summe_db_netto = sum(f["db_nach_standkosten"] for f in data)
            monate.append({
                "month": month,
                "year": year,
                "anzahl": n,
                "summe_db1": round(summe_db1, 2),
                "avg_db_pro_fzg": round(summe_db1 / n, 2) if n else 0,
                "avg_standzeit": round(summe_standzeit / n, 1) if n else 0,
                "summe_standkosten": round(summe_standkosten, 2),
                "summe_db_netto": round(summe_db_netto, 2),
            })
        return {"success": True, "data": monate, "meta": {"year": year, "standort": standort}}
