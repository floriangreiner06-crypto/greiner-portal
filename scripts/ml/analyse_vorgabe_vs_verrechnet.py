#!/usr/bin/env python3
"""
ANALYSE: Vorgabe vs. Gestempelt vs. Verrechnet
===============================================
Beantwortet die Frage: Sind wir zu langsam oder verrechnen wir zu wenig?

Die Wahrheit liegt in der Differenz zwischen:
- VORGABE (was der Hersteller/SB vorgibt)
- IST-ZEIT (was der Mechaniker tatsächlich braucht)  
- VERRECHNET (was am Ende auf der Rechnung steht)

Szenarien:
1. IST > Vorgabe UND Verrechnet = IST → Unterbewertung erkannt & korrigiert ✅
2. IST > Vorgabe UND Verrechnet = Vorgabe → Umsatz-Verlust! ❌
3. IST < Vorgabe UND Verrechnet = Vorgabe → Effizienz-Gewinn ✅
4. IST ≈ Vorgabe → Alles passt

TAG 99 - Analyse für ML-Training-Verbesserung
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# .env laden
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(env_path)

def get_connection():
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )

def analyse_vorgabe_vs_verrechnet(tage=90, betrieb=None):
    """
    Hauptanalyse: Vergleicht Vorgabe, IST-Zeit und verrechnete AW
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print(f"ANALYSE: Vorgabe vs. Gestempelt vs. Verrechnet (letzte {tage} Tage)")
    print("=" * 80)
    
    # Query: Abgerechnete Aufträge mit allen drei Werten
    query = """
        WITH 
        -- Verrechnete AW pro Auftrag (was auf der Rechnung steht)
        verrechnet AS (
            SELECT 
                l.order_number,
                SUM(l.time_units) as verrechnet_aw,
                SUM(l.net_price_in_order) as verrechnet_eur,
                STRING_AGG(DISTINCT CAST(l.mechanic_no AS TEXT), ',') as mechaniker
            FROM labours l
            JOIN invoices i ON l.invoice_number = i.invoice_number 
                AND l.invoice_type = i.invoice_type
            JOIN orders o ON l.order_number = o.number
            WHERE i.invoice_date >= CURRENT_DATE - INTERVAL '%s days'
              AND o.order_date >= CURRENT_DATE - INTERVAL '%s days'
              AND l.is_invoiced = true
              AND l.mechanic_no IS NOT NULL
              AND l.time_units > 0
              AND i.invoice_type IN (2, 4, 5, 6)  -- Nur Werkstatt, keine Fahrzeugverkäufe
            GROUP BY l.order_number
        ),
        -- Vorgabe-AW pro Auftrag (was ursprünglich geplant war)
        vorgabe AS (
            SELECT 
                order_number,
                SUM(time_units) as vorgabe_aw
            FROM labours
            WHERE time_units > 0
              AND order_number IN (SELECT order_number FROM verrechnet)
            GROUP BY order_number
        ),
        -- Gestempelte Zeit pro Auftrag (DEDUPLIZIERT!)
        -- Locosoft erzeugt Duplikate pro Position, daher DISTINCT ON
        gestempelt AS (
            SELECT 
                order_number,
                SUM(minuten) / 6.0 as ist_aw
            FROM (
                SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                    order_number,
                    EXTRACT(EPOCH FROM (end_time - start_time)) / 60 as minuten
                FROM times
                WHERE type = 2
                  AND end_time IS NOT NULL
                  AND order_number IN (SELECT order_number FROM verrechnet)
            ) dedup
            GROUP BY order_number
        ),
        -- Auftragsdetails
        auftraege AS (
            SELECT 
                o.number as order_number,
                o.subsidiary,
                o.order_date,
                m.description as marke,
                v.license_plate as kennzeichen
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            WHERE o.number IN (SELECT order_number FROM verrechnet)
        )
        SELECT 
            a.order_number,
            a.subsidiary as betrieb,
            a.order_date,
            a.marke,
            a.kennzeichen,
            ROUND(COALESCE(v.vorgabe_aw, 0)::numeric, 2) as vorgabe_aw,
            ROUND(COALESCE(g.ist_aw, 0)::numeric, 2) as ist_aw,
            ROUND(COALESCE(r.verrechnet_aw, 0)::numeric, 2) as verrechnet_aw,
            ROUND(COALESCE(r.verrechnet_eur, 0)::numeric, 2) as verrechnet_eur,
            r.mechaniker
        FROM auftraege a
        LEFT JOIN vorgabe v ON a.order_number = v.order_number
        LEFT JOIN gestempelt g ON a.order_number = g.order_number
        LEFT JOIN verrechnet r ON a.order_number = r.order_number
        WHERE COALESCE(v.vorgabe_aw, 0) > 0
          AND COALESCE(g.ist_aw, 0) > 0
    """
    
    params = [tage, tage]
    
    if betrieb:
        query += " AND a.subsidiary = %s"
        params.append(betrieb)
    
    query += " ORDER BY a.order_date DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if not rows:
        print("❌ Keine Daten gefunden!")
        return None
    
    # In DataFrame umwandeln
    df = pd.DataFrame(rows)
    
    # Berechnungen
    df['diff_ist_vorgabe'] = df['ist_aw'] - df['vorgabe_aw']
    df['diff_verrechnet_vorgabe'] = df['verrechnet_aw'] - df['vorgabe_aw']
    df['diff_verrechnet_ist'] = df['verrechnet_aw'] - df['ist_aw']
    
    # Ratio berechnen
    df['ratio_ist_vorgabe'] = df['ist_aw'] / df['vorgabe_aw']
    df['ratio_verrechnet_vorgabe'] = df['verrechnet_aw'] / df['vorgabe_aw']
    
    # Kategorisierung
    def kategorisiere(row):
        ist = float(row['ist_aw'])
        vorgabe = float(row['vorgabe_aw'])
        verrechnet = float(row['verrechnet_aw'])
        
        # Toleranz: 10%
        toleranz = vorgabe * 0.1
        
        if ist > vorgabe + toleranz:
            # Länger gearbeitet als Vorgabe
            if verrechnet >= ist - toleranz:
                return 'NACHKALKULIERT'  # Mehr verrechnet ✅
            elif verrechnet >= vorgabe - toleranz and verrechnet < ist - toleranz:
                return 'VERLUST'  # Nur Vorgabe verrechnet ❌
            else:
                return 'RABATT'  # Weniger als Vorgabe verrechnet
        elif ist < vorgabe - toleranz:
            # Schneller als Vorgabe
            if verrechnet >= vorgabe - toleranz:
                return 'EFFIZIENZ'  # Vorgabe verrechnet trotz schneller ✅
            else:
                return 'KULANZ'  # Weniger verrechnet
        else:
            # Im Rahmen der Vorgabe
            return 'NORMAL'
    
    df['kategorie'] = df.apply(kategorisiere, axis=1)
    
    # =========================================================================
    # STATISTIKEN
    # =========================================================================
    
    print(f"\n📊 DATENBASIS: {len(df)} abgerechnete Aufträge")
    print(f"   Zeitraum: {df['order_date'].min()} bis {df['order_date'].max()}")
    
    # Kategorie-Verteilung
    print("\n" + "=" * 60)
    print("📈 KATEGORIE-VERTEILUNG")
    print("=" * 60)
    
    kategorie_stats = df.groupby('kategorie').agg({
        'order_number': 'count',
        'diff_ist_vorgabe': 'sum',
        'diff_verrechnet_ist': 'sum',
        'verrechnet_eur': 'sum'
    }).rename(columns={
        'order_number': 'anzahl',
        'diff_ist_vorgabe': 'mehr_gearbeitet_aw',
        'diff_verrechnet_ist': 'diff_verrechnet_aw',
        'verrechnet_eur': 'umsatz_eur'
    })
    
    kategorie_stats['anteil_%'] = (kategorie_stats['anzahl'] / len(df) * 100).round(1)
    
    print(kategorie_stats.to_string())
    
    # Interpretation
    print("\n" + "=" * 60)
    print("🎯 INTERPRETATION")
    print("=" * 60)
    
    verlust_auftraege = df[df['kategorie'] == 'VERLUST']
    nachkalk_auftraege = df[df['kategorie'] == 'NACHKALKULIERT']
    effizienz_auftraege = df[df['kategorie'] == 'EFFIZIENZ']
    
    if len(verlust_auftraege) > 0:
        verlust_aw = verlust_auftraege['diff_ist_vorgabe'].sum()
        # Durchschnittlicher AW-Preis berechnen
        avg_aw_preis = df['verrechnet_eur'].sum() / df['verrechnet_aw'].sum() if df['verrechnet_aw'].sum() > 0 else 100
        verlust_eur = verlust_aw * avg_aw_preis
        
        print(f"\n❌ UMSATZ-VERLUST durch nicht nachkalkulierte Aufträge:")
        print(f"   {len(verlust_auftraege)} Aufträge mit {verlust_aw:.1f} AW Mehrarbeit")
        print(f"   → Geschätzter Verlust: {verlust_eur:,.0f} € (bei Ø {avg_aw_preis:.0f} €/AW)")
    
    if len(nachkalk_auftraege) > 0:
        nachkalk_aw = nachkalk_auftraege['diff_verrechnet_vorgabe'].sum()
        print(f"\n✅ NACHKALKULATION funktioniert bei:")
        print(f"   {len(nachkalk_auftraege)} Aufträgen mit {nachkalk_aw:.1f} AW Nachberechnung")
    
    if len(effizienz_auftraege) > 0:
        effizienz_aw = effizienz_auftraege['diff_ist_vorgabe'].abs().sum()
        print(f"\n✅ EFFIZIENZ-GEWINN:")
        print(f"   {len(effizienz_auftraege)} Aufträge {effizienz_aw:.1f} AW schneller als Vorgabe")
    
    # =========================================================================
    # MECHANIKER-ANALYSE
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("👨‍🔧 MECHANIKER-ANALYSE: Wer arbeitet effizienter?")
    print("=" * 60)
    
    # Mechaniker extrahieren (kann mehrere pro Auftrag sein)
    mech_data = []
    for _, row in df.iterrows():
        if row['mechaniker']:
            for mech in str(row['mechaniker']).split(','):
                mech_data.append({
                    'mechaniker_nr': int(mech.strip()),
                    'vorgabe_aw': row['vorgabe_aw'],
                    'ist_aw': row['ist_aw'],
                    'verrechnet_aw': row['verrechnet_aw'],
                    'kategorie': row['kategorie']
                })
    
    if mech_data:
        mech_df = pd.DataFrame(mech_data)
        
        # Decimal zu float konvertieren
        for col in ['vorgabe_aw', 'ist_aw', 'verrechnet_aw']:
            mech_df[col] = mech_df[col].astype(float)
        
        mech_stats = mech_df.groupby('mechaniker_nr').agg({
            'vorgabe_aw': ['count', 'sum'],
            'ist_aw': 'sum',
            'verrechnet_aw': 'sum'
        })
        mech_stats.columns = ['auftraege', 'vorgabe_sum', 'ist_sum', 'verrechnet_sum']
        mech_stats['effizienz_%'] = (mech_stats['vorgabe_sum'] / mech_stats['ist_sum'] * 100).round(1)
        mech_stats['nachkalk_%'] = ((mech_stats['verrechnet_sum'] - mech_stats['vorgabe_sum']) / mech_stats['vorgabe_sum'] * 100).round(1)
        
        mech_stats = mech_stats.sort_values('effizienz_%', ascending=False)
        
        print("\nTop 10 Mechaniker nach Effizienz:")
        print(mech_stats.head(10).to_string())
    
    # =========================================================================
    # MARKEN-ANALYSE
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("🚗 MARKEN-ANALYSE: Wo sind Vorgaben am ungenauesten?")
    print("=" * 60)
    
    # Decimal zu float für Marken-Analyse
    df_float = df.copy()
    for col in ['ratio_ist_vorgabe', 'diff_ist_vorgabe']:
        df_float[col] = df_float[col].astype(float)
    
    marken_stats = df_float.groupby('marke').agg({
        'order_number': 'count',
        'ratio_ist_vorgabe': 'mean',
        'diff_ist_vorgabe': 'sum',
        'kategorie': lambda x: (x == 'VERLUST').sum()
    }).rename(columns={
        'order_number': 'auftraege',
        'ratio_ist_vorgabe': 'avg_ratio',
        'diff_ist_vorgabe': 'total_mehrarbeit_aw',
        'kategorie': 'verlust_auftraege'
    })
    
    marken_stats = marken_stats[marken_stats['auftraege'] >= 10]  # Min. 10 Aufträge
    marken_stats = marken_stats.sort_values('avg_ratio', ascending=False)
    
    print(marken_stats.to_string())
    
    # =========================================================================
    # SCHLUSSFOLGERUNG
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("💡 SCHLUSSFOLGERUNG FÜR ML-TRAINING")
    print("=" * 60)
    
    total_verlust = len(verlust_auftraege)
    total_nachkalk = len(nachkalk_auftraege)
    total_normal = len(df[df['kategorie'] == 'NORMAL'])
    
    verlust_ratio = total_verlust / len(df) * 100
    nachkalk_ratio = total_nachkalk / len(df) * 100
    
    print(f"""
    ERGEBNIS:
    ─────────────────────────────────────────────────────────
    • {verlust_ratio:.1f}% der Aufträge = VERLUST (Mehr gearbeitet, nur Vorgabe verrechnet)
    • {nachkalk_ratio:.1f}% der Aufträge = NACHKALKULIERT (Mehr gearbeitet, mehr verrechnet)
    • {100 - verlust_ratio - nachkalk_ratio:.1f}% = Normal/Effizienz
    
    INTERPRETATION:
    ─────────────────────────────────────────────────────────
    """)
    
    if verlust_ratio > nachkalk_ratio:
        print(f"""
    ❌ PROBLEM: Hauptsächlich INEFFIZIENZ!
    
       Die Mechaniker brauchen länger, aber es wird NICHT nachkalkuliert.
       → Das ML-Modell zeigt echte Ineffizienz, nicht Unterbewertung.
       → Fokus: Prozessoptimierung, Schulung, bessere Vorgaben
       → ML-Label: Vorhersage = "Erwartete Dauer" (Warnung)
    """)
    elif nachkalk_ratio > verlust_ratio:
        print(f"""
    ✅ GUT: Hauptsächlich UNTERBEWERTUNG mit Nachkalkulation!
    
       Die Vorgaben sind zu niedrig, aber SBs kalkulieren nach.
       → Das ML-Modell zeigt echte Unterbewertung.
       → Fokus: Bessere Vorgabezeiten, Hersteller-Feedback
       → ML-Label: Vorhersage = "Potenzial" (Umsatzchance)
    """)
    else:
        print(f"""
    ⚖️ GEMISCHT: Teils Ineffizienz, teils Unterbewertung
    
       → Differenzierte Betrachtung pro Marke/Mechaniker nötig
       → ML-Label: Neutral formulieren
    """)
    
    # =========================================================================
    # EXPORT FÜR TRAINING
    # =========================================================================
    
    export_path = "/opt/greiner-portal/data/ml/analyse_vorgabe_verrechnet.csv"
    df.to_csv(export_path, index=False)
    print(f"\n📁 Analyse exportiert nach: {export_path}")
    
    return df


