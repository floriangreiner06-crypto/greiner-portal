"""
Erwartete wiederkehrende Ausgaben für Liquiditätsvorschau aus Transaktionen-Historie.
Erkennt Muster (Kategorie + typischer Tag im Monat) und projiziert auf den Zeitraum.

Kategorien aus transaktionen (z. B. Personal/Gehalt, Miete, Steuern, Bank & Zinsen).
Workstream: Controlling / Liquidität
"""

from __future__ import annotations

import calendar
import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

from api.db_utils import db_session, row_to_dict, rows_to_list

logger = logging.getLogger(__name__)

# Transfers/Intern aus Projektion ausblenden (wie in cashflow_vorschau)
_TRANSFER_FILTER = """
    AND NOT (
        verwendungszweck LIKE '%%Autohaus Greiner%%Autohaus Greiner%%'
        OR verwendungszweck LIKE '%%Umbuchung%%'
        OR verwendungszweck LIKE '%%Einlage%%'
        OR verwendungszweck LIKE '%%Rückzahlung Einlage%%'
    )
    AND (kategorie IS NULL OR kategorie != 'Intern')
    AND (kategorie IS NULL OR kategorie != 'Einkaufsfinanzierung')
"""
# Einkaufsfinanzierung wird nicht aus Historie projiziert – Tilgungen kommen aus Tabelle tilgungen

# Mindestanzahl Monate mit Daten, um eine Kategorie als „wiederkehrend“ zu werten
_MIN_MONATE_FUER_MUSTER = 2

# Fachliche Regeln: Diese Kategorien zahlen wir typischerweise zu Monatsanfang (Tag 1)
# – unabhängig vom aus den Daten ermittelten Tag (Buchung kann z. B. 14. sein wegen Valuta/Import).
_MONATSANFANG_KATEGORIEN = ("Personal",)  # Löhne, Gehälter, SV, Lohnsteuer


def get_wiederkehrende_ausgaben_muster(monate_historie: int = 12) -> List[Dict[str, Any]]:
    """
    Analysiert Transaktionen (Ausgaben) der letzten N Monate und ermittelt pro
    (kategorie, unterkategorie) den durchschnittlichen Monatsbetrag und den
    typischen Zahlungstag (Median Tag im Monat).

    Returns:
        Liste von {
            "kategorie": str,
            "unterkategorie": str | None,
            "avg_monatlich": float,
            "typical_day": int,  # 1–31
            "anzahl_monate": int,
            "label": str
        }
    """
    heute = date.today()
    von = heute - timedelta(days=min(365, monate_historie * 31))
    von = von.replace(day=1)

    with db_session() as conn:
        cursor = conn.cursor()
        # Rohdaten: Ausgaben (betrag < 0), mit Kategorie
        cursor.execute("""
            SELECT
                COALESCE(kategorie, 'Sonstige Ausgaben') AS kategorie,
                unterkategorie,
                buchungsdatum AS datum,
                ABS(betrag) AS betrag_abs
            FROM transaktionen
            WHERE buchungsdatum >= %s AND buchungsdatum <= %s AND betrag < 0
            """ + _TRANSFER_FILTER + """
            ORDER BY buchungsdatum
        """, (von, heute))
        rows = rows_to_list(cursor.fetchall(), cursor)

    # Gruppieren nach (kategorie, unterkategorie)
    # pro Gruppe: pro Monat Summe + Liste der Tage
    by_group: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {"monate": defaultdict(float), "tage": []})
    for r in rows:
        kat = (r.get("kategorie") or "Sonstige Ausgaben").strip()
        uk = (r.get("unterkategorie") or "").strip()
        key = (kat, uk)
        d = r.get("datum")
        if not d:
            continue
        if hasattr(d, "date"):
            d = d.date()
        monat_key = (d.year, d.month)
        by_group[key]["monate"][monat_key] += float(r.get("betrag_abs") or 0)
        by_group[key]["tage"].append(d.day)

    result = []
    for (kat, uk), data in by_group.items():
        if kat == "Einkaufsfinanzierung":
            continue  # Tilgungen aus Tabelle tilgungen, keine Doppelzählung
        if kat in ("Einnahmen", "Sonstige Einnahmen"):
            continue  # Nur Ausgaben projizieren
        if kat == "Sonstige Ausgaben":
            continue  # Catch-all, oft Einmalposten – nicht als wiederkehrend projizieren (verzerrt z. B. 15.03)
        monate = data["monate"]
        if len(monate) < _MIN_MONATE_FUER_MUSTER:
            continue
        summen = list(monate.values())
        avg_monatlich = sum(summen) / len(summen) if summen else 0
        tage = data["tage"]
        typical_day = int(round(sum(tage) / len(tage))) if tage else 15
        typical_day = max(1, min(28, typical_day))  # 1–28, um in jedem Monat gültig zu sein
        # Fachliche Regel: Löhne/Gehälter (Personal) zahlen wir zu Monatsanfang
        if kat in _MONATSANFANG_KATEGORIEN:
            typical_day = 1
        label = f"{kat}" + (f" / {uk}" if uk else "")
        result.append({
            "kategorie": kat,
            "unterkategorie": uk or None,
            "avg_monatlich": round(avg_monatlich, 2),
            "typical_day": typical_day,
            "anzahl_monate": len(monate),
            "label": label,
        })
    return result


