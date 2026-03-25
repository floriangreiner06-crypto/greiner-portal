"""
VKL-Verkaufsdashboard – Aggregiert bestehende SSOT-Quellen (keine parallele Fachlogik).
"""
from __future__ import annotations

import copy
import logging
import threading
import time
from datetime import date, datetime
from typing import Any, Dict, Optional

from api.bankenspiegel_api import build_einkaufsfinanzierung_top_und_warnungen
from api.db_utils import db_session
from api.serviceberater_api import get_werktage_monat
from api.verkaeufer_zielplanung_api import _get_planungsstand, get_monatsziele_konzern_dict
from api.verkauf_data import VerkaufData

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 60
_payload_cache: dict[tuple[bool, bool, str], tuple[float, Dict[str, Any]]] = {}
_payload_cache_lock = threading.Lock()


def _pct(n: float, d: float) -> Optional[float]:
    if d and d > 0:
        return round(100.0 * n / d, 1)
    return None


def _ampel_trend(pct: Optional[float]) -> str:
    if pct is None:
        return "unknown"
    if pct >= 100:
        return "green"
    if pct >= 90:
        return "yellow"
    return "red"


def _month_iter(start: date, end: date):
    y, m = start.year, start.month
    while (y < end.year) or (y == end.year and m <= end.month):
        yield y, m
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1


def _ytd_window(now: date, mode: str) -> tuple[date, str]:
    if mode == "fiscal":
        if now.month >= 9:
            start = date(now.year, 9, 1)
        else:
            start = date(now.year - 1, 9, 1)
        return start, "Geschaeftsjahr"
    return date(now.year, 1, 1), "Kalenderjahr"


