#!/usr/bin/env python3
"""
Predictive Scoring: km-Schätzung + Reparatur-Scores für Call-Agent / Catch-Export.
Liest aus Locosoft (read-only), schreibt in drive_portal (PostgreSQL).
Verwendung: python scripts/marketing/marketing_km_scoring.py [--dry-run]
"""

import sys
from datetime import date, datetime
from collections import defaultdict

sys.path.insert(0, "/opt/greiner-portal")

from api.db_utils import db_session, locosoft_session


# Opel = 40, Hyundai = 27 (Locosoft make_number)
MAKE_NUMBERS = (27, 40)
ORDER_MILEAGE_YEARS = 5
TODAY = date.today()

# Locosoft: Einige order_mileage-Werte sind in Metern (z. B. 1.800.001). Werte > Schwellwert → Meter → km
MILEAGE_METER_THRESHOLD = 500_000  # ab hier als Meter interpretieren, durch 1000 teilen
MAX_PLAUSIBLE_KM = 999_999  # Obergrenze für geschätzte km (Datenfehler abfangen)
MAX_PLAUSIBLE_KM_PER_YEAR = 60_000  # wenn berechnetes km/Jahr darüber → keine Extrapolation (Datenfehler)


def _mileage_to_km(val):
    """Konvertiert Locosoft-Kilometerstand: Werte > MILEAGE_METER_THRESHOLD gelten als Meter."""
    if val is None:
        return None
    if val > MILEAGE_METER_THRESHOLD:
        return int(val / 1000)
    return val


def load_categories_and_keywords(conn):
    """Lädt repair_categories und repair_category_keywords aus Portal."""
    cur = conn.cursor()
    cur.execute("SELECT category_id, name, interval_km, interval_years FROM repair_categories")
    categories = {r[0]: {"name": r[1], "interval_km": r[2], "interval_years": r[3]} for r in cur.fetchall()}
    cur.execute("""
        SELECT category_id, keyword, make_number
        FROM repair_category_keywords
    """)
    keywords_by_cat = defaultdict(list)
    for cat_id, kw, make in cur.fetchall():
        keywords_by_cat[cat_id].append((kw, make))
    return categories, dict(keywords_by_cat)


def fetch_vehicles_locosoft(conn):
    """Kundenfahrzeuge Opel/Hyundai (make 27, 40)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT internal_number, subsidiary, make_number
        FROM vehicles
        WHERE make_number IN %s
          AND (is_customer_vehicle = true OR is_customer_vehicle IS NULL)
          AND internal_number IS NOT NULL
    """, (MAKE_NUMBERS,))
    return [{"vehicle_number": r[0], "subsidiary": r[1], "make_number": r[2]} for r in cur.fetchall()]


def fetch_orders_with_mileage(conn, vehicle_numbers):
    """Aufträge mit km-Stand, letzte ORDER_MILEAGE_YEARS Jahre. order_mileage wird in km normalisiert (_mileage_to_km)."""
    if not vehicle_numbers:
        return []
    cur = conn.cursor()
    cur.execute("""
        SELECT vehicle_number, (order_date::date) AS order_date, order_mileage
        FROM orders
        WHERE vehicle_number = ANY(%s)
          AND order_mileage > 0
          AND order_date >= CURRENT_DATE - (INTERVAL '1 year' * %s)
        ORDER BY vehicle_number, order_date
    """, (vehicle_numbers, ORDER_MILEAGE_YEARS))
    return [(r[0], r[1], _mileage_to_km(r[2])) for r in cur.fetchall()]


