#!/usr/bin/env python3
"""
Reparaturpotenzial-Analyse für aktuelle Werkstatt-Aufträge
Analysiert Fahrzeuge nach Upselling-Potenzial basierend auf:
- km-Stand
- Fahrzeugalter
- Saisonale Empfehlungen

Aktualisiert: 2025-12-19 (TAG 127)
- Neuwagen-Filter (< 5.000 km)
- E-Auto-Erkennung (Marke + E-Kennzeichen)
- Baujahr-Fallback korrigiert
"""

import psycopg2
from datetime import date
from collections import Counter
import sys

# ============================================================================
# KONSTANTEN UND FILTER
# ============================================================================

# Mindest-km für Empfehlungen (Neuwagen-Filter)
MIN_KM_FUER_EMPFEHLUNGEN = 5000

# E-Auto Marken (keine Zahnriemen, Kupplung, etc.)
E_AUTO_MARKEN = [
    'leapmotor', 'tesla', 'polestar', 'nio', 'byd', 'lucid', 'rivian',
    'xpeng', 'aiways', 'smart'
]

# Regeln die für E-Autos nicht relevant sind
E_AUTO_AUSSCHLUSS_REGELN = ['zahnriemen', 'kupplung', 'klimaanlage']


# Regeln aus der API
REPARATUR_REGELN = {
    "batterie": {
        "name": "Batterie-Check",
        "icon": "🔋",
        "km_schwelle": 40000,
        "km_median": 49000,
        "alter_schwelle": 4,
        "prioritaet": 1
    },
    "bremsen": {
        "name": "Bremsbeläge prüfen",
        "icon": "🛑",
        "km_schwelle": 55000,
        "km_median": 73000,
        "alter_schwelle": 4,
        "prioritaet": 2
    },
    "klimaanlage": {
        "name": "Klimaservice",
        "icon": "❄️",
        "km_schwelle": 60000,
        "km_median": 81000,
        "alter_schwelle": 5,
        "prioritaet": 3,
        "saison_monate": [4, 5, 6]
    },
    "zahnriemen": {
        "name": "Zahnriemen-Intervall",
        "icon": "⚙️",
        "km_schwelle": 80000,
        "km_median": 92000,
        "alter_schwelle": 5,
        "prioritaet": 1
    },
    "kupplung": {
        "name": "Kupplung prüfen",
        "icon": "🔧",
        "km_schwelle": 50000,
        "km_median": 62000,
        "alter_schwelle": 4,
        "prioritaet": 3
    },
    "stossdaempfer": {
        "name": "Fahrwerk/Stoßdämpfer",
        "icon": "🚗",
        "km_schwelle": 80000,
        "km_median": 98000,
        "alter_schwelle": 6,
        "prioritaet": 3
    }
}

SAISONALE = {
    "wintercheck": {
        "name": "Wintercheck",
        "icon": "🌨️",
        "monate": [9, 10, 11]
    },
    "sommercheck": {
        "name": "Klimacheck",
        "icon": "☀️",
        "monate": [4, 5, 6]
    },
    "reifenwechsel": {
        "name": "Reifenwechsel-Saison",
        "icon": "🛞",
        "monate": [3, 4, 10, 11]
    }
}


