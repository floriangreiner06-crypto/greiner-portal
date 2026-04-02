"""
Verkäufer-Zielplanung API – Kalenderjahr, NW/GW-Ziele, Verteilung nach Historie
===============================================================================
Daten: Locosoft dealer_vehicles + employees_history + makes.
Basis: **Auftragseingang** (Vertragsdatum out_sales_contract_date), nicht Fakturierung
(out_invoice_date) – entspricht Verkäuferarbeitsplatz Catch / DRIVE Auftragseingang.
Pool Handelsgeschäft (von Verteilung ausgenommen): 9001, 1003, 2000.
Gespeicherte Ziele: Tabelle verkaeufer_ziele; nach Speichern wirksam für Monatsziele und Auftragseingang.

NW nach Marken:
- Hyundai: Ziel-Pool nur auf Roland (2006) und Edeltraud (2001) aufteilen.
- Opel: Die beiden haben keine Relevanz; Pool nur auf die übrigen Verkäufer.
- Leapmotor: Auf alle (außer Pool) verteilen.

Endpoints:
- GET /api/verkaeufer-zielplanung/stueckzahl/<jahr>  – Stückzahl pro Verkäufer (NW/GW + NW nach Marke)
- GET /api/verkaeufer-zielplanung/verteilung        – Ziele verteilt (optional ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor)
- GET /api/verkaeufer-zielplanung/saisonalitaet/<jahr> – Monatsverteilung NW/GW aus Referenzjahr (Anteile in %)
- GET /api/verkaeufer-zielplanung/monatsverteilung  – Ziele auf 12 Monate verteilt (Query: referenz_jahr, ziel_nw, ziel_gw)
- GET /api/verkaeufer-zielplanung/monatsziele      – Monatsziele für ein (jahr, monat): Konzern + pro Verkäufer (für Zielerfüllung Auftragseingang)
- GET /api/verkaeufer-zielplanung/ziele/<jahr>      – Gespeicherte Ziele für Jahr
- POST /api/verkaeufer-zielplanung/ziele/<jahr>     – Ziele speichern (Body: ziele[], optional: referenz_jahr, konzernziel_nw/gw, ziel_nw_hyundai/opel/leapmotor); schreibt auch Planungsstand (Status Entwurf)
- GET /api/verkaeufer-zielplanung/planungsstand/<jahr> – Planungsstand + Parameter + Ziele (für Seitenaufruf)
- POST /api/verkaeufer-zielplanung/planungsstand/<jahr>/freigeben – Planung freigeben (Status → freigegeben; ab dann wirksam für Monatsziele/Auftragseingang)
- GET /api/verkaeufer-zielplanung/pool             – Konfiguration Pool Handelsgeschäft
"""
import logging
import copy
import math
import threading
import time
from flask import Blueprint, jsonify, request
from flask_login import current_user
from psycopg2.extras import RealDictCursor

from api.db_connection import get_db
from api.db_utils import get_locosoft_connection
from api.verkauf_data import FAHRZEUGTYP_NW, FAHRZEUGTYP_GW

logger = logging.getLogger(__name__)

_DATA_CACHE_TTL_SECONDS = 900
_stueckzahl_cache: dict[int, tuple[float, list]] = {}
_saisonal_cache: dict[int, tuple[float, dict]] = {}
_data_cache_lock = threading.Lock()

verkaeufer_zielplanung_bp = Blueprint(
    "verkaeufer_zielplanung",
    __name__,
    url_prefix="/api/verkaeufer-zielplanung",
)

# Pool Handelsgeschäft – von Zielverteilung ausgenommen (siehe VERKAEUFER_HANDELSGESCHAEFT_POOL.md)
POOL_HANDELSGESCHAEFT = [9001, 1003, 2000]

# NW Hyundai: nur diese zwei Verkäufer bekommen Hyundai-NW-Ziele (Roland Schmid, Edeltraud Punzmann)
NW_HYUNDAI_VERKAEUFER = [2001, 2006]

# Locosoft makes.make_number: 27=Hyundai, 40=Opel, 41=Leapmotor
MAKE_HYUNDAI, MAKE_OPEL, MAKE_LEAPMOTOR = 27, 40, 41

STANDORT_NAME = {1: "DEG", 2: "HYU", 3: "LAN", None: "-"}


