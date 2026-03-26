#!/usr/bin/env python3
"""
Pragmatische Planung GJ 2025/26 in Abteilungsleiter-Planung eintragen
======================================================================
Trägt die Werte aus dem pragmatischen Plan (NW+GW Ø 1.880 €, Teile, Werkstatt)
in die Tabelle abteilungsleiter_planung ein – für alle Bereiche (NW, GW, Teile, Werkstatt)
und alle Standorte (1,2,3) sowie alle 12 Monate.

Verteilung: Konzern-Summen werden gleichmäßig auf 3 Standorte verteilt (je 1/3).
Sonstige: wird übersprungen (keine Berechnungslogik im Modul).

Aufruf: python3 scripts/planung_eintragen_abteilungsleiter.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.db_utils import db_session
from api.db_connection import get_db
from psycopg2.extras import RealDictCursor

# Pragmatische Planung 2025/26 (Konzern-Summen, aus planung_pragmatisch_2025_26)
GESCHAEFTSJAHR = "2025/26"
# NW: 630 Stück, Ø DB 1.800 → Plan-DB1 NW = 1.134.000 € (oder 1.880 kombiniert)
# GW: 900 Stück, Ziel DB 800.000 € (oder kombiniert mit NW → 1.880 €/Stück)
# Kombiniert: 1530 Stück × 1.880 = 2.876.400 € → NW-Anteil 630/1530, GW 900/1530
NW_PLAN_STUECK = 630
GW_PLAN_STUECK = 900
NW_GW_DB_PRO_STUECK = 1_880
# Aufteilung NW/GW nach Stück: NW-DB1 = 630*1880 = 1.184.400, GW-DB1 = 900*1880 = 1.692.000
PLAN_DB1_NW_JAHR = NW_PLAN_STUECK * NW_GW_DB_PRO_STUECK   # 1.184.400
PLAN_DB1_GW_JAHR = GW_PLAN_STUECK * NW_GW_DB_PRO_STUECK   # 1.692.000
# Teile, Werkstatt, Sonstige (Konzern)
PLAN_DB1_TEILE_JAHR = 1_149_335
PLAN_DB1_WERKSTATT_JAHR = 1_227_539
PLAN_DB1_SONSTIGE_JAHR = 121_430

STANDORTE = [1, 2, 3]
MONATE = list(range(1, 13))
ERSTELLT_VON = "planung_pragmatisch_script"


def verteile_jahr_auf_monate(jahreswert: float) -> list:
    """Gibt 12 Monatswerte (gleichmäßig 1/12) zurück."""
    pro_monat = jahreswert / 12
    return [round(pro_monat, 2)] * 12


def stueck_pro_monat(jahresstueck: int) -> list:
    """Verteilt Jahresstückzahl auf 12 Monate (gerundet, Summe = jahresstueck)."""
    base, rest = divmod(jahresstueck, 12)
    return [base + (1 if i < rest else 0) for i in range(12)]


def main():
    from api.abteilungsleiter_planung_data import (
        AbteilungsleiterPlanungData,
    )

    # Pro Standort 1/3 der Konzern-Summen
    nw_stueck_pro_standort = NW_PLAN_STUECK // 3      # 210
    gw_stueck_pro_standort = GW_PLAN_STUECK // 3     # 300
    db1_nw_pro_standort_jahr = PLAN_DB1_NW_JAHR / 3
    db1_gw_pro_standort_jahr = PLAN_DB1_GW_JAHR / 3
    db1_teile_pro_standort_jahr = PLAN_DB1_TEILE_JAHR / 3
    db1_werkstatt_pro_standort_jahr = PLAN_DB1_WERKSTATT_JAHR / 3

    nw_stueck_monate = stueck_pro_monat(nw_stueck_pro_standort)
    gw_stueck_monate = stueck_pro_monat(gw_stueck_pro_standort)
    db1_nw_pro_monat = db1_nw_pro_standort_jahr / 12
    db1_gw_pro_monat = db1_gw_pro_standort_jahr / 12

    # Bruttoertrag pro Fzg so dass DB1 = Stück × Bruttoertrag (bei variable_kosten_prozent = 0)
    brutto_nw = (db1_nw_pro_monat / nw_stueck_monate[0]) if nw_stueck_monate[0] else 0
    brutto_gw = (db1_gw_pro_monat / gw_stueck_monate[0]) if gw_stueck_monate[0] else 0

    inserted = 0
    with db_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        for standort in STANDORTE:
            for monat in MONATE:
                i = monat - 1
                # --- NW ---
                planung_data_nw = {
                    "plan_stueck": nw_stueck_monate[i],
                    "plan_bruttoertrag_pro_fzg": round(brutto_nw, 2),
                    "plan_variable_kosten_prozent": 0,
                    "plan_verkaufspreis": round(brutto_nw * 1.15, 2),  # grob
                    "plan_standzeit_tage": 60,
                    "plan_fertigmachen_pro_fzg": 0,
                    "plan_werbung_jahr": 0,
                    "plan_kulanz_jahr": 0,
                    "plan_training_jahr": 0,
                }
                try:
                    berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                        geschaeftsjahr=GESCHAEFTSJAHR,
                        monat=monat,
                        bereich="NW",
                        standort=standort,
                        planung_data=planung_data_nw,
                    )
                    hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                        berechnung["umsatz_basis"],
                        berechnung["db1_basis"],
                        GESCHAEFTSJAHR,
                        "NW",
                        standort,
                    )
                except Exception as e:
                    print(f"NW S{standort} M{monat}: Berechnung fehlgeschlagen: {e}")
                    continue

                row = {
                    "geschaeftsjahr": GESCHAEFTSJAHR,
                    "monat": monat,
                    "bereich": "NW",
                    "standort": standort,
                    "status": "entwurf",
                    "erstellt_von": ERSTELLT_VON,
                    **planung_data_nw,
                    "umsatz_basis": berechnung["umsatz_basis"],
                    "db1_basis": berechnung["db1_basis"],
                    "db2_basis": berechnung.get("db2_basis", 0),
                    "aufhol_umsatz": hybrid["aufhol_umsatz"],
                    "aufhol_db1": hybrid["aufhol_db1"],
                    "umsatz_ziel": hybrid["umsatz_ziel"],
                    "db1_ziel": hybrid["db1_ziel"],
                    "db2_ziel": berechnung.get("db2_basis", 0),
                }
                upsert(cur, row)
                inserted += 1

                # --- GW ---
                planung_data_gw = {
                    "plan_stueck": gw_stueck_monate[i],
                    "plan_bruttoertrag_pro_fzg": round(brutto_gw, 2),
                    "plan_variable_kosten_prozent": 0,
                    "plan_verkaufspreis": round(brutto_gw * 1.2, 2),
                    "plan_standzeit_tage": 75,
                    "plan_fertigmachen_pro_fzg": 0,
                    "plan_werbung_jahr": 0,
                    "plan_kulanz_jahr": 0,
                    "plan_training_jahr": 0,
                    "plan_ek_preis": round(brutto_gw * 0.85, 2),
                }
                try:
                    berechnung = AbteilungsleiterPlanungData.berechne_nw_gw_planung(
                        geschaeftsjahr=GESCHAEFTSJAHR,
                        monat=monat,
                        bereich="GW",
                        standort=standort,
                        planung_data=planung_data_gw,
                    )
                    hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                        berechnung["umsatz_basis"],
                        berechnung["db1_basis"],
                        GESCHAEFTSJAHR,
                        "GW",
                        standort,
                    )
                except Exception as e:
                    print(f"GW S{standort} M{monat}: {e}")
                    continue

                row = {
                    "geschaeftsjahr": GESCHAEFTSJAHR,
                    "monat": monat,
                    "bereich": "GW",
                    "standort": standort,
                    "status": "entwurf",
                    "erstellt_von": ERSTELLT_VON,
                    **planung_data_gw,
                    "umsatz_basis": berechnung["umsatz_basis"],
                    "db1_basis": berechnung["db1_basis"],
                    "db2_basis": berechnung.get("db2_basis", 0),
                    "aufhol_umsatz": hybrid["aufhol_umsatz"],
                    "aufhol_db1": hybrid["aufhol_db1"],
                    "umsatz_ziel": hybrid["umsatz_ziel"],
                    "db1_ziel": hybrid["db1_ziel"],
                    "db2_ziel": berechnung.get("db2_basis", 0),
                }
                upsert(cur, row)
                inserted += 1

            # --- Teile (12 Monate, gleiche Werte) ---
            umsatz_teile_standort_jahr = (db1_teile_pro_standort_jahr / 0.28)  # Marge 28 %
            planung_data_teile = {
                "plan_umsatz": round(umsatz_teile_standort_jahr, 2),
                "plan_marge_prozent": 28,
                "plan_lagerumschlag": 6,
                "plan_penner_quote": 5,
                "plan_servicegrad": 95,
                "plan_direkte_kosten": 0,
            }
            for monat in MONATE:
                try:
                    berechnung = AbteilungsleiterPlanungData.berechne_teile_planung(
                        geschaeftsjahr=GESCHAEFTSJAHR,
                        monat=monat,
                        standort=standort,
                        planung_data=planung_data_teile,
                    )
                    hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                        berechnung["umsatz_basis"],
                        berechnung["db1_basis"],
                        GESCHAEFTSJAHR,
                        "Teile",
                        standort,
                    )
                except Exception as e:
                    print(f"Teile S{standort} M{monat}: {e}")
                    continue
                row = {
                    "geschaeftsjahr": GESCHAEFTSJAHR,
                    "monat": monat,
                    "bereich": "Teile",
                    "standort": standort,
                    "status": "entwurf",
                    "erstellt_von": ERSTELLT_VON,
                    **planung_data_teile,
                    "umsatz_basis": berechnung["umsatz_basis"],
                    "db1_basis": berechnung["db1_basis"],
                    "db2_basis": berechnung.get("db2_basis", 0),
                    "aufhol_umsatz": hybrid["aufhol_umsatz"],
                    "aufhol_db1": hybrid["aufhol_db1"],
                    "umsatz_ziel": hybrid["umsatz_ziel"],
                    "db1_ziel": hybrid["db1_ziel"],
                    "db2_ziel": berechnung.get("db2_basis", 0),
                }
                upsert(cur, row)
                inserted += 1

            # --- Werkstatt (Ziel DB1/Monat ≈ 34.098 pro Standort) ---
            # db1 = stunden_verkauft * stundensatz * db1_marge → 400h * 155 * 0.55 ≈ 34.100
            # Werkstatt-Berechnung: stunden_verkauft_jahr = stunden_verkauft_pro_monat * 12, umsatz = stunden_jahr * stundensatz
            # Also pro Monat: stunden_pro_monat so dass (stunden_pro_monat*12)*stundensatz*0.55 = db1_jahr
            # db1_jahr = 409180 → umsatz_jahr = 409180/0.55 = 743964, stunden_jahr = 743964/155 = 4800, stunden_monat = 400
            planung_data_werkstatt = {
                "plan_anzahl_sb": 2,
                "plan_stundensatz": 155,
                "plan_produktivitaet": 85,
                "plan_leistungsgrad": 75,
                "plan_anzahl_mechaniker": 12,
                "plan_db1_marge": 55,
            }
            for monat in MONATE:
                try:
                    berechnung = AbteilungsleiterPlanungData.berechne_werkstatt_planung(
                        geschaeftsjahr=GESCHAEFTSJAHR,
                        monat=monat,
                        standort=standort,
                        planung_data=planung_data_werkstatt,
                    )
                    hybrid = AbteilungsleiterPlanungData.berechne_hybrid_ziele(
                        berechnung["umsatz_basis"],
                        berechnung["db1_basis"],
                        GESCHAEFTSJAHR,
                        "Werkstatt",
                        standort,
                    )
                except Exception as e:
                    print(f"Werkstatt S{standort} M{monat}: {e}")
                    continue
                row = {
                    "geschaeftsjahr": GESCHAEFTSJAHR,
                    "monat": monat,
                    "bereich": "Werkstatt",
                    "standort": standort,
                    "status": "entwurf",
                    "erstellt_von": ERSTELLT_VON,
                    **planung_data_werkstatt,
                    "umsatz_basis": berechnung["umsatz_basis"],
                    "db1_basis": berechnung["db1_basis"],
                    "db2_basis": berechnung.get("db2_basis", 0),
                    "aufhol_umsatz": hybrid["aufhol_umsatz"],
                    "aufhol_db1": hybrid["aufhol_db1"],
                    "umsatz_ziel": hybrid["umsatz_ziel"],
                    "db1_ziel": hybrid["db1_ziel"],
                    "db2_ziel": berechnung.get("db2_basis", 0),
                }
                upsert(cur, row)
                inserted += 1

        conn.commit()

    print(f"Abteilungsleiter-Planung eingetragen: {inserted} Zeilen (GJ {GESCHAEFTSJAHR}, NW/GW/Teile/Werkstatt, 3 Standorte, 12 Monate).")
    print("Bitte unter http://drive/planung/abteilungsleiter prüfen und ggf. anpassen.")


def upsert(cursor, row: dict):
    """INSERT ... ON CONFLICT DO UPDATE für abteilungsleiter_planung."""
    # Nur Spalten die in der Tabelle existieren
    allowed = {
        "geschaeftsjahr", "monat", "bereich", "standort", "status", "erstellt_von",
        "plan_stueck", "plan_bruttoertrag_pro_fzg", "plan_variable_kosten_prozent",
        "plan_verkaufspreis", "plan_standzeit_tage", "plan_fertigmachen_pro_fzg",
        "plan_werbung_jahr", "plan_kulanz_jahr", "plan_training_jahr", "plan_ek_preis",
        "plan_umsatz", "plan_marge_prozent", "plan_lagerumschlag", "plan_penner_quote",
        "plan_servicegrad", "plan_direkte_kosten",
        "plan_anzahl_sb", "plan_stundensatz", "plan_produktivitaet", "plan_leistungsgrad",
        "plan_anzahl_mechaniker", "plan_db1_marge",
        "umsatz_basis", "db1_basis", "db2_basis",
        "aufhol_umsatz", "aufhol_db1", "umsatz_ziel", "db1_ziel", "db2_ziel",
    }
    insert_data = {k: v for k, v in row.items() if k in allowed}
    cols = list(insert_data.keys())
    vals = [insert_data[c] for c in cols]
    placeholders = ", ".join(["%s"] * len(vals))
    update_cols = [c for c in cols if c not in ("geschaeftsjahr", "monat", "bereich", "standort")]
    set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])
    sql = f"""
        INSERT INTO abteilungsleiter_planung ({", ".join(cols)})
        VALUES ({placeholders})
        ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
        DO UPDATE SET {set_clause}, geaendert_am = CURRENT_TIMESTAMP
    """
    cursor.execute(sql, vals)


if __name__ == "__main__":
    main()