def get_erwartete_ausgaben_pro_tag(
    von_datum: date,
    bis_datum: date,
    monate_historie: int = 12,
) -> Dict[str, Dict[str, Any]]:
    """
    Projiziert wiederkehrende Ausgaben (aus Historie) auf den Zeitraum [von_datum, bis_datum].
    Pro Datum: Summe aller Kategorien, die an ihrem „typischen Tag“ in diesem Monat fällig sind.

    Returns:
        dict[datum_iso] = {
            "erwartete_ausgaben": float,
            "details": [ {"label": str, "betrag": float}, ... ]
        }
    """
    muster = get_wiederkehrende_ausgaben_muster(monate_historie)
    result: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"erwartete_ausgaben": 0.0, "details": []})

    for m in muster:
        avg = m["avg_monatlich"]
        day = m["typical_day"]
        label = m["label"]
        # Alle Monate im Projektionszeitraum durchgehen
        d = von_datum.replace(day=1)
        while d <= bis_datum:
            last = calendar.monthrange(d.year, d.month)[1]
            zahlung_tag = min(day, last)
            zahlung_am = d.replace(day=zahlung_tag)
            if von_datum <= zahlung_am <= bis_datum:
                key = zahlung_am.isoformat()
                result[key]["erwartete_ausgaben"] += avg
                result[key]["details"].append({"label": label, "betrag": avg})
            # Nächster Monat
            if d.month == 12:
                d = d.replace(year=d.year + 1, month=1)
            else:
                d = d.replace(month=d.month + 1)

    for k in result:
        result[k]["erwartete_ausgaben"] = round(result[k]["erwartete_ausgaben"], 2)
        for det in result[k]["details"]:
            det["betrag"] = round(det["betrag"], 2)
    return dict(result)


def get_erwartete_ausgaben_gesamt(
    von_datum: date,
    bis_datum: date,
    monate_historie: int = 12,
) -> Dict[str, Any]:
    """
    Kombinierte Ausgabe für die Liquiditätsvorschau.

    Returns:
        {
            "pro_tag": { datum_iso: { "erwartete_ausgaben": float, "details": [...] } },
            "muster": [ ... ]  # Liste der erkannten wiederkehrenden Kategorien
        }
    """
    muster = get_wiederkehrende_ausgaben_muster(monate_historie)
    pro_tag = get_erwartete_ausgaben_pro_tag(von_datum, bis_datum, monate_historie)
    return {
        "pro_tag": pro_tag,
        "muster": muster,
    }
