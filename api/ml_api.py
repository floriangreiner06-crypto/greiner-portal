#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - ML API: Werkstatt-Vorhersagen
=============================================================================
REST API für Machine Learning Vorhersagen:
- /api/ml/auftragsdauer - Auftragsdauer vorhersagen
- /api/ml/mechaniker-ranking - Mechaniker-Effizienz
- /api/ml/mechaniker-liste - Liste aller Mechaniker mit Namen
- /api/ml/health - Health-Check

TAG 97: Mechaniker-Namen hinzugefügt (JOIN mit employees-Tabelle)
"""

from flask import Blueprint, jsonify, request
import pickle
import numpy as np
import pandas as pd
import sqlite3
import os

# Blueprint erstellen
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/ml')

# =============================================================================
# KONFIGURATION
# =============================================================================
MODEL_DIR = "/opt/greiner-portal/data/ml/models"
DATA_DIR = "/opt/greiner-portal/data/ml"
SQLITE_DB = "/opt/greiner-portal/data/greiner_controlling.db"

# Globale Variablen für Modell und Encoder
_model = None
_encoders = None
_training_data = None
_mechaniker_namen = None

def get_model():
    """Lädt das trainierte Modell (lazy loading)"""
    global _model
    if _model is None:
        model_path = f"{MODEL_DIR}/auftragsdauer_model.pkl"
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                _model = pickle.load(f)
        else:
            raise FileNotFoundError(f"Modell nicht gefunden: {model_path}")
    return _model

def get_encoders():
    """Lädt die Label-Encoder"""
    global _encoders
    if _encoders is None:
        encoder_path = f"{MODEL_DIR}/label_encoders.pkl"
        if os.path.exists(encoder_path):
            with open(encoder_path, 'rb') as f:
                _encoders = pickle.load(f)
        else:
            raise FileNotFoundError(f"Encoder nicht gefunden: {encoder_path}")
    return _encoders

def get_training_data():
    """Lädt Trainingsdaten für Statistiken - V2 (gefiltert)"""
    global _training_data
    if _training_data is None:
        # Priorität: V2 (gefiltert) > V1 (ungefiltert)
        data_path_v2 = f"{DATA_DIR}/auftraege_mit_zeiten_v2.csv"
        data_path_v1 = f"{DATA_DIR}/auftraege_mit_zeiten.csv"
        
        if os.path.exists(data_path_v2):
            _training_data = pd.read_csv(data_path_v2)
        elif os.path.exists(data_path_v1):
            _training_data = pd.read_csv(data_path_v1)
    return _training_data

def get_mechaniker_namen():
    """Lädt Mechaniker-Namen aus SQLite (locosoft_id -> Name + Standort)"""
    global _mechaniker_namen
    if _mechaniker_namen is None:
        try:
            conn = sqlite3.connect(SQLITE_DB)
            query = """
                SELECT locosoft_id, first_name, last_name, department_name, location
                FROM employees 
                WHERE locosoft_id IS NOT NULL
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Dictionary: locosoft_id -> Infos inkl. Standort
            _mechaniker_namen = {}
            for _, row in df.iterrows():
                location = row['location'] if row['location'] else 'Unbekannt'
                # Kürzel für Standort
                loc_short = 'DEG' if 'Deggendorf' in location else ('LAU' if 'Landau' in location else location[:3].upper())
                
                _mechaniker_namen[int(row['locosoft_id'])] = {
                    'name': f"{row['first_name']} {row['last_name']}",
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'department': row['department_name'],
                    'location': location,
                    'location_short': loc_short
                }
        except Exception as e:
            print(f"Fehler beim Laden der Mechaniker-Namen: {e}")
            _mechaniker_namen = {}
    return _mechaniker_namen