def _stueckzahl_fuer_jahr(jahr: int):
    """
    Liest aus Locosoft: Auftragseingang (Vertragsdatum) pro Verkäufer für Kalenderjahr.
    Stück NW/GW, NW aufgeteilt nach Marke (Hyundai/Opel/Leapmotor).
    T-Regel Verkaufsleitung: T = NW nur bis 1 Jahr ab Erstzulassung; älter = GW (v.first_registration_date).
    Dedup: N wird nicht gezählt, wenn dieselbe vehicle_number am gleichen Vertragsdatum als T oder V vorkommt.
    """
    now_ts = time.time()
    with _data_cache_lock:
        cached = _stueckzahl_cache.get(jahr)
        if cached and now_ts - cached[0] <= _DATA_CACHE_TTL_SECONDS:
            return copy.deepcopy(cached[1])

    # T zählt als NW nur wenn (Vertragsdatum - Erstzulassung) <= 365 Tage; fehlt Ez → NW
    _t_als_nw = "(v.first_registration_date IS NULL OR (dv.out_sales_contract_date::date - v.first_registration_date) <= 365)"
    _is_nw = f"(dv.dealer_vehicle_type IN ('N','V') OR (dv.dealer_vehicle_type = 'T' AND {_t_als_nw}))"
    _is_gw = f"(dv.dealer_vehicle_type IN ('D','G') OR (dv.dealer_vehicle_type = 'T' AND v.first_registration_date IS NOT NULL AND (dv.out_sales_contract_date::date - v.first_registration_date) > 365))"
    conn = get_locosoft_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        f"""
        SELECT
            dv.out_salesman_number_1 AS mitarbeiter_nr,
            eh.name AS mitarbeiter_name,
            eh.subsidiary AS standort,
            COUNT(*) FILTER (WHERE {_is_nw}) AS nw_stueck,
            COUNT(*) FILTER (WHERE dv.dealer_vehicle_type = 'N') AS nw_neu,
            COUNT(*) FILTER (WHERE dv.dealer_vehicle_type = 'V') AS nw_vorfuehr,
            COUNT(*) FILTER (WHERE dv.dealer_vehicle_type = 'T' AND ({_t_als_nw})) AS nw_tageszulassung,
            COUNT(*) FILTER (WHERE {_is_gw}) AS gw_stueck,
            COUNT(*) FILTER (WHERE {_is_nw} AND dv.out_make_number = %s) AS nw_hyundai,
            COUNT(*) FILTER (WHERE {_is_nw} AND dv.out_make_number = %s) AS nw_opel,
            COUNT(*) FILTER (WHERE {_is_nw} AND dv.out_make_number = %s) AS nw_leapmotor
        FROM dealer_vehicles dv
        LEFT JOIN vehicles v ON v.dealer_vehicle_number = dv.dealer_vehicle_number AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        LEFT JOIN employees_history eh
            ON eh.employee_number = dv.out_salesman_number_1
            AND eh.is_latest_record = true
        WHERE EXTRACT(YEAR FROM dv.out_sales_contract_date) = %s
          AND dv.out_sales_contract_date IS NOT NULL
          AND dv.dealer_vehicle_type IN {FAHRZEUGTYP_NW + FAHRZEUGTYP_GW}
          AND dv.out_salesman_number_1 IS NOT NULL
          AND NOT (
            dv.dealer_vehicle_type = 'N'
            AND EXISTS (
                SELECT 1 FROM dealer_vehicles dv2
                WHERE dv2.vehicle_number = dv.vehicle_number
                  AND dv2.out_sales_contract_date = dv.out_sales_contract_date
                  AND dv2.dealer_vehicle_type IN ('T', 'V')
            )
          )
        GROUP BY dv.out_salesman_number_1, eh.name, eh.subsidiary
        ORDER BY (COUNT(*) FILTER (WHERE {_is_nw}) + COUNT(*) FILTER (WHERE {_is_gw})) DESC
        """,
        (MAKE_HYUNDAI, MAKE_OPEL, MAKE_LEAPMOTOR, jahr),
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        nw = int(r["nw_stueck"] or 0)
        gw = int(r["gw_stueck"] or 0)
        nw_neu = int(r.get("nw_neu") or 0)
        nw_vfw = int(r.get("nw_vorfuehr") or 0)
        nw_tz = int(r.get("nw_tageszulassung") or 0)
        nw_hy = int(r["nw_hyundai"] or 0)
        nw_op = int(r["nw_opel"] or 0)
        nw_lm = int(r["nw_leapmotor"] or 0)
        result.append(
            {
                "mitarbeiter_nr": r["mitarbeiter_nr"],
                "name": (r.get("mitarbeiter_name") or "").strip()
                or f"Verkäufer #{r['mitarbeiter_nr']}",
                "standort": STANDORT_NAME.get(
                    r.get("standort"), str(r.get("standort") or "")
                ),
                "nw_stueck": nw,
                "nw_neu": nw_neu,
                "nw_vorfuehr": nw_vfw,
                "nw_tageszulassung": nw_tz,
                "gw_stueck": gw,
                "nw_hyundai": nw_hy,
                "nw_opel": nw_op,
                "nw_leapmotor": nw_lm,
                "summe_stueck": nw + gw,
                "ist_handelsgeschaeft": r["mitarbeiter_nr"] in POOL_HANDELSGESCHAEFT,
            }
        )
    with _data_cache_lock:
        _stueckzahl_cache[jahr] = (time.time(), copy.deepcopy(result))
    return result


def _saisonalitaet_fuer_jahr(jahr: int):
    """
    Liest aus Locosoft: Auftragseingang pro Monat (1–12) für ein Kalenderjahr.
    Gleiche Filter/Dedup und T-Regel (Ez ≤ 1 Jahr = NW) wie _stueckzahl_fuer_jahr.
    """
    now_ts = time.time()
    with _data_cache_lock:
        cached = _saisonal_cache.get(jahr)
        if cached and now_ts - cached[0] <= _DATA_CACHE_TTL_SECONDS:
            return copy.deepcopy(cached[1])

    _t_als_nw = "(v.first_registration_date IS NULL OR (dv.out_sales_contract_date::date - v.first_registration_date) <= 365)"
    _is_nw = f"(dv.dealer_vehicle_type IN ('N','V') OR (dv.dealer_vehicle_type = 'T' AND {_t_als_nw}))"
    _is_gw = f"(dv.dealer_vehicle_type IN ('D','G') OR (dv.dealer_vehicle_type = 'T' AND v.first_registration_date IS NOT NULL AND (dv.out_sales_contract_date::date - v.first_registration_date) > 365))"
    conn = get_locosoft_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        f"""
        SELECT
            EXTRACT(MONTH FROM dv.out_sales_contract_date)::integer AS monat,
            COUNT(*) FILTER (WHERE {_is_nw}) AS nw_stueck,
            COUNT(*) FILTER (WHERE {_is_gw}) AS gw_stueck
        FROM dealer_vehicles dv
        LEFT JOIN vehicles v ON v.dealer_vehicle_number = dv.dealer_vehicle_number AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        WHERE EXTRACT(YEAR FROM dv.out_sales_contract_date) = %s
          AND dv.out_sales_contract_date IS NOT NULL
          AND dv.dealer_vehicle_type IN {FAHRZEUGTYP_NW + FAHRZEUGTYP_GW}
          AND dv.out_salesman_number_1 IS NOT NULL
          AND NOT (
            dv.dealer_vehicle_type = 'N'
            AND EXISTS (
                SELECT 1 FROM dealer_vehicles dv2
                WHERE dv2.vehicle_number = dv.vehicle_number
                  AND dv2.out_sales_contract_date = dv.out_sales_contract_date
                  AND dv2.dealer_vehicle_type IN ('T', 'V')
            )
          )
        GROUP BY EXTRACT(MONTH FROM dv.out_sales_contract_date)
        ORDER BY monat
        """,
        (jahr,),
    )
    rows = cur.fetchall()
    conn.close()

    # Alle 12 Monate (fehlende Monate = 0)
    by_month = {int(r["monat"]): {"nw": int(r["nw_stueck"] or 0), "gw": int(r["gw_stueck"] or 0)} for r in rows}
    gesamt_nw = sum(d["nw"] for d in by_month.values())
    gesamt_gw = sum(d["gw"] for d in by_month.values())

    monate = []
    for m in range(1, 13):
        d = by_month.get(m, {"nw": 0, "gw": 0})
        nw_pct = round(100.0 * d["nw"] / gesamt_nw, 2) if gesamt_nw else 0
        gw_pct = round(100.0 * d["gw"] / gesamt_gw, 2) if gesamt_gw else 0
        monate.append({
            "monat": m,
            "nw_stueck": d["nw"],
            "gw_stueck": d["gw"],
            "nw_pct": nw_pct,
            "gw_pct": gw_pct,
        })

    out = {
        "jahr": jahr,
        "monate": monate,
        "gesamt_nw": gesamt_nw,
        "gesamt_gw": gesamt_gw,
    }
    with _data_cache_lock:
        _saisonal_cache[jahr] = (time.time(), copy.deepcopy(out))
    return out