def create_training_labels(df):
    """
    Erstellt verbesserte Training-Labels basierend auf der Analyse.
    
    Anstatt nur IST-Zeit zu predicten, unterscheiden wir:
    - is_inefficient: True wenn IST > Vorgabe UND nur Vorgabe verrechnet
    - is_undervalued: True wenn IST > Vorgabe UND mehr verrechnet
    - recommended_aw: Was SOLLTE die Vorgabe sein?
    """
    
    df['is_inefficient'] = df['kategorie'] == 'VERLUST'
    df['is_undervalued'] = df['kategorie'] == 'NACHKALKULIERT'
    
    # Empfohlene AW = Was am Ende verrechnet wurde (das ist die "Wahrheit")
    df['recommended_aw'] = df['verrechnet_aw']
    
    # Für Training: Nur die relevanten Spalten
    training_df = df[[
        'order_number', 'betrieb', 'marke', 'mechaniker',
        'vorgabe_aw', 'ist_aw', 'verrechnet_aw',
        'is_inefficient', 'is_undervalued', 'recommended_aw',
        'kategorie'
    ]].copy()
    
    export_path = "/opt/greiner-portal/data/ml/training_data_with_labels.csv"
    training_df.to_csv(export_path, index=False)
    print(f"\n📁 Training-Daten mit Labels exportiert nach: {export_path}")
    
    return training_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyse Vorgabe vs. Verrechnet')
    parser.add_argument('--tage', type=int, default=90, help='Anzahl Tage')
    parser.add_argument('--betrieb', type=int, help='Betrieb-Filter (1, 2, 3)')
    parser.add_argument('--export-training', action='store_true', help='Training-Labels exportieren')
    
    args = parser.parse_args()
    
    df = analyse_vorgabe_vs_verrechnet(tage=args.tage, betrieb=args.betrieb)
    
    if args.export_training and df is not None:
        create_training_labels(df)