def compute_km_estimates(orders_by_vehicle):
    """
    Pro Fahrzeug: km_current_estimate, km_per_year_estimate, confidence.
    - Mehrere Messungen: km/Jahr aus Durchschnitt der jährlichen Steigerung, dann Hochrechnung.
    - Eine Messung: MEDIUM, km_current = last_known_km.
    """
    result = {}
    for vn, rows in orders_by_vehicle.items():
        if not rows:
            continue
        rows = sorted(rows, key=lambda r: r[1])  # by order_date
        last_date = rows[-1][1]
        last_km = rows[-1][2]
        n = len(rows)
        if n >= 2:
            # km/Jahr aus Deltas
            km_per_year_list = []
            for i in range(1, n):
                d0, d1 = rows[i - 1][1], rows[i][1]
                km0, km1 = rows[i - 1][2], rows[i][2]
                if d0 and d1 and km0 and km1 and d1 > d0:
                    years = (d1 - d0).days / 365.25
                    if years > 0:
                        km_per_year_list.append((km1 - km0) / years)
            if km_per_year_list:
                import statistics
                km_per_year_raw = max(0, statistics.median(km_per_year_list))
                if km_per_year_raw > MAX_PLAUSIBLE_KM_PER_YEAR:
                    # Unplausibel (z. B. 5.457 km in 6 Tagen → 332k/Jahr) = vermutlich Erfassungsfehler
                    km_per_year = None
                    km_current = last_km
                    confidence = "MEDIUM"
                else:
                    km_per_year = km_per_year_raw
                    days_since = (TODAY - last_date).days
                    km_current = int(last_km + km_per_year * (days_since / 365.25))
                    if km_current > MAX_PLAUSIBLE_KM:
                        km_current = min(last_km, MAX_PLAUSIBLE_KM)
                    confidence = "HIGH"
            else:
                km_per_year = None
                km_current = last_km
                confidence = "MEDIUM"
        else:
            km_per_year = None
            km_current = last_km
            confidence = "MEDIUM"
        if km_current > MAX_PLAUSIBLE_KM:
            km_current = min(last_km, MAX_PLAUSIBLE_KM)
        result[vn] = {
            "km_current_estimate": km_current,
            "km_per_year_estimate": int(km_per_year) if km_per_year is not None else None,
            "confidence": confidence,
            "last_known_km": last_km,
            "last_known_date": last_date,
            "measurement_count": n,
        }
    return result


def fetch_last_service_per_vehicle_category(conn, vehicle_numbers, category_id, keywords):
    """
    Pro Fahrzeug die letzte Auftragszeile (order_date, order_mileage), wo eine Labour
    zu dieser Kategorie passt (keyword in text_line). keywords: Liste (keyword, make_number).
    """
    if not vehicle_numbers or not keywords:
        return {}
    kw_list = [kw for kw, _ in keywords]
    cur = conn.cursor()
    placeholders = " OR ".join("LOWER(l.text_line) LIKE %s" for _ in kw_list)
    params = [vehicle_numbers] + [f"%{k}%" for k in kw_list]
    cur.execute("""
        SELECT DISTINCT ON (o.vehicle_number)
            o.vehicle_number,
            (o.order_date::date) AS order_date,
            o.order_mileage,
            o.subsidiary
        FROM orders o
        JOIN labours l ON l.order_number = o.number
        WHERE o.vehicle_number = ANY(%s)
          AND o.order_date >= CURRENT_DATE - INTERVAL '10 years'
          AND l.text_line IS NOT NULL
          AND (""" + placeholders + """)
        ORDER BY o.vehicle_number, o.order_date DESC
    """, params)
    return {
        r[0]: {
            "order_date": r[1],
            "order_mileage": _mileage_to_km(r[2]),
            "subsidiary": r[3],
        }
        for r in cur.fetchall()
    }


def score_priority(score_km, score_years, interval_km, interval_years):
    """score_combined = max(score_km, score_years); Priorität und Empfehlung."""
    score_combined = max(score_km or 0, score_years or 0)
    if score_combined >= 1.0:
        priority = "HIGH"
        recommended = "Zeitnahe Durchführung empfohlen"
    elif score_combined >= 0.7:
        priority = "MEDIUM"
        recommended = "Bald prüfen"
    else:
        priority = "LOW"
        recommended = "Im Auge behalten"
    return score_combined, priority, recommended