def _monatsverteilung_aus_saisonalitaet(ziel_nw: int, ziel_gw: int, saisonalitaet: dict):
    """
    Verteilt Jahresziele ziel_nw / ziel_gw auf 12 Monate gemäß Saisonalität (Anteile in %).
    Rundung: Rest wird den Monaten mit größtem Nachkommaanteil zugegeben.
    """
    monate = saisonalitaet.get("monate", [])
    if len(monate) != 12:
        return []
    out = []
    nw_rest = ziel_nw
    gw_rest = ziel_gw
    # Zuerst mit floor
    for i, m in enumerate(monate):
        z_nw = int(ziel_nw * (m["nw_pct"] or 0) / 100)
        z_gw = int(ziel_gw * (m["gw_pct"] or 0) / 100)
        nw_rest -= z_nw
        gw_rest -= z_gw
        out.append({
            "monat": m["monat"],
            "nw_pct": m["nw_pct"],
            "gw_pct": m["gw_pct"],
            "ziel_nw": z_nw,
            "ziel_gw": z_gw,
        })
    # Rest verteilen (Monate mit höchstem Anteil zuerst)
    nw_sorted = sorted(range(12), key=lambda i: monate[i]["nw_pct"] or 0, reverse=True)
    for idx in nw_sorted:
        if nw_rest <= 0:
            break
        out[idx]["ziel_nw"] += 1
        nw_rest -= 1
    gw_sorted = sorted(range(12), key=lambda i: monate[i]["gw_pct"] or 0, reverse=True)
    for idx in gw_sorted:
        if gw_rest <= 0:
            break
        out[idx]["ziel_gw"] += 1
        gw_rest -= 1
    return out


def _verteile_rest(stueck_rest: int, out: list, referenz_daten: list, indices: list, key: str):
    """Verteilt Rest-Stück (Rundung) auf indices (nicht Pool). key = 'ziel_nw' oder 'ziel_gw'."""
    idx = 0
    while stueck_rest != 0 and indices:
        i = indices[idx % len(indices)]
        if stueck_rest > 0:
            out[i][key] += 1
            stueck_rest -= 1
        else:
            out[i][key] -= 1
            stueck_rest += 1
        idx += 1


def _verteilung_berechnen(
    referenz_daten: list,
    ziel_nw: int,
    ziel_gw: int,
    ziel_nw_hyundai: int | None = None,
    ziel_nw_opel: int | None = None,
    ziel_nw_leapmotor: int | None = None,
):
    """
    Verteilt Ziele auf Verkäufer. NW nach Marken:
    - Hyundai: nur an 2001, 2006 (Roland, Edeltraud).
    - Opel: nur an alle außer Pool und außer 2001, 2006.
    - Leapmotor: an alle außer Pool.
    GW: an alle außer Pool.
    Wenn ziel_nw_hyundai/opel/leapmotor nicht übergeben, werden sie aus ziel_nw nach Referenz-Anteilen abgeleitet.
    """
    # Ziele NW pro Marke ableiten, falls nicht übergeben
    total_nw_ref = sum(d["nw_stueck"] for d in referenz_daten)
    nw_hy_ref = sum(d.get("nw_hyundai", 0) for d in referenz_daten)
    nw_op_ref = sum(d.get("nw_opel", 0) for d in referenz_daten)
    nw_lm_ref = sum(d.get("nw_leapmotor", 0) for d in referenz_daten)
    if ziel_nw_hyundai is None:
        ziel_nw_hyundai = int(round(ziel_nw * nw_hy_ref / total_nw_ref)) if total_nw_ref else 0
    if ziel_nw_opel is None:
        ziel_nw_opel = int(round(ziel_nw * nw_op_ref / total_nw_ref)) if total_nw_ref else 0
    if ziel_nw_leapmotor is None:
        ziel_nw_leapmotor = int(round(ziel_nw * nw_lm_ref / total_nw_ref)) if total_nw_ref else 0
    # Korrektur: Summe soll ziel_nw ergeben (Rest in größte Marke)
    diff = ziel_nw - (ziel_nw_hyundai + ziel_nw_opel + ziel_nw_leapmotor)
    if diff != 0:
        ziel_nw_opel = max(0, ziel_nw_opel + diff)  # Rest in Opel

    # Handelsgeschäft-Abzug pro Marke und GW
    def _handel_sum(key):
        return sum(d.get(key, 0) for d in referenz_daten if d.get("ist_handelsgeschaeft"))

    nw_handel_hy = _handel_sum("nw_hyundai")
    nw_handel_op = _handel_sum("nw_opel")
    nw_handel_lm = _handel_sum("nw_leapmotor")
    gw_handel = _handel_sum("gw_stueck")
    pool_hy = ziel_nw_hyundai - nw_handel_hy
    pool_op = ziel_nw_opel - nw_handel_op
    pool_lm = ziel_nw_leapmotor - nw_handel_lm
    pool_gw = ziel_gw - gw_handel

    nur_nicht_pool = [d for d in referenz_daten if not d.get("ist_handelsgeschaeft")]
    nur_hyundai_vk = [d for d in nur_nicht_pool if d["mitarbeiter_nr"] in NW_HYUNDAI_VERKAEUFER]
    nur_opel_vk = [d for d in nur_nicht_pool if d["mitarbeiter_nr"] not in NW_HYUNDAI_VERKAEUFER]

    sum_hy = sum(d.get("nw_hyundai", 0) for d in nur_hyundai_vk)
    sum_op = sum(d.get("nw_opel", 0) for d in nur_opel_vk)
    sum_lm = sum(d.get("nw_leapmotor", 0) for d in nur_nicht_pool)
    sum_gw = sum(d["gw_stueck"] for d in nur_nicht_pool)

    out = []
    rest_hy = pool_hy
    rest_op = pool_op
    rest_lm = pool_lm
    rest_gw = pool_gw

    for d in referenz_daten:
        nr = d["mitarbeiter_nr"]
        name = d["name"]
        standort = d.get("standort", "")
        is_pool = d.get("ist_handelsgeschaeft", False)
        nw_hy = d.get("nw_hyundai", 0)
        nw_op = d.get("nw_opel", 0)
        nw_lm = d.get("nw_leapmotor", 0)
        gw_ist = d["gw_stueck"]
        nw_ist = d["nw_stueck"]

        if is_pool:
            ziel_nw_hy_vk = nw_hy
            ziel_nw_op_vk = nw_op
            ziel_nw_lm_vk = nw_lm
            ziel_gw_vk = gw_ist
        else:
            # Hyundai: nur 2001, 2006
            if nr in NW_HYUNDAI_VERKAEUFER and sum_hy and sum_hy > 0:
                ziel_nw_hy_vk = int(pool_hy * (nw_hy / sum_hy))
            else:
                ziel_nw_hy_vk = 0
            # Opel: nur nicht-Hyundai-Verkäufer (ohne 2001, 2006)
            if nr not in NW_HYUNDAI_VERKAEUFER and sum_op and sum_op > 0:
                ziel_nw_op_vk = int(pool_op * (nw_op / sum_op))
            else:
                ziel_nw_op_vk = 0
            # Leapmotor: alle
            if sum_lm and sum_lm > 0:
                ziel_nw_lm_vk = int(pool_lm * (nw_lm / sum_lm))
            else:
                ziel_nw_lm_vk = 0
            if sum_gw and sum_gw > 0:
                ziel_gw_vk = int(pool_gw * (gw_ist / sum_gw))
            else:
                ziel_gw_vk = 0
            rest_hy -= ziel_nw_hy_vk
            rest_op -= ziel_nw_op_vk
            rest_lm -= ziel_nw_lm_vk
            rest_gw -= ziel_gw_vk

        ziel_nw_vk = ziel_nw_hy_vk + ziel_nw_op_vk + ziel_nw_lm_vk
        out.append({
            "mitarbeiter_nr": nr,
            "name": name,
            "standort": standort,
            "nw_ist": nw_ist,
            "gw_ist": gw_ist,
            "nw_hyundai_ist": nw_hy,
            "nw_opel_ist": nw_op,
            "nw_leapmotor_ist": nw_lm,
            "ziel_nw_hyundai": ziel_nw_hy_vk,
            "ziel_nw_opel": ziel_nw_op_vk,
            "ziel_nw_leapmotor": ziel_nw_lm_vk,
            "ziel_nw": ziel_nw_vk,
            "ziel_gw": ziel_gw_vk,
            "ziel_summe": ziel_nw_vk + ziel_gw_vk,
            "ist_handelsgeschaeft": is_pool,
        })

    # Rest-Stück verteilen
    idx_pool = [i for i, d in enumerate(referenz_daten) if not d.get("ist_handelsgeschaeft")]
    idx_hy = [i for i in idx_pool if referenz_daten[i]["mitarbeiter_nr"] in NW_HYUNDAI_VERKAEUFER]
    idx_op = [i for i in idx_pool if referenz_daten[i]["mitarbeiter_nr"] not in NW_HYUNDAI_VERKAEUFER]
    _verteile_rest(rest_hy, out, referenz_daten, idx_hy, "ziel_nw_hyundai")
    _verteile_rest(rest_op, out, referenz_daten, idx_op, "ziel_nw_opel")
    _verteile_rest(rest_lm, out, referenz_daten, idx_pool, "ziel_nw_leapmotor")
    _verteile_rest(rest_gw, out, referenz_daten, idx_pool, "ziel_gw")
    for o in out:
        o["ziel_nw"] = o["ziel_nw_hyundai"] + o["ziel_nw_opel"] + o["ziel_nw_leapmotor"]
        o["ziel_summe"] = o["ziel_nw"] + o["ziel_gw"]

    # Pool-Mitglieder ans Ende, ansonsten Reihenfolge beibehalten (stabile Sortierung)
    out.sort(key=lambda v: v.get("ist_handelsgeschaeft", False))

    nw_handel = nw_handel_hy + nw_handel_op + nw_handel_lm
    return {
        "verkaeufer": out,
        "konzernziel_nw": ziel_nw,
        "konzernziel_gw": ziel_gw,
        "konzernziel_nw_hyundai": ziel_nw_hyundai,
        "konzernziel_nw_opel": ziel_nw_opel,
        "konzernziel_nw_leapmotor": ziel_nw_leapmotor,
        "pool_handelsgeschaeft_nw": nw_handel,
        "pool_handelsgeschaeft_gw": gw_handel,
        "pool_verteilung_nw": pool_hy + pool_op + pool_lm,
        "pool_verteilung_gw": pool_gw,
        "summe_ziel_nw": sum(x["ziel_nw"] for x in out),
        "summe_ziel_gw": sum(x["ziel_gw"] for x in out),
    }