def analyse_auftraege(tage=2):
    """Analysiert Aufträge der letzten X Tage"""

    conn = psycopg2.connect(
        host="10.80.80.8",
        database="loco_auswertung_db",
        user="loco_auswertung_benutzer",
        password="loco"
    )
    cur = conn.cursor()

    # Aufträge holen
    cur.execute(f"""
        SELECT
            o.number,
            o.order_date::date,
            COALESCE(o.order_mileage, v.mileage_km, 0),
            v.license_plate,
            v.production_year,
            COALESCE(m.description, 'Unbekannt'),
            v.internal_number
        FROM orders o
        JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN makes m ON v.make_number = m.make_number
        WHERE o.order_date::date >= CURRENT_DATE - INTERVAL '{tage} days'
          AND v.license_plate IS NOT NULL
          AND LENGTH(v.license_plate) > 3
        ORDER BY o.order_date DESC
        LIMIT 50
    """)

    auftraege = cur.fetchall()
    heute = date.today()
    aktueller_monat = heute.month

    print("=" * 90)
    print(f"REPARATURPOTENZIAL-ANALYSE - {heute.strftime('%d.%m.%Y')}")
    print(f"Aufträge analysiert: {len(auftraege)} (letzte {tage} Tage)")
    print("=" * 90)

    ergebnisse = []
    uebersprungen_neuwagen = 0
    uebersprungen_eauto = 0

    def ist_elektrofahrzeug(marke, kennzeichen):
        """Prüft ob E-Auto (Marke oder E-Kennzeichen)"""
        if marke and marke.lower() in E_AUTO_MARKEN:
            return True
        if kennzeichen:
            kz_clean = kennzeichen.replace(' ', '').replace('-', '').upper()
            if kz_clean.endswith('E') and len(kz_clean) >= 6:
                return True
        return False

    for row in auftraege:
        order_nr, datum, km, kennzeichen, baujahr, marke, vehicle_nr = row

        # Baujahr-Fallback: Kein Baujahr = 0 Jahre alt (keine Altersempfehlungen)
        if baujahr and baujahr > 1990:
            alter = heute.year - baujahr
        else:
            alter = 0

        # NEUWAGEN-FILTER: Unter 5.000 km überspringen
        if km < MIN_KM_FUER_EMPFEHLUNGEN:
            uebersprungen_neuwagen += 1
            continue

        # E-Auto Erkennung
        ist_e_auto = ist_elektrofahrzeug(marke, kennzeichen)

        empfehlungen = []

        # Regel-Check
        for regel_id, regel in REPARATUR_REGELN.items():
            # E-Auto Filter: Bestimmte Regeln überspringen
            if ist_e_auto and regel_id in E_AUTO_AUSSCHLUSS_REGELN:
                continue

            km_relevant = km >= regel["km_schwelle"]
            alter_relevant = alter >= regel["alter_schwelle"]

            # Saison-Prüfung
            saison_relevant = True
            if "saison_monate" in regel:
                saison_relevant = aktueller_monat in regel["saison_monate"]

            if km_relevant or (alter_relevant and saison_relevant):
                dringlichkeit = "mittel"
                if km > regel["km_median"] * 1.1:
                    dringlichkeit = "HOCH"
                elif km > regel["km_median"]:
                    dringlichkeit = "mittel"
                else:
                    dringlichkeit = "niedrig"

                if regel_id == "zahnriemen" and km >= regel["km_schwelle"]:
                    dringlichkeit = "HOCH"

                empfehlungen.append({
                    "regel": regel_id,
                    "name": regel["name"],
                    "icon": regel["icon"],
                    "dringlichkeit": dringlichkeit,
                    "grund": f"{km:,}km / {alter}J".replace(",", ".")
                })

        # Saisonale Empfehlungen
        for saison_id, saison in SAISONALE.items():
            if aktueller_monat in saison["monate"]:
                empfehlungen.append({
                    "regel": saison_id,
                    "name": saison["name"],
                    "icon": saison["icon"],
                    "dringlichkeit": "saisonal",
                    "grund": "Dezember"
                })

        if empfehlungen:
            ergebnisse.append({
                "kennzeichen": kennzeichen,
                "marke": marke,
                "km": km,
                "alter": alter,
                "baujahr": baujahr if baujahr and baujahr > 1990 else None,
                "ist_e_auto": ist_e_auto,
                "empfehlungen": empfehlungen
            })

    # Sortieren nach Anzahl HOHE Empfehlungen
    ergebnisse.sort(key=lambda x: (
        -len([e for e in x["empfehlungen"] if e["dringlichkeit"] == "HOCH"]),
        -len(x["empfehlungen"])
    ))

    print()
    for e in ergebnisse:
        km_str = f"{e['km']:,}".replace(",", ".")
        bj_str = f"BJ {e['baujahr']}" if e['baujahr'] else "BJ ?"
        e_marker = " ⚡" if e.get('ist_e_auto') else ""
        print(f"🚗 {e['kennzeichen']:<15} | {e['marke']:<10} | {km_str:>10} km | {bj_str} ({e['alter']}J){e_marker}")

        for emp in e["empfehlungen"]:
            if emp["dringlichkeit"] == "HOCH":
                print(f"   ⚠️  {emp['icon']} {emp['name']:<25} [{emp['dringlichkeit']}] - {emp['grund']}")
            elif emp["dringlichkeit"] == "mittel":
                print(f"   ➡️  {emp['icon']} {emp['name']:<25} [{emp['dringlichkeit']}] - {emp['grund']}")
            elif emp["dringlichkeit"] == "saisonal":
                print(f"   📅 {emp['icon']} {emp['name']:<25} [saisonal]")
            else:
                print(f"   ℹ️  {emp['icon']} {emp['name']:<25} [{emp['dringlichkeit']}] - {emp['grund']}")
        print()

    # Statistik
    print("=" * 90)
    print("ZUSAMMENFASSUNG")
    print("-" * 90)
    total_empf = sum(len(e["empfehlungen"]) for e in ergebnisse)
    hohe_empf = sum(len([x for x in e["empfehlungen"] if x["dringlichkeit"] == "HOCH"]) for e in ergebnisse)
    mit_empf = len(ergebnisse)
    e_autos = len([e for e in ergebnisse if e.get('ist_e_auto')])

    analysiert = len(auftraege) - uebersprungen_neuwagen
    pct = mit_empf * 100 // analysiert if analysiert else 0

    print(f"Aufträge gesamt:             {len(auftraege)}")
    print(f"Übersprungen (Neuwagen):     {uebersprungen_neuwagen} (< {MIN_KM_FUER_EMPFEHLUNGEN:,} km)".replace(",", "."))
    print(f"Analysiert:                  {analysiert}")
    print("-" * 90)
    print(f"Fahrzeuge mit Empfehlungen:  {mit_empf}/{analysiert} ({pct}%)")
    print(f"Davon E-Autos:               {e_autos} ⚡")
    print(f"Gesamt-Empfehlungen:         {total_empf}")
    print(f"Davon HOHE Priorität:        {hohe_empf}")

    # Top-Empfehlungen
    print()
    print("TOP EMPFEHLUNGEN (häufigste):")
    alle_empf = [emp["name"] for e in ergebnisse for emp in e["empfehlungen"] if emp["dringlichkeit"] != "saisonal"]
    for name, count in Counter(alle_empf).most_common(5):
        print(f"   {count}x {name}")

    conn.close()

    return ergebnisse


if __name__ == "__main__":
    tage = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    analyse_auftraege(tage)