def build_vkl_dashboard_payload(
    *,
    include_afa: bool,
    include_ekf: bool,
    ytd_mode: str = "calendar",
) -> Dict[str, Any]:
    cache_key = (bool(include_afa), bool(include_ekf), (ytd_mode or "calendar").lower())
    now_ts = time.time()
    with _payload_cache_lock:
        cached = _payload_cache.get(cache_key)
        if cached and now_ts - cached[0] <= _CACHE_TTL_SECONDS:
            return copy.deepcopy(cached[1])

    now_dt = datetime.now()
    today = now_dt.date()
    jahr, monat = now_dt.year, now_dt.month
    referenz_jahr = max(2024, jahr - 1)

    ytd_mode = (ytd_mode or "calendar").lower()
    if ytd_mode not in {"calendar", "fiscal"}:
        ytd_mode = "calendar"
    ytd_start, ytd_label = _ytd_window(today, ytd_mode)

    planstand = _get_planungsstand(jahr)
    ziel_nw = int((planstand.get("konzernziel_nw") or 630) if planstand else 630)
    ziel_gw = int((planstand.get("konzernziel_gw") or 900) if planstand else 900)

    ae_m = VerkaufData.get_auftragseingang_segments(month=monat, year=jahr, ytd=False)
    al_m = VerkaufData.get_auslieferung_segments(month=monat, year=jahr, ytd=False)

    ae_ytd = VerkaufData.get_auftragseingang_segments_range(
        start_date=ytd_start.isoformat(), end_date=today.isoformat()
    )
    al_ytd = VerkaufData.get_auslieferung_segments_range(
        start_date=ytd_start.isoformat(), end_date=today.isoformat()
    )

    ae_marken = VerkaufData.get_auftragseingang_marken_split(month=monat, year=jahr, ytd=False)
    db_marken = VerkaufData.get_db_marken_split_monat(month=monat, year=jahr)
    forecast_offen = VerkaufData.get_offene_auftraege_forecast()

    mz = get_monatsziele_konzern_dict(jahr, monat, referenz_jahr, ziel_nw, ziel_gw)
    if not mz.get("success"):
        mz = {
            "success": False,
            "ziel_nw_konzern": 0,
            "ziel_gw_konzern": 0,
            "aus_gespeicherten_zielen": False,
            "error": mz.get("error"),
        }

    wt = get_werktage_monat(jahr, monat)
    wg = max(int(wt.get("gesamt") or 0), 1)
    wv = int(wt.get("vergangen") or 0)
    ziel_nw_monat = int(mz.get("ziel_nw_konzern") or 0)
    ziel_gw_monat = int(mz.get("ziel_gw_konzern") or 0)
    ziel_nw_bis_heute = ziel_nw_monat * wv / wg
    ziel_gw_bis_heute = ziel_gw_monat * wv / wg

    ist_nw = int(ae_m.get("stueck_nw") or 0) if ae_m.get("success") else 0
    ist_gw = int(ae_m.get("stueck_gw") or 0) if ae_m.get("success") else 0

    pct_nw_kal = _pct(ist_nw, ziel_nw_monat)
    pct_gw_kal = _pct(ist_gw, ziel_gw_monat)
    pct_nw_trend = _pct(ist_nw, ziel_nw_bis_heute)
    pct_gw_trend = _pct(ist_gw, ziel_gw_bis_heute)

    ytd_nw_ziel = 0.0
    ytd_gw_ziel = 0.0
    for y, m in _month_iter(ytd_start, today):
        ps = _get_planungsstand(y)
        z_nw = int((ps.get("konzernziel_nw") or 630) if ps else 630)
        z_gw = int((ps.get("konzernziel_gw") or 900) if ps else 900)
        ref = max(2024, y - 1)

        mm = get_monatsziele_konzern_dict(y, m, ref, z_nw, z_gw)
        if not mm.get("success"):
            continue
        wtm = get_werktage_monat(y, m)
        gg = max(int(wtm.get("gesamt") or 0), 1)
        if y == today.year and m == today.month:
            anteil = int(wtm.get("vergangen") or 0) / gg
        else:
            anteil = 1.0
        ytd_nw_ziel += (mm.get("ziel_nw_konzern") or 0) * anteil
        ytd_gw_ziel += (mm.get("ziel_gw_konzern") or 0) * anteil

    ytd_ist_nw = int(ae_ytd.get("stueck_nw") or 0) if ae_ytd.get("success") else 0
    ytd_ist_gw = int(ae_ytd.get("stueck_gw") or 0) if ae_ytd.get("success") else 0
    pct_ytd_nw_trend = _pct(ytd_ist_nw, ytd_nw_ziel)
    pct_ytd_gw_trend = _pct(ytd_ist_gw, ytd_gw_ziel)

    out: Dict[str, Any] = {
        "success": True,
        "stand": {"jahr": jahr, "monat": monat, "referenz_jahr": referenz_jahr},
        "ytd": {
            "mode": ytd_mode,
            "label": ytd_label,
            "start": ytd_start.isoformat(),
            "ende": today.isoformat(),
        },
        "auftragseingang_monat": ae_m if ae_m.get("success") else {"success": False, "error": ae_m.get("error")},
        "auftragseingang_ytd": ae_ytd if ae_ytd.get("success") else {},
        "auslieferung_monat": al_m if al_m.get("success") else {"success": False},
        "auslieferung_ytd": al_ytd if al_ytd.get("success") else {},
        "auftragseingang_marken": ae_marken if ae_marken.get("success") else {"success": False, "marken": []},
        "db_marken_monat": db_marken if db_marken.get("success") else {"success": False, "marken": []},
        "forecast_offen": forecast_offen if forecast_offen.get("success") else {"success": False, "anzahl": 0, "marken": []},
        "ziele_monat": {
            "ziel_nw_konzern": ziel_nw_monat,
            "ziel_gw_konzern": ziel_gw_monat,
            "aus_gespeicherten_zielen": mz.get("aus_gespeicherten_zielen"),
            "werktage_monat_gesamt": wt.get("gesamt"),
            "werktage_monat_vergangen": wt.get("vergangen"),
            "ziel_nw_bis_heute_werktag": round(ziel_nw_bis_heute, 2),
            "ziel_gw_bis_heute_werktag": round(ziel_gw_bis_heute, 2),
            "ist_nw": ist_nw,
            "ist_gw": ist_gw,
            "pct_nw_zum_monatsziel": pct_nw_kal,
            "pct_gw_zum_monatsziel": pct_gw_kal,
            "pct_nw_trend_werktag": pct_nw_trend,
            "pct_gw_trend_werktag": pct_gw_trend,
            "ampel_nw": _ampel_trend(pct_nw_trend),
            "ampel_gw": _ampel_trend(pct_gw_trend),
        },
        "ziele_jahr_klein": {
            "ist_nw_ytd": ytd_ist_nw,
            "ist_gw_ytd": ytd_ist_gw,
            "soll_nw_ytd_werktag": round(ytd_nw_ziel, 2),
            "soll_gw_ytd_werktag": round(ytd_gw_ziel, 2),
            "pct_nw_trend": pct_ytd_nw_trend,
            "pct_gw_trend": pct_ytd_gw_trend,
        },
    }

    if include_afa:
        try:
            from api.afa_api import STANDZEIT_ZWANG_VERMARKTUNG_TAGE, _get_verkaufsempfehlungen_liste

            liste = _get_verkaufsempfehlungen_liste()
            brennend = sum(
                1
                for x in liste
                if (x.get("standzeit_tage") is not None and x.get("standzeit_tage") > STANDZEIT_ZWANG_VERMARKTUNG_TAGE)
            )
            out["afa"] = {
                "standzeit_grenze_tage": STANDZEIT_ZWANG_VERMARKTUNG_TAGE,
                "anzahl_standzeit_darueber": brennend,
                "gesamt_empfehlungen": len(liste),
            }
        except Exception as e:
            logger.exception("VKL-Dashboard AfA: %s", e)
            out["afa"] = {"error": str(e)}

    if include_ekf:
        try:
            with db_session() as conn:
                cur = conn.cursor()
                top10, warnungen = build_einkaufsfinanzierung_top_und_warnungen(cur, top_limit=10)
            kritisch = sum(1 for w in warnungen if w.get("kritisch"))
            out["einkaufsfinanzierung"] = {
                "top_zinsverursacher": top10,
                "warnungen_anzahl": len(warnungen),
                "warnungen_kritisch_anzahl": kritisch,
                "warnungen_preview": warnungen[:5],
            }
        except Exception as e:
            logger.exception("VKL-Dashboard EKF: %s", e)
            out["einkaufsfinanzierung"] = {"error": str(e)}

    with _payload_cache_lock:
        _payload_cache[cache_key] = (time.time(), out)
    return copy.deepcopy(out)