def _get_gespeicherte_ziele(jahr: int):
    """Liest gespeicherte Ziele für ein Kalenderjahr aus verkaeufer_ziele (Portal-DB)."""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw,
                   planungsgespraech_am, planungsgespraech_notiz, gespeichert_von, gespeichert_am
            FROM verkaeufer_ziele
            WHERE kalenderjahr = %s
            ORDER BY mitarbeiter_nr
            """,
            (jahr,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "mitarbeiter_nr": r["mitarbeiter_nr"],
                "ziel_nw": int(r["ziel_nw"] or 0),
                "ziel_gw": int(r["ziel_gw"] or 0),
                "planungsgespraech_am": r["planungsgespraech_am"].isoformat() if r.get("planungsgespraech_am") else None,
                "planungsgespraech_notiz": (r.get("planungsgespraech_notiz") or "").strip() or None,
                "gespeichert_von": r.get("gespeichert_von"),
                "gespeichert_am": r["gespeichert_am"].isoformat() if r.get("gespeichert_am") else None,
            }
            for r in rows
        ]
    except Exception as e:
        if "does not exist" in str(e).lower() or "verkaeufer_ziele" in str(e):
            return []
        logger.warning("Gespeicherte Ziele lesen für %s: %s", jahr, e)
        return []


def get_nw_ziel_verkaeufer_monat(mitarbeiter_nr: int, jahr: int, monat: int) -> int:
    """
    NW-Ziel (Stück) für einen Verkäufer in einem Monat – aus Verkäufer-Zielplanung.
    Wird von Provisionsmodul für Zielprämie (I_neuwagen) genutzt.
    - Wenn Planung freigegeben: gespeicherte Ziele × Saisonalität.
    - Wenn nicht freigegeben: Vorschlag (Verteilung × Saisonalität) für Tests ohne Freigabe.
    Returns: Ziel NW für diesen Monat (0 wenn Verkäufer nicht in Zielen/Vorschlag).
    """
    if monat < 1 or monat > 12:
        return 0
    try:
        referenz_jahr = max(2024, jahr - 1)
        saison = _saisonalitaet_fuer_jahr(referenz_jahr)
        monate = saison.get("monate", [])
        if len(monate) < monat:
            return 0
        nw_pct = (monate[monat - 1].get("nw_pct") or 0) / 100.0
        planstand = _get_planungsstand(jahr)
        gespeichert = _get_gespeicherte_ziele(jahr) if (planstand and planstand.get("status") == "freigegeben") else []

        if gespeichert:
            for v in gespeichert:
                if v.get("mitarbeiter_nr") == mitarbeiter_nr:
                    ziel_jahr = int(v.get("ziel_nw") or 0)
                    return max(0, math.floor(ziel_jahr * nw_pct + 0.5))
            return 0

        # Ohne Freigabe: Vorschlag nutzen (Verteilung × Saisonalität) – zum Testen ohne Zielplanung-Freigabe
        referenz_daten = _stueckzahl_fuer_jahr(referenz_jahr)
        ziel_nw = (planstand.get("konzernziel_nw") or 630) if planstand else 630
        ziel_gw = (planstand.get("konzernziel_gw") or 900) if planstand else 900
        verteilung = _verteilung_berechnen(
            referenz_daten, ziel_nw, ziel_gw,
            ziel_nw_hyundai=planstand.get("ziel_nw_hyundai") if planstand else None,
            ziel_nw_opel=planstand.get("ziel_nw_opel") if planstand else None,
            ziel_nw_leapmotor=planstand.get("ziel_nw_leapmotor") if planstand else None,
        )
        for v in verteilung.get("verkaeufer", []):
            if v.get("mitarbeiter_nr") == mitarbeiter_nr:
                ziel_jahr = int(v.get("ziel_nw") or 0)
                return max(0, math.floor(ziel_jahr * nw_pct + 0.5))
        return 0
    except Exception:
        return 0


def _get_planungsstand(jahr: int):
    """
    Liest Planungsstand für ein Zieljahr aus zielplanung_stand.
    Returns: dict mit referenz_jahr, konzernziel_nw, konzernziel_gw, ziel_nw_hyundai/opel/leapmotor,
             status, zuletzt_gespeichert_am/von, freigegeben_am/von – oder None wenn kein Eintrag/Tabelle fehlt.
    """
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT kalenderjahr, referenz_jahr, konzernziel_nw, konzernziel_gw,
                   ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor, status,
                   zuletzt_gespeichert_am, zuletzt_gespeichert_von,
                   freigegeben_am, freigegeben_von
            FROM zielplanung_stand
            WHERE kalenderjahr = %s
            """,
            (jahr,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "kalenderjahr": row["kalenderjahr"],
            "referenz_jahr": row["referenz_jahr"],
            "konzernziel_nw": int(row["konzernziel_nw"] or 0),
            "konzernziel_gw": int(row["konzernziel_gw"] or 0),
            "ziel_nw_hyundai": int(row["ziel_nw_hyundai"]) if row.get("ziel_nw_hyundai") is not None else None,
            "ziel_nw_opel": int(row["ziel_nw_opel"]) if row.get("ziel_nw_opel") is not None else None,
            "ziel_nw_leapmotor": int(row["ziel_nw_leapmotor"]) if row.get("ziel_nw_leapmotor") is not None else None,
            "status": (row.get("status") or "entwurf").strip().lower(),
            "zuletzt_gespeichert_am": row["zuletzt_gespeichert_am"].isoformat() if row.get("zuletzt_gespeichert_am") else None,
            "zuletzt_gespeichert_von": row.get("zuletzt_gespeichert_von"),
            "freigegeben_am": row["freigegeben_am"].isoformat() if row.get("freigegeben_am") else None,
            "freigegeben_von": row.get("freigegeben_von"),
        }
    except Exception as e:
        if "does not exist" in str(e).lower() or "zielplanung_stand" in str(e):
            return None
        logger.warning("Planungsstand lesen für %s: %s", jahr, e)
        return None