def run(dry_run=False):
    with db_session() as portal_conn:
        categories, keywords_by_cat = load_categories_and_keywords(portal_conn)
    if not categories:
        print("Keine repair_categories gefunden. Migration ausführen?")
        return

    with locosoft_session() as loco_conn:
        vehicles = fetch_vehicles_locosoft(loco_conn)
    vehicle_numbers = [v["vehicle_number"] for v in vehicles]
    print(f"Fahrzeuge (Opel/Hyundai, Kundenfahrzeuge): {len(vehicle_numbers)}")

    # Km-Schätzung
    with locosoft_session() as loco_conn:
        rows = fetch_orders_with_mileage(loco_conn, vehicle_numbers)
    orders_by_vehicle = defaultdict(list)
    for vn, od, om in rows:
        orders_by_vehicle[vn].append((vn, od, om))
    km_estimates = compute_km_estimates(orders_by_vehicle)
    print(f"Km-Schätzungen berechnet: {len(km_estimates)}")

    if not dry_run:
        with db_session() as portal_conn:
            cur = portal_conn.cursor()
            for vn, est in km_estimates.items():
                cur.execute("""
                    INSERT INTO vehicle_km_estimates (
                        vehicle_number, km_current_estimate, km_per_year_estimate,
                        confidence, last_known_km, last_known_date, measurement_count, calculated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (vehicle_number) DO UPDATE SET
                        km_current_estimate = EXCLUDED.km_current_estimate,
                        km_per_year_estimate = EXCLUDED.km_per_year_estimate,
                        confidence = EXCLUDED.confidence,
                        last_known_km = EXCLUDED.last_known_km,
                        last_known_date = EXCLUDED.last_known_date,
                        measurement_count = EXCLUDED.measurement_count,
                        calculated_at = NOW()
                """, (
                    vn, est["km_current_estimate"], est["km_per_year_estimate"],
                    est["confidence"], est["last_known_km"], est["last_known_date"],
                    est["measurement_count"]
                ))
            portal_conn.commit()

    # Reparatur-Scores pro Kategorie
    scores_to_insert = []
    with locosoft_session() as loco_conn:
        for cat_id, meta in categories.items():
            keywords = keywords_by_cat.get(cat_id, [])
            last_services = fetch_last_service_per_vehicle_category(
                loco_conn, vehicle_numbers, cat_id, keywords
            )
            interval_km = meta["interval_km"]
            interval_years = meta["interval_years"]
            for vn in vehicle_numbers:
                est = km_estimates.get(vn)
                estimated_km = est["km_current_estimate"] if est else None
                ls = last_services.get(vn)
                if not ls:
                    # Kein Service gefunden → hoher Score (noch nie gemacht)
                    last_date = None
                    last_km = None
                    km_since = estimated_km if estimated_km else 0
                    years_since = 99.0
                else:
                    last_date = ls["order_date"]
                    last_km = ls["order_mileage"]
                    km_since = (estimated_km - last_km) if (estimated_km and last_km) else None
                    years_since = (TODAY - last_date).days / 365.25 if last_date else 99.0
                score_km = (km_since / interval_km) if (km_since is not None and interval_km) else (years_since / interval_years if interval_years else 0)
                score_years = years_since / interval_years if interval_years else 0
                score_combined, priority, recommended = score_priority(
                    score_km, score_years, interval_km, interval_years
                )
                subsidiary = ls["subsidiary"] if ls else None
                scores_to_insert.append((
                    vn, cat_id, subsidiary, last_date, last_km, estimated_km,
                    km_since, years_since, score_km, score_years, score_combined,
                    priority, recommended
                ))

    print(f"Reparatur-Scores: {len(scores_to_insert)} Zeilen (Fahrzeuge × Kategorien)")

    if not dry_run and scores_to_insert:
        with db_session() as portal_conn:
            cur = portal_conn.cursor()
            for row in scores_to_insert:
                cur.execute("""
                    INSERT INTO vehicle_repair_scores (
                        vehicle_number, category_id, subsidiary,
                        last_service_date, last_service_km, estimated_current_km,
                        km_since_service, years_since_service, score_km, score_years, score_combined,
                        priority, recommended_action, calculated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (vehicle_number, category_id) DO UPDATE SET
                        subsidiary = EXCLUDED.subsidiary,
                        last_service_date = EXCLUDED.last_service_date,
                        last_service_km = EXCLUDED.last_service_km,
                        estimated_current_km = EXCLUDED.estimated_current_km,
                        km_since_service = EXCLUDED.km_since_service,
                        years_since_service = EXCLUDED.years_since_service,
                        score_km = EXCLUDED.score_km,
                        score_years = EXCLUDED.score_years,
                        score_combined = EXCLUDED.score_combined,
                        priority = EXCLUDED.priority,
                        recommended_action = EXCLUDED.recommended_action,
                        calculated_at = NOW()
                """, row)
            portal_conn.commit()

    if dry_run:
        print("(Dry-Run: keine Änderungen in der DB)")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
