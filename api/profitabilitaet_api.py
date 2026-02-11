"""
Profitabilitäts-API (TAG 219)
REST-Endpoints für das Profitabilitäts-Dashboard.
"""

import logging
from flask import Blueprint, jsonify, request

from api.profitabilitaet_data import ProfitabilitaetData

logger = logging.getLogger(__name__)

profitabilitaet_api = Blueprint(
    "profitabilitaet_api",
    __name__,
    url_prefix="/api/profitabilitaet",
)


def _parse_params():
    """Monat, Jahr, Standort aus Request lesen."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    standort = request.args.get("standort", type=int)
    typ = request.args.get("typ", type=str)
    if typ == "":
        typ = None
    return month, year, standort, typ


@profitabilitaet_api.route("/fahrzeuge", methods=["GET"])
def get_fahrzeuge():
    """
    GET /api/profitabilitaet/fahrzeuge?month=2&year=2026&standort=1&typ=G
    Einzelfahrzeuge mit Profitabilitäts-Kalkulation.
    """
    try:
        month, year, standort, typ = _parse_params()
        if not month or not year:
            return jsonify({"success": False, "error": "month und year erforderlich"}), 400
        result = ProfitabilitaetData.get_verkaufte_fahrzeuge_profitabilitaet(
            month, year, standort=standort, fahrzeugtyp=typ
        )
        if not result.get("success"):
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        logger.exception("GET /api/profitabilitaet/fahrzeuge: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@profitabilitaet_api.route("/summary", methods=["GET"])
def get_summary():
    """
    GET /api/profitabilitaet/summary?month=2&year=2026&standort=1
    Aggregierte KPIs.
    """
    try:
        month, year, standort, _ = _parse_params()
        if not month or not year:
            return jsonify({"success": False, "error": "month und year erforderlich"}), 400
        result = ProfitabilitaetData.get_profitabilitaet_summary(month, year, standort=standort)
        if not result.get("success"):
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        logger.exception("GET /api/profitabilitaet/summary: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@profitabilitaet_api.route("/verkaeufer", methods=["GET"])
def get_verkaeufer():
    """
    GET /api/profitabilitaet/verkaeufer?month=2&year=2026&standort=1
    Verkäufer-Ranking nach DB netto.
    """
    try:
        month, year, standort, _ = _parse_params()
        if not month or not year:
            return jsonify({"success": False, "error": "month und year erforderlich"}), 400
        result = ProfitabilitaetData.get_verkaeufer_profitabilitaet(month, year, standort=standort)
        if not result.get("success"):
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        logger.exception("GET /api/profitabilitaet/verkaeufer: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@profitabilitaet_api.route("/trend", methods=["GET"])
def get_trend():
    """
    GET /api/profitabilitaet/trend?year=2026&standort=1
    12-Monats-Trend für Charts.
    """
    try:
        year = request.args.get("year", type=int)
        standort = request.args.get("standort", type=int)
        if not year:
            return jsonify({"success": False, "error": "year erforderlich"}), 400
        result = ProfitabilitaetData.get_profitabilitaet_trend(year, standort=standort)
        if not result.get("success"):
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        logger.exception("GET /api/profitabilitaet/trend: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@profitabilitaet_api.route("/health", methods=["GET"])
def health():
    """GET /api/profitabilitaet/health – Health-Check."""
    try:
        from datetime import datetime
        result = ProfitabilitaetData.get_profitabilitaet_summary(
            datetime.now().month, datetime.now().year, standort=None
        )
        return jsonify({
            "status": "ok",
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.exception("GET /api/profitabilitaet/health: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
