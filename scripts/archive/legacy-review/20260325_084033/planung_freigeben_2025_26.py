#!/usr/bin/env python3
"""
Planung GJ 2025/26 freigeben – alle Einträge in abteilungsleiter_planung
auf status 'freigegeben' setzen und Ziele in kst_ziele schreiben.

Damit erscheinen die Planungen in der Gesamtübersicht (http://drive/planung/gesamtplanung).

Aufruf: python3 scripts/planung_freigeben_2025_26.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.db_utils import db_session
from psycopg2.extras import RealDictCursor
from api.abteilungsleiter_planung_data import AbteilungsleiterPlanungData

GESCHAEFTSJAHR = "2025/26"
FREIGEGEBEN_VON = "script_freigabe_2025_26"


def main():
    with db_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id FROM abteilungsleiter_planung
            WHERE geschaeftsjahr = %s
              AND status IN ('entwurf', 'eingereicht')
            ORDER BY bereich, standort, monat
        """, (GESCHAEFTSJAHR,))
        rows = cur.fetchall()

    ids = [r["id"] for r in rows]
    if not ids:
        print(f"Keine Planungen mit Status Entwurf/Eingereicht für GJ {GESCHAEFTSJAHR} gefunden.")
        print("(Bereits freigegeben oder keine Einträge.)")
        return

    print(f"Geben {len(ids)} Planungen für GJ {GESCHAEFTSJAHR} frei …")
    ok = 0
    fehler = 0
    for planung_id in ids:
        result = AbteilungsleiterPlanungData.freigeben_planung(
            planung_id,
            FREIGEGEBEN_VON,
            kommentar=None,
        )
        if result.get("success"):
            ok += 1
        else:
            fehler += 1
            print(f"  ID {planung_id}: {result.get('message', 'Unbekannt')}")

    print(f"Fertig: {ok} freigegeben, {fehler} Fehler.")
    print("Komplettübersicht: http://drive/planung/gesamtplanung?geschaeftsjahr=2025/26")


if __name__ == "__main__":
    main()