@verkaeufer_zielplanung_bp.route("/planungsstand/<int:jahr>", methods=["GET"])
def get_planungsstand(jahr):
    """
    Planungsstand für ein Zieljahr: Parameter + Status + gespeicherte Ziele.
    Beim Seitenaufruf laden, um Formular und Tabelle wiederherzustellen.
    """
    stand = _get_planungsstand(jahr)
    ziele = _get_gespeicherte_ziele(jahr)
    try:
        ref_jahr = stand["referenz_jahr"] if stand else max(2024, jahr - 1)
        referenz = _stueckzahl_fuer_jahr(ref_jahr)
        names = {d["mitarbeiter_nr"]: d.get("name") or "" for d in referenz}
        for z in ziele:
            z["name"] = names.get(z["mitarbeiter_nr"], "") or f"Verkäufer #{z['mitarbeiter_nr']}"
    except Exception:
        for z in ziele:
            z["name"] = z.get("name") or f"Verkäufer #{z['mitarbeiter_nr']}"
    return jsonify({
        "success": True,
        "jahr": jahr,
        "planungsstand": stand,
        "ziele": ziele,
        "gespeichert": len(ziele) > 0,
    })


@verkaeufer_zielplanung_bp.route("/planungsstand/<int:jahr>/freigeben", methods=["POST"])
def freigeben_planung(jahr):
    """Planung für ein Jahr freigeben. Nur wenn Status bisher 'entwurf'. Ab dann wirksam für Monatsziele/Auftragseingang."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Nicht angemeldet"}), 401
    stand = _get_planungsstand(jahr)
    if not stand:
        return jsonify({"success": False, "error": "Kein Planungsstand für dieses Jahr. Bitte zuerst Ziele speichern."}), 400
    if stand.get("status") == "freigegeben":
        return jsonify({"success": True, "message": "Planung war bereits freigegeben.", "status": "freigegeben"})
    user = getattr(current_user, "username", None) or getattr(current_user, "name", None) or str(current_user.id)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE zielplanung_stand
            SET status = 'freigegeben', freigegeben_am = CURRENT_TIMESTAMP, freigegeben_von = %s
            WHERE kalenderjahr = %s
            """,
            (user, jahr),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "jahr": jahr, "message": "Planung freigegeben – Ziele sind jetzt verbindlich.", "status": "freigegeben"})
    except Exception as e:
        if "does not exist" in str(e).lower():
            return jsonify({"success": False, "error": "Tabelle zielplanung_stand fehlt. Bitte Migration ausführen."}), 503
        logger.exception("Planung freigeben %s: %s", jahr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/pool", methods=["GET"])
def get_pool():
    """Konfiguration Pool Handelsgeschäft und NW-Marken-Regeln."""
    return jsonify(
        {
            "pool_mitarbeiter_nrn": POOL_HANDELSGESCHAEFT,
            "beschreibung": "Diese Verkäufer werden von der Zielverteilung ausgenommen; ihre Verkäufe werden vom Konzernziel abgezogen.",
            "nw_hyundai_verkaeufer": NW_HYUNDAI_VERKAEUFER,
            "nw_hyundai_beschreibung": "NW Hyundai-Ziele werden nur auf diese Verkäufer (Roland, Edeltraud) verteilt.",
            "nw_opel_beschreibung": "NW Opel-Ziele werden auf alle Verkäufer außer Pool und außer die Hyundai-Verkäufer verteilt.",
            "nw_leapmotor_beschreibung": "NW Leapmotor-Ziele werden auf alle Verkäufer (außer Pool) verteilt.",
        }
    )


@verkaeufer_zielplanung_bp.route("/ziele/<int:jahr>", methods=["GET"])
def get_ziele(jahr):
    """Gespeicherte Ziele für ein Kalenderjahr. Leer wenn noch keine gespeichert."""
    ziele = _get_gespeicherte_ziele(jahr)
    # Namen aus Referenz-Stückzahl ergänzen (gleiche Verkäufer-Struktur)
    try:
        referenz = _stueckzahl_fuer_jahr(max(2024, jahr - 1))
        names = {d["mitarbeiter_nr"]: d.get("name") or "" for d in referenz}
        for z in ziele:
            z["name"] = names.get(z["mitarbeiter_nr"], "") or f"Verkäufer #{z['mitarbeiter_nr']}"
    except Exception:
        for z in ziele:
            z["name"] = z.get("name") or f"Verkäufer #{z['mitarbeiter_nr']}"
    return jsonify({
        "success": True,
        "jahr": jahr,
        "gespeichert": len(ziele) > 0,
        "ziele": ziele,
    })


@verkaeufer_zielplanung_bp.route("/verkaeufer/<int:mitarbeiter_nr>", methods=["GET"])
def verkaeufer_detail(mitarbeiter_nr):
    """
    Detail für einen Verkäufer: Vorjahr (IST), Planungsvorschlag, ggf. gespeicherte Ziele.
    Für Planungsgespräch – nur diese Person, keine anderen Daten.
    Query: jahr, referenz_jahr (optional), ziel_nw, ziel_gw (für Vorschlag).
    """
    jahr = request.args.get("jahr", type=int) or 2026
    referenz_jahr = request.args.get("referenz_jahr", type=int) or max(2024, jahr - 1)
    ziel_nw = request.args.get("ziel_nw", type=int) or 630
    ziel_gw = request.args.get("ziel_gw", type=int) or 900
    try:
        referenz_daten = _stueckzahl_fuer_jahr(referenz_jahr)
        person = next((d for d in referenz_daten if d["mitarbeiter_nr"] == mitarbeiter_nr), None)
        if not person:
            return jsonify({"success": False, "error": "Verkäufer nicht gefunden"}), 404
        verteilung = _verteilung_berechnen(
            referenz_daten, ziel_nw, ziel_gw,
            ziel_nw_hyundai=None, ziel_nw_opel=None, ziel_nw_leapmotor=None,
        )
        vorschlag = next((v for v in verteilung.get("verkaeufer", []) if v["mitarbeiter_nr"] == mitarbeiter_nr), None)
        gespeichert_liste = _get_gespeicherte_ziele(jahr)
        gespeichert = next((z for z in gespeichert_liste if z["mitarbeiter_nr"] == mitarbeiter_nr), None)
        return jsonify({
            "success": True,
            "mitarbeiter_nr": mitarbeiter_nr,
            "name": person.get("name") or f"Verkäufer #{mitarbeiter_nr}",
            "standort": person.get("standort") or "",
            "jahr": jahr,
            "referenz_jahr": referenz_jahr,
            "vorjahr": {"nw": person.get("nw_stueck") or 0, "gw": person.get("gw_stueck") or 0},
            "vorschlag": {
                "ziel_nw": vorschlag.get("ziel_nw") if vorschlag else 0,
                "ziel_gw": vorschlag.get("ziel_gw") if vorschlag else 0,
            } if vorschlag else {"ziel_nw": 0, "ziel_gw": 0},
            "gespeichert": {
                "ziel_nw": gespeichert["ziel_nw"],
                "ziel_gw": gespeichert["ziel_gw"],
                "planungsgespraech_am": gespeichert.get("planungsgespraech_am"),
                "planungsgespraech_notiz": gespeichert.get("planungsgespraech_notiz"),
            } if gespeichert else None,
        })
    except Exception as e:
        logger.exception("Verkäufer-Detail %s: %s", mitarbeiter_nr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/ziele/<int:jahr>/verkaeufer/<int:mitarbeiter_nr>", methods=["PUT"])
def save_verkaeufer_ziel(jahr, mitarbeiter_nr):
    """Nur diesen Verkäufer speichern (für Detailansicht / Planungsgespräch). Body: ziel_nw, ziel_gw, planungsgespraech_am?, planungsgespraech_notiz?."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Nicht angemeldet"}), 401
    data = request.get_json(force=True, silent=True) or {}
    zn = int(data.get("ziel_nw") or 0)
    zg = int(data.get("ziel_gw") or 0)
    pdatum = (data.get("planungsgespraech_am") or "").strip()
    pnotiz = (data.get("planungsgespraech_notiz") or "").strip() or None
    if pdatum and len(pdatum) > 10:
        pdatum = pdatum[:10]
    user = getattr(current_user, "username", None) or getattr(current_user, "name", None) or str(current_user.id)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO verkaeufer_ziele (kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw, planungsgespraech_am, planungsgespraech_notiz, gespeichert_von, gespeichert_am)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (kalenderjahr, mitarbeiter_nr)
            DO UPDATE SET ziel_nw = EXCLUDED.ziel_nw, ziel_gw = EXCLUDED.ziel_gw,
                          planungsgespraech_am = EXCLUDED.planungsgespraech_am,
                          planungsgespraech_notiz = EXCLUDED.planungsgespraech_notiz,
                          gespeichert_von = EXCLUDED.gespeichert_von, gespeichert_am = CURRENT_TIMESTAMP
            """,
            (jahr, mitarbeiter_nr, zn, zg, pdatum or None, pnotiz, user),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ziele gespeichert – sie sind wirksam."})
    except Exception as e:
        if "does not exist" in str(e).lower():
            return jsonify({"success": False, "error": "Tabelle verkaeufer_ziele fehlt."}), 503
        logger.exception("Ziel speichern Verkäufer %s: %s", mitarbeiter_nr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/ziele/<int:jahr>", methods=["POST"])
def save_ziele(jahr):
    """
    Ziele für ein Kalenderjahr speichern (Entwurf). Schreibt auch Planungsstand mit Status 'entwurf'.
    Body: { ziele: [...], optional: referenz_jahr, konzernziel_nw, konzernziel_gw, ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor }.
    """
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Nicht angemeldet"}), 401
    data = request.get_json(force=True, silent=True) or {}
    ziele = data.get("ziele") or []
    if not isinstance(ziele, list):
        return jsonify({"success": False, "error": "ziele muss eine Liste sein"}), 400
    user = getattr(current_user, "username", None) or getattr(current_user, "name", None) or str(current_user.id)
    # Planungsparameter (optional) für zielplanung_stand
    ref_jahr = data.get("referenz_jahr")
    ref_jahr = int(ref_jahr) if ref_jahr is not None else max(2024, jahr - 1)
    konzern_nw = int(data.get("konzernziel_nw", 0) or 0)
    konzern_gw = int(data.get("konzernziel_gw", 0) or 0)
    zn_hy = data.get("ziel_nw_hyundai")
    zn_op = data.get("ziel_nw_opel")
    zn_lm = data.get("ziel_nw_leapmotor")
    zn_hy = int(zn_hy) if zn_hy not in (None, "") else None
    zn_op = int(zn_op) if zn_op not in (None, "") else None
    zn_lm = int(zn_lm) if zn_lm not in (None, "") else None
    try:
        conn = get_db()
        cur = conn.cursor()
        for z in ziele:
            nr = z.get("mitarbeiter_nr")
            if nr is None:
                continue
            zn = int(z.get("ziel_nw") or 0)
            zg = int(z.get("ziel_gw") or 0)
            pdatum = z.get("planungsgespraech_am")
            pnotiz = (z.get("planungsgespraech_notiz") or "").strip() or None
            if pdatum and len(pdatum) > 10:
                pdatum = pdatum[:10]
            cur.execute(
                """
                INSERT INTO verkaeufer_ziele (kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw, planungsgespraech_am, planungsgespraech_notiz, gespeichert_von, gespeichert_am)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (kalenderjahr, mitarbeiter_nr)
                DO UPDATE SET ziel_nw = EXCLUDED.ziel_nw, ziel_gw = EXCLUDED.ziel_gw,
                              planungsgespraech_am = EXCLUDED.planungsgespraech_am,
                              planungsgespraech_notiz = EXCLUDED.planungsgespraech_notiz,
                              gespeichert_von = EXCLUDED.gespeichert_von, gespeichert_am = CURRENT_TIMESTAMP
                """,
                (jahr, nr, zn, zg, pdatum if pdatum else None, pnotiz, user),
            )
        # Planungsstand upserten (Status bleibt entwurf; bei bereits freigegeben nicht überschreiben)
        cur.execute(
            """
            INSERT INTO zielplanung_stand (kalenderjahr, referenz_jahr, konzernziel_nw, konzernziel_gw,
                ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor, status, zuletzt_gespeichert_am, zuletzt_gespeichert_von)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'entwurf', CURRENT_TIMESTAMP, %s)
            ON CONFLICT (kalenderjahr) DO UPDATE SET
                referenz_jahr = EXCLUDED.referenz_jahr,
                konzernziel_nw = EXCLUDED.konzernziel_nw,
                konzernziel_gw = EXCLUDED.konzernziel_gw,
                ziel_nw_hyundai = EXCLUDED.ziel_nw_hyundai,
                ziel_nw_opel = EXCLUDED.ziel_nw_opel,
                ziel_nw_leapmotor = EXCLUDED.ziel_nw_leapmotor,
                zuletzt_gespeichert_am = CURRENT_TIMESTAMP,
                zuletzt_gespeichert_von = EXCLUDED.zuletzt_gespeichert_von
            WHERE zielplanung_stand.status = 'entwurf'
            """,
            (jahr, ref_jahr, konzern_nw, konzern_gw, zn_hy, zn_op, zn_lm, user),
        )
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "jahr": jahr,
            "message": "Entwurf gespeichert. Noch nicht freigegeben – für Monatsziele/Auftragseingang bitte „Planung freigeben“ klicken.",
        })
    except Exception as e:
        if "does not exist" in str(e).lower():
            return jsonify({"success": False, "error": "Tabelle verkaeufer_ziele oder zielplanung_stand fehlt. Bitte Migrationen ausführen."}), 503
        logger.exception("Ziele speichern für %s: %s", jahr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/stueckzahl/<int:jahr>", methods=["GET"])
def stueckzahl(jahr):
    """Stückzahl pro Verkäufer (NW/GW) für Kalenderjahr aus Locosoft. Pool-Mitglieder ans Ende sortiert."""
    try:
        data = _stueckzahl_fuer_jahr(jahr)
        data = sorted(data, key=lambda d: d.get("ist_handelsgeschaeft", False))
        gesamt_nw = sum(d["nw_stueck"] for d in data)
        gesamt_gw = sum(d["gw_stueck"] for d in data)
        return jsonify(
            {
                "success": True,
                "jahr": jahr,
                "verkaeufer": data,
                "gesamt": {"nw": gesamt_nw, "gw": gesamt_gw, "summe": gesamt_nw + gesamt_gw},
            }
        )
    except Exception as e:
        logger.exception("Stückzahl für Jahr %s: %s", jahr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/verteilung", methods=["GET"])
def verteilung():
    """
    Ziele verteilt nach Referenzjahr. NW nach Marken:
    - ziel_nw_hyundai: nur auf Roland (2006) und Edeltraud (2001)
    - ziel_nw_opel: nur auf Verkäufer außer 2001, 2006
    - ziel_nw_leapmotor: auf alle (außer Pool)
    Optional: ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor (sonst aus ziel_nw nach Referenz-Anteil).
    """
    ziel_jahr = request.args.get("ziel_jahr", type=int) or 2026
    referenz_jahr = request.args.get("referenz_jahr", type=int) or 2025
    ziel_nw = request.args.get("ziel_nw", type=int) or 630
    ziel_gw = request.args.get("ziel_gw", type=int) or 900
    ziel_nw_hyundai = request.args.get("ziel_nw_hyundai", type=int)
    ziel_nw_opel = request.args.get("ziel_nw_opel", type=int)
    ziel_nw_leapmotor = request.args.get("ziel_nw_leapmotor", type=int)

    try:
        referenz_daten = _stueckzahl_fuer_jahr(referenz_jahr)
        result = _verteilung_berechnen(
            referenz_daten,
            ziel_nw,
            ziel_gw,
            ziel_nw_hyundai=ziel_nw_hyundai if ziel_nw_hyundai is not None else None,
            ziel_nw_opel=ziel_nw_opel if ziel_nw_opel is not None else None,
            ziel_nw_leapmotor=ziel_nw_leapmotor if ziel_nw_leapmotor is not None else None,
        )
        # Pool-Mitglieder ans Ende (falls noch nicht durch _verteilung_berechnen)
        result["verkaeufer"] = sorted(
            result["verkaeufer"], key=lambda v: v.get("ist_handelsgeschaeft", False)
        )
        result["ziel_jahr"] = ziel_jahr
        result["referenz_jahr"] = referenz_jahr
        return jsonify({"success": True, **result})
    except Exception as e:
        logger.exception("Verteilung: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/saisonalitaet/<int:jahr>", methods=["GET"])
def saisonalitaet(jahr):
    """Monatsverteilung NW/GW aus Referenzjahr (Anteile in %). Gleiche Logik wie Stückzahl (Vertragsdatum, Dedup)."""
    try:
        data = _saisonalitaet_fuer_jahr(jahr)
        return jsonify({"success": True, **data})
    except Exception as e:
        logger.exception("Saisonalität für Jahr %s: %s", jahr, e)
        return jsonify({"success": False, "error": str(e)}), 500


@verkaeufer_zielplanung_bp.route("/monatsverteilung", methods=["GET"])
def monatsverteilung():
    """Ziele auf 12 Monate verteilt gemäß Saisonalität eines Referenzjahrs. Query: referenz_jahr, ziel_nw, ziel_gw."""
    referenz_jahr = request.args.get("referenz_jahr", type=int) or 2025
    ziel_nw = request.args.get("ziel_nw", type=int) or 0
    ziel_gw = request.args.get("ziel_gw", type=int) or 0
    try:
        saison = _saisonalitaet_fuer_jahr(referenz_jahr)
        monate = _monatsverteilung_aus_saisonalitaet(ziel_nw, ziel_gw, saison)
        return jsonify({
            "success": True,
            "referenz_jahr": referenz_jahr,
            "ziel_nw": ziel_nw,
            "ziel_gw": ziel_gw,
            "monate": monate,
        })
    except Exception as e:
        logger.exception("Monatsverteilung: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


def get_monatsziele_konzern_dict(
    jahr: int,
    monat: int,
    referenz_jahr: int | None = None,
    ziel_nw: int = 630,
    ziel_gw: int = 900,
) -> dict:
    """
    SSOT für Konzern-Monatsziele (gleiche Logik wie HTTP /monatsziele).
    Rückgabe: dict mit success, ziel_nw_konzern, ziel_gw_konzern, …
    """
    if not jahr or not monat or monat < 1 or monat > 12:
        return {"success": False, "error": "jahr und monat (1–12) erforderlich"}
    referenz_jahr = referenz_jahr or max(2024, jahr - 1)
    saison = _saisonalitaet_fuer_jahr(referenz_jahr)
    monate = saison.get("monate", [])
    if len(monate) < monat:
        return {"success": False, "error": "Saisonalität unvollständig"}
    m = monate[monat - 1]
    nw_pct = m.get("nw_pct") or 0
    gw_pct = m.get("gw_pct") or 0

    planstand = _get_planungsstand(jahr)
    gespeichert = _get_gespeicherte_ziele(jahr) if (planstand and planstand.get("status") == "freigegeben") else []
    if gespeichert:
        referenz_daten = _stueckzahl_fuer_jahr(referenz_jahr)
        names = {d["mitarbeiter_nr"]: d.get("name") or "" for d in referenz_daten}
        ziele = []
        ziel_nw_konzern = 0
        ziel_gw_konzern = 0
        for v in gespeichert:
            zn = math.floor((v.get("ziel_nw") or 0) * nw_pct / 100 + 0.5)
            zg = math.floor((v.get("ziel_gw") or 0) * gw_pct / 100 + 0.5)
            ziele.append({
                "mitarbeiter_nr": v["mitarbeiter_nr"],
                "name": names.get(v["mitarbeiter_nr"], "") or f"Verkäufer #{v['mitarbeiter_nr']}",
                "ziel_nw": zn,
                "ziel_gw": zg,
            })
            ziel_nw_konzern += zn
            ziel_gw_konzern += zg
        return {
            "success": True,
            "jahr": jahr,
            "monat": monat,
            "referenz_jahr": referenz_jahr,
            "aus_gespeicherten_zielen": True,
            "ziel_nw_konzern": ziel_nw_konzern,
            "ziel_gw_konzern": ziel_gw_konzern,
            "ziele": ziele,
        }

    referenz_daten = _stueckzahl_fuer_jahr(referenz_jahr)
    verteilung = _verteilung_berechnen(
        referenz_daten, ziel_nw, ziel_gw,
        ziel_nw_hyundai=None, ziel_nw_opel=None, ziel_nw_leapmotor=None,
    )
    ziele = []
    ziel_nw_konzern = 0
    ziel_gw_konzern = 0
    for v in verteilung.get("verkaeufer", []):
        zn = math.floor((v.get("ziel_nw") or 0) * nw_pct / 100 + 0.5)
        zg = math.floor((v.get("ziel_gw") or 0) * gw_pct / 100 + 0.5)
        ziele.append({
            "mitarbeiter_nr": v["mitarbeiter_nr"],
            "name": v.get("name") or "",
            "ziel_nw": zn,
            "ziel_gw": zg,
        })
        ziel_nw_konzern += zn
        ziel_gw_konzern += zg
    return {
        "success": True,
        "jahr": jahr,
        "monat": monat,
        "referenz_jahr": referenz_jahr,
        "aus_gespeicherten_zielen": False,
        "ziel_nw_konzern": ziel_nw_konzern,
        "ziel_gw_konzern": ziel_gw_konzern,
        "ziele": ziele,
    }


@verkaeufer_zielplanung_bp.route("/monatsziele", methods=["GET"])
def monatsziele():
    """
    Monatsziele für Zielerfüllung (z. B. Auftragseingang).
    Nutzt gespeicherte Ziele (verkaeufer_ziele) für jahr, falls vorhanden; sonst Verteilung × Saisonalität.
    """
    jahr = request.args.get("jahr", type=int)
    monat = request.args.get("monat", type=int)
    if not jahr or not monat or monat < 1 or monat > 12:
        return jsonify({"success": False, "error": "jahr und monat (1–12) erforderlich"}), 400
    referenz_jahr = request.args.get("referenz_jahr", type=int) or max(2024, jahr - 1)
    ziel_nw = request.args.get("ziel_nw", type=int) or 630
    ziel_gw = request.args.get("ziel_gw", type=int) or 900
    try:
        data = get_monatsziele_konzern_dict(jahr, monat, referenz_jahr, ziel_nw, ziel_gw)
        if not data.get("success"):
            err = data.get("error", "")
            code = 500 if "Saisonalität" in err else 400
            return jsonify(data), code
        return jsonify(data)
    except Exception as e:
        logger.exception("Monatsziele: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
