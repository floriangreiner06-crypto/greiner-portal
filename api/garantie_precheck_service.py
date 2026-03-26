"""
Garantie-Precheck Service (regelbasiert + KI-Cache)
===================================================
Hintergrundprüfung für Garantieaufträge, Ergebnisse in Redis gecacht.
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from api.cache_utils import get_redis_client

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "garantie:precheck:"
_CACHE_TTL_SECONDS = 60 * 60 * 12  # 12h

# Falls je Marke abweichend, hier zentral pflegen.
_FRIST_DAYS_BY_MARKE = {
    "stellantis": 21,
    "hyundai": 21,
    "leapmotor": 21,
    "allgemein": 21,
}


def _marke_key(marke: Optional[str], betrieb: Optional[int] = None) -> str:
    m = (marke or "").strip().lower()
    if "opel" in m or "stellantis" in m:
        return "stellantis"
    if "hyundai" in m:
        return "hyundai"
    if "leapmotor" in m:
        return "leapmotor"
    # Fallback über Betrieb
    if betrieb in (1, 3):
        return "stellantis"
    if betrieb == 2:
        return "hyundai"
    return "allgemein"


def _parse_order_date(order_date: Any) -> Optional[date]:
    if isinstance(order_date, datetime):
        return order_date.date()
    if isinstance(order_date, date):
        return order_date
    if not order_date:
        return None
    text = str(order_date)
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _base_precheck(auftrag: Dict[str, Any]) -> Dict[str, Any]:
    marke = _marke_key(auftrag.get("marke"), auftrag.get("betrieb"))
    frist_tage = _FRIST_DAYS_BY_MARKE.get(marke, 21)
    order_dt = _parse_order_date(auftrag.get("order_date"))
    frist_bis = order_dt + timedelta(days=frist_tage) if order_dt else None
    resttage = (frist_bis - date.today()).days if frist_bis else None
    if resttage is None:
        frist_status = "unbekannt"
    elif resttage < 0:
        frist_status = "rot"
    elif resttage <= 3:
        frist_status = "gelb"
    else:
        frist_status = "gruen"

    akte_exists = bool(((auftrag.get("garantieakte") or {}).get("existiert")))
    gudat_ok = bool(auftrag.get("gudat_dossier_gefunden"))

    emp = []
    if not akte_exists:
        emp.append("Garantieakte anlegen")
    if not gudat_ok:
        emp.append("Gudat-Dossier prüfen")
    if frist_status == "rot":
        emp.append("Frist überzogen: sofort Priorität")
    elif frist_status == "gelb":
        emp.append("Frist naht: zeitnah einreichen")
    if not emp:
        emp.append("Dokumentation prüfen und einreichen")

    return {
        "status": "vorpruefung",
        "marke": marke,
        "frist_bis": frist_bis.isoformat() if frist_bis else None,
        "resttage": resttage,
        "frist_status": frist_status,
        "fristen_bewertung": (
            "Frist nicht bestimmbar" if resttage is None else
            "Frist überzogen" if resttage < 0 else
            f"Noch {resttage} Tage"
        ),
        "ki_empfehlung_kurz": "; ".join(emp[:2]),
        "ki_empfehlung_lang": "; ".join(emp),
        "ki_quelle": "regelbasiert",
        "last_checked_at": datetime.now().isoformat(),
    }


def is_ai_candidate(auftrag: Dict[str, Any], threshold_days: int = 7) -> bool:
    """
    KI nur für priorisierte Aufträge:
    - Garantieakte existiert
    - Frist nah/überfällig (resttage <= threshold_days)
    """
    akte_exists = bool(((auftrag.get("garantieakte") or {}).get("existiert")))
    if not akte_exists:
        return False
    basis = _base_precheck(auftrag)
    resttage = basis.get("resttage")
    return resttage is not None and resttage <= int(threshold_days)


def get_cached_precheck(order_number: int) -> Optional[Dict[str, Any]]:
    redis_client = get_redis_client()
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(f"{_CACHE_PREFIX}{int(order_number)}")
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.debug("Precheck-Cache lesen fehlgeschlagen (%s): %s", order_number, e)
        return None


def set_cached_precheck(order_number: int, data: Dict[str, Any], ttl_seconds: int = _CACHE_TTL_SECONDS) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return
    try:
        redis_client.setex(f"{_CACHE_PREFIX}{int(order_number)}", ttl_seconds, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        logger.debug("Precheck-Cache schreiben fehlgeschlagen (%s): %s", order_number, e)


def run_precheck_for_auftrag(auftrag: Dict[str, Any], with_ai: bool = False) -> Dict[str, Any]:
    order_number = int(auftrag.get("auftrag_nr") or auftrag.get("order_number"))
    base = _base_precheck(auftrag)
    if not with_ai:
        set_cached_precheck(order_number, base)
        return base

    # KI nur, wenn Daten ausreichend sind; sonst bleibt Vorprüfung.
    akte_exists = bool(((auftrag.get("garantieakte") or {}).get("existiert")))
    if not akte_exists:
        set_cached_precheck(order_number, base)
        return base

    try:
        from api.garantie_pruefung import run_garantie_pruefung
        ki = run_garantie_pruefung(order_number, marke=base.get("marke"))
        if ki.get("success"):
            checkliste = ki.get("checkliste") or []
            base["status"] = "vollpruefung"
            base["ki_quelle"] = "lm_studio"
            base["ki_empfehlung_lang"] = ki.get("empfehlung") or base["ki_empfehlung_lang"]
            base["ki_empfehlung_kurz"] = (base["ki_empfehlung_lang"] or "")[:180]
            base["checkliste"] = checkliste
        else:
            base["status"] = "vorpruefung"
            base["ki_fehler"] = ki.get("error")
    except Exception as e:
        logger.warning("KI-Precheck Auftrag %s fehlgeschlagen: %s", order_number, e)
        base["status"] = "vorpruefung"
        base["ki_fehler"] = str(e)

    base["last_checked_at"] = datetime.now().isoformat()
    set_cached_precheck(order_number, base)
    return base