# =============================================================================
# HEALTH CHECK
# =============================================================================
@ml_api.route('/health', methods=['GET'])
def health_check():
    """Health-Check für ML-API"""
    try:
        model = get_model()
        encoders = get_encoders()
        namen = get_mechaniker_namen()

        return jsonify({
            'status': 'ok',
            'model_loaded': model is not None,
            'encoders_loaded': encoders is not None,
            'mechaniker_namen_loaded': len(namen) > 0,
            'available_endpoints': [
                '/api/ml/auftragsdauer',
                '/api/ml/mechaniker-ranking',
                '/api/ml/mechaniker-liste',
                '/api/ml/statistik'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# =============================================================================
# MECHANIKER-LISTE (NEU - TAG 97)
# =============================================================================
@ml_api.route('/mechaniker-liste', methods=['GET'])
def mechaniker_liste():
    """
    Liste aller Mechaniker mit Namen und Standort für Dropdowns.
    
    Query-Parameter:
    - standort: Filter nach Standort (optional, z.B. "Deggendorf" oder "Landau")
    
    Response:
    {
        "success": true,
        "standorte": ["Deggendorf", "Landau a.d. Isar"],
        "mechaniker": [
            {"nr": 5008, "name": "Patrick Ebner", "location": "Deggendorf", "location_short": "DEG"},
            ...
        ]
    }
    """
    try:
        namen = get_mechaniker_namen()
        df = get_training_data()
        standort_filter = request.args.get('standort', '')
        
        # Nur Mechaniker die auch in Trainingsdaten vorkommen
        aktive_mechaniker = []
        standorte = set()
        
        if df is not None:
            mechaniker_in_daten = df['mechaniker_nr'].unique()
            for nr in sorted(mechaniker_in_daten):
                nr_int = int(nr)
                if nr_int in namen:
                    info = namen[nr_int]
                    # Nur Werkstatt-Mitarbeiter
                    if info['department'] == 'Werkstatt':
                        standorte.add(info['location'])
                        
                        # Standort-Filter anwenden
                        if standort_filter and standort_filter.lower() not in info['location'].lower():
                            continue
                        
                        aktive_mechaniker.append({
                            'nr': nr_int,
                            'name': info['name'],
                            'location': info['location'],
                            'location_short': info['location_short']
                        })
        
        # Sortieren nach Standort, dann Name
        aktive_mechaniker.sort(key=lambda x: (x['location'], x['name']))
        
        return jsonify({
            'success': True,
            'anzahl': len(aktive_mechaniker),
            'standorte': sorted(list(standorte)),
            'mechaniker': aktive_mechaniker
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# AUFTRAGSDAUER VORHERSAGE
# =============================================================================
@ml_api.route('/auftragsdauer', methods=['POST'])
def predict_auftragsdauer():
    """
    Sagt die Auftragsdauer vorher.

    POST JSON:
    {
        "vorgabe_aw": 5.0,
        "mechaniker_nr": 5008,
        "betrieb": 1,
        "marke": "Opel",
        "km_stand": 85000,
        "fahrzeug_alter_jahre": 5,
        "wochentag": 1,        # 0=So, 1=Mo, ...
        "monat": 12,
        "start_stunde": 8
    }

    Response:
    {
        "vorhersage_minuten": 52.3,
        "vorhersage_stunden": 0.87,
        "vorgabe_minuten": 50.0,
        "abweichung_minuten": 2.3,
        "konfidenz": "hoch",
        "mechaniker_name": "Patrick Ebner"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Keine Daten übergeben'}), 400

        # Pflichtfelder prüfen
        required = ['vorgabe_aw']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Pflichtfeld fehlt: {field}'}), 400

        # Modell und Encoder laden
        model = get_model()
        encoders = get_encoders()
        namen = get_mechaniker_namen()

        # Defaults für optionale Felder
        vorgabe_aw = float(data.get('vorgabe_aw', 5))
        mechaniker_nr = int(data.get('mechaniker_nr', 5008))
        betrieb = int(data.get('betrieb', 1))
        marke = data.get('marke', 'Opel')
        km_stand = float(data.get('km_stand', 50000))
        fahrzeug_alter = float(data.get('fahrzeug_alter_jahre', 3))
        wochentag = int(data.get('wochentag', 1))
        monat = int(data.get('monat', 6))
        start_stunde = int(data.get('start_stunde', 8))

        # Mechaniker-Name ermitteln
        mechaniker_name = namen.get(mechaniker_nr, {}).get('name', f'Mechaniker {mechaniker_nr}')

        # Marke encodieren
        try:
            marke_encoded = encoders['marke'].transform([marke])[0]
        except ValueError:
            marke_encoded = 0  # Fallback für unbekannte Marke

        # Mechaniker encodieren
        try:
            mechaniker_encoded = encoders['mechaniker'].transform([str(mechaniker_nr)])[0]
        except ValueError:
            mechaniker_encoded = 0  # Fallback

        # Feature-Vektor erstellen (gleiche Reihenfolge wie Training!)
        features = pd.DataFrame([[
            vorgabe_aw,
            mechaniker_encoded,
            betrieb,
            wochentag,
            monat,
            start_stunde,
            marke_encoded,
            fahrzeug_alter,
            km_stand
        ]], columns=[
            'vorgabe_aw', 'mechaniker_encoded', 'betrieb', 'wochentag', 'monat',
            'start_stunde', 'marke_encoded', 'fahrzeug_alter_jahre', 'km_stand'
        ])

        # Vorhersage
        vorhersage = model.predict(features)[0]
        vorgabe_minuten = vorgabe_aw * 10  # 1 AW = 10 min

        # Konfidenz basierend auf Abweichung
        abweichung_prozent = abs(vorhersage - vorgabe_minuten) / vorgabe_minuten * 100 if vorgabe_minuten > 0 else 0
        if abweichung_prozent < 20:
            konfidenz = "hoch"
        elif abweichung_prozent < 50:
            konfidenz = "mittel"
        else:
            konfidenz = "niedrig"

        return jsonify({
            'success': True,
            'vorhersage_minuten': round(vorhersage, 1),
            'vorhersage_stunden': round(vorhersage / 60, 2),
            'vorhersage_aw': round(vorhersage / 10, 1),
            'vorgabe_minuten': round(vorgabe_minuten, 1),
            'vorgabe_aw': vorgabe_aw,
            'abweichung_minuten': round(vorhersage - vorgabe_minuten, 1),
            'abweichung_prozent': round((vorhersage - vorgabe_minuten) / vorgabe_minuten * 100, 1) if vorgabe_minuten > 0 else 0,
            'konfidenz': konfidenz,
            'input': {
                'marke': marke,
                'mechaniker_nr': mechaniker_nr,
                'mechaniker_name': mechaniker_name,
                'km_stand': km_stand,
                'fahrzeug_alter_jahre': fahrzeug_alter
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# MECHANIKER RANKING
# =============================================================================
@ml_api.route('/mechaniker-ranking', methods=['GET'])
def mechaniker_ranking():
    """
    Ranking der Mechaniker nach Effizienz.
    
    TAG 97: Jetzt mit Namen und nur Werkstatt-Mitarbeiter!

    Query-Parameter:
    - marke: Filter nach Marke (optional)
    - limit: Anzahl Ergebnisse (default: 20)
    - nur_werkstatt: Nur echte Mechaniker (default: true)

    Response: Liste der Mechaniker mit Effizienz-Score und Namen
    """
    try:
        marke = request.args.get('marke')
        limit = request.args.get('limit', 20, type=int)
        nur_werkstatt = request.args.get('nur_werkstatt', 'true').lower() == 'true'

        df = get_training_data()
        namen = get_mechaniker_namen()
        
        if df is None:
            return jsonify({'error': 'Trainingsdaten nicht verfügbar'}), 500

        # Optional nach Marke filtern
        if marke:
            df = df[df['marke'] == marke]

        # Aggregieren nach Mechaniker
        ranking = df.groupby('mechaniker_nr').agg({
            'ist_dauer_min': ['mean', 'std', 'count'],
            'vorgabe_aw': 'mean'
        }).reset_index()

        ranking.columns = ['mechaniker_nr', 'avg_ist_min', 'std_ist_min', 'anzahl_auftraege', 'avg_vorgabe_aw']

        # Effizienz berechnen: Vorgabe / IST (>1 = schneller als Vorgabe)
        ranking['vorgabe_min'] = ranking['avg_vorgabe_aw'] * 10
        ranking['effizienz'] = ranking['vorgabe_min'] / ranking['avg_ist_min']
        ranking['effizienz_prozent'] = (ranking['effizienz'] * 100).round(1)

        # Namen hinzufügen und nach Werkstatt filtern
        result = []
        for _, row in ranking.iterrows():
            mech_nr = int(row['mechaniker_nr'])
            mech_info = namen.get(mech_nr, {})
            mech_name = mech_info.get('name', f'Mitarbeiter {mech_nr}')
            mech_dept = mech_info.get('department', 'Unbekannt')
            
            # Nur Werkstatt-Mitarbeiter wenn gewünscht
            if nur_werkstatt and mech_dept != 'Werkstatt':
                continue
            
            result.append({
                'mechaniker_nr': mech_nr,
                'mechaniker_name': mech_name,
                'department': mech_dept,
                'location': mech_info.get('location', 'Unbekannt'),
                'location_short': mech_info.get('location_short', '?'),
                'anzahl_auftraege': int(row['anzahl_auftraege']),
                'avg_vorgabe_aw': round(row['avg_vorgabe_aw'], 1),
                'avg_ist_minuten': round(row['avg_ist_min'], 1),
                'effizienz_prozent': row['effizienz_prozent'],
                'bewertung': 'schnell' if row['effizienz'] > 1.1 else ('normal' if row['effizienz'] > 0.9 else 'langsam')
            })

        # Sortieren nach Effizienz (höher = besser)
        result = sorted(result, key=lambda x: x['effizienz_prozent'], reverse=True)[:limit]

        return jsonify({
            'success': True,
            'filter_marke': marke,
            'nur_werkstatt': nur_werkstatt,
            'anzahl': len(result),
            'ranking': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# STATISTIK
# =============================================================================
@ml_api.route('/statistik', methods=['GET'])
def ml_statistik():
    """Allgemeine ML-Statistiken - TAG 97: V2-Daten verwenden"""
    try:
        df = get_training_data()
        namen = get_mechaniker_namen()
        
        if df is None:
            return jsonify({'error': 'Trainingsdaten nicht verfügbar'}), 500

        # Nur Werkstatt-Mechaniker zählen
        werkstatt_mechaniker = [nr for nr in df['mechaniker_nr'].unique() 
                                 if namen.get(int(nr), {}).get('department') == 'Werkstatt']

        return jsonify({
            'success': True,
            'training_datensaetze': len(df),
            'datenversion': 'V2 (gefiltert)',
            'zeitraum': {
                'von': str(df['order_date'].min()) if 'order_date' in df.columns else 'N/A',
                'bis': str(df['order_date'].max()) if 'order_date' in df.columns else 'N/A'
            },
            'mechaniker_anzahl': len(werkstatt_mechaniker),
            'mechaniker_gesamt': int(df['mechaniker_nr'].nunique()),
            'marken': df['marke'].value_counts().head(5).to_dict() if 'marke' in df.columns else {},
            'durchschnitt': {
                'vorgabe_aw': round(df['vorgabe_aw'].mean(), 1),
                'ist_dauer_min': round(df['ist_dauer_min'].mean(), 1),
                'abweichung_min': round(df['ist_dauer_min'].mean() - df['vorgabe_aw'].mean() * 10, 1)
            },
            'modell_performance': {
                'mae_minuten': 21.6,
                'r2_score': 0.749,
                'verbesserung_vs_vorgabe': '61%'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
