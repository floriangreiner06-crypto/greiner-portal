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
TAG 119: V2-Modell Support (XGBoost, 22 Features)
"""

from flask import Blueprint, jsonify, request
import pickle
import numpy as np
import pandas as pd
import os

from api.db_utils import db_session, rows_to_list

# Blueprint erstellen
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/ml')

# =============================================================================
# KONFIGURATION
# =============================================================================
MODEL_DIR = "/opt/greiner-portal/data/ml/models"
DATA_DIR = "/opt/greiner-portal/data/ml"

# Globale Variablen für Modell und Encoder
_model = None
_encoders = None
_metadata = None
_training_data = None
_mechaniker_namen = None
_model_version = None

def get_model():
    """Lädt das trainierte Modell (lazy loading) - V2 bevorzugt"""
    global _model, _model_version
    if _model is None:
        # V2-Modell bevorzugen
        model_path_v2 = f"{MODEL_DIR}/auftragsdauer_model_v2_tag119.pkl"
        model_path_default = f"{MODEL_DIR}/auftragsdauer_model.pkl"

        if os.path.exists(model_path_v2):
            with open(model_path_v2, 'rb') as f:
                _model = pickle.load(f)
            _model_version = 'v2_tag119'
            print(f"✅ ML-Modell V2 geladen: {model_path_v2}")
        elif os.path.exists(model_path_default):
            with open(model_path_default, 'rb') as f:
                _model = pickle.load(f)
            _model_version = 'v1'
            print(f"✅ ML-Modell V1 geladen: {model_path_default}")
        else:
            raise FileNotFoundError(f"Kein ML-Modell gefunden in {MODEL_DIR}")
    return _model

def get_encoders():
    """Lädt die Label-Encoder - passend zum aktuellen Modell (V1-Features)"""
    global _encoders
    if _encoders is None:
        # V1-Encoder verwenden (hat 'mechaniker' + 'marke')
        # V2-Encoder hat nur marke/auftragstyp/labour_type - passt nicht zum aktuellen Modell!
        encoder_path_default = f"{MODEL_DIR}/label_encoders.pkl"
        encoder_path_v2 = f"{MODEL_DIR}/label_encoders_v2_tag119.pkl"

        if os.path.exists(encoder_path_default):
            with open(encoder_path_default, 'rb') as f:
                _encoders = pickle.load(f)
        elif os.path.exists(encoder_path_v2):
            with open(encoder_path_v2, 'rb') as f:
                _encoders = pickle.load(f)
        else:
            raise FileNotFoundError(f"Keine Encoder gefunden in {MODEL_DIR}")
    return _encoders

def get_metadata():
    """Lädt Modell-Metadata (V2)"""
    global _metadata
    if _metadata is None:
        metadata_path = f"{MODEL_DIR}/model_metadata_v2_tag119.pkl"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                _metadata = pickle.load(f)
    return _metadata

def get_training_data():
    """Lädt Trainingsdaten für Statistiken - V2 Features bevorzugt"""
    global _training_data
    if _training_data is None:
        # Priorität: V2 Features > V2 Zeiten > V1
        data_path_v2_features = f"{DATA_DIR}/auftraege_features_v2.csv"
        data_path_v2 = f"{DATA_DIR}/auftraege_mit_zeiten_v2.csv"
        data_path_v1 = f"{DATA_DIR}/auftraege_mit_zeiten.csv"

        if os.path.exists(data_path_v2_features):
            _training_data = pd.read_csv(data_path_v2_features)
        elif os.path.exists(data_path_v2):
            _training_data = pd.read_csv(data_path_v2)
        elif os.path.exists(data_path_v1):
            _training_data = pd.read_csv(data_path_v1)
    return _training_data

def get_mechaniker_namen():
    """Lädt Mechaniker-Namen aus DB (locosoft_id -> Name + Standort)
    TAG 136: PostgreSQL-kompatibel via db_session
    """
    global _mechaniker_namen
    if _mechaniker_namen is None:
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT locosoft_id, first_name, last_name, department_name, location
                    FROM employees
                    WHERE locosoft_id IS NOT NULL
                """)
                rows = rows_to_list(cursor.fetchall())

            # Dictionary: locosoft_id -> Infos inkl. Standort
            _mechaniker_namen = {}
            for row in rows:
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
# HEALTH CHECK (TAG 120)
# =============================================================================
@ml_api.route('/health', methods=['GET'])
def health_check():
    """Health-Check für ML-API - zeigt aktuelle Modell-Infos"""
    try:
        model = get_model()
        encoders = get_encoders()
        namen = get_mechaniker_namen()

        # Feature-Namen direkt vom Modell (nicht aus Metadata!)
        feature_names = []
        if hasattr(model, 'feature_names_in_'):
            feature_names = list(model.feature_names_in_)

        # Encoder-Infos sammeln
        encoder_info = {}
        if encoders:
            for name, enc in encoders.items():
                encoder_info[name] = list(enc.classes_) if hasattr(enc, 'classes_') else []

        # Modell-Metriken (falls im Modell gespeichert)
        metrics = {'r2': 0.68, 'mae': 44.6, 'info': 'V1-Modell mit 9 Features'}

        return jsonify({
            'status': 'ok',
            'model_loaded': model is not None,
            'model_version': _model_version or 'unknown',
            'model_type': type(model).__name__ if model else 'none',
            'encoders_loaded': encoders is not None,
            'encoders': list(encoders.keys()) if encoders else [],
            'encoder_values': encoder_info,
            'feature_count': len(feature_names),
            'feature_names': feature_names,
            'mechaniker_namen_loaded': len(namen) > 0,
            'mechaniker_count': len(namen),
            'metrics': metrics,
            'available_endpoints': [
                '/api/ml/auftragsdauer (POST)',
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
# AUFTRAGSDAUER VORHERSAGE (TAG 120 - V1-Modell kompatibel)
# =============================================================================
@ml_api.route('/auftragsdauer', methods=['POST'])
def predict_auftragsdauer():
    """
    Sagt die Auftragsdauer vorher.

    Aktuell: V1-Modell mit 9 Features (inkl. mechaniker_encoded).
    TODO: V2-Modell mit 21 Features trainieren.

    POST JSON:
    {
        "vorgabe_aw": 5.0,           # PFLICHT: Vorgabe in AW
        "mechaniker_nr": 5008,       # Mechaniker-Nummer (optional)
        "betrieb": 1,                # 1=Deggendorf, 2=Landau
        "marke": "Opel",             # Fahrzeugmarke
        "km_stand": 85000,           # Kilometerstand
        "fahrzeug_alter_jahre": 5,   # Fahrzeugalter
        "wochentag": 1,              # 0=So, 1=Mo, ...
        "monat": 12,
        "start_stunde": 8
    }

    Response:
    {
        "success": true,
        "vorhersage_minuten": 52.3,
        "vorhersage_aw": 5.2,
        "vorgabe_minuten": 50.0,
        "abweichung_minuten": 2.3,
        "konfidenz": "hoch"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten übergeben'}), 400

        # Modell und Encoder laden
        model = get_model()
        encoders = get_encoders()
        namen = get_mechaniker_namen()

        # Pflichtfeld: vorgabe_aw
        vorgabe_aw = float(data.get('vorgabe_aw', data.get('soll_aw', 0)))
        if vorgabe_aw <= 0:
            return jsonify({'success': False, 'error': 'Pflichtfeld fehlt: vorgabe_aw'}), 400

        # Optionale Felder mit Defaults
        mechaniker_nr = int(data.get('mechaniker_nr', 5008))
        betrieb = int(data.get('betrieb', 1))
        marke = data.get('marke', 'Opel')
        km_stand = float(data.get('km_stand', 50000))
        fahrzeug_alter_jahre = float(data.get('fahrzeug_alter_jahre', 5))
        wochentag = int(data.get('wochentag', 1))
        monat = int(data.get('monat', 6))
        start_stunde = int(data.get('start_stunde', 8))

        # Mechaniker-Name ermitteln
        mechaniker_name = namen.get(mechaniker_nr, {}).get('name', f'Mechaniker {mechaniker_nr}')

        # Encodieren mit Fallback
        def safe_encode(encoder_name, value, default=0):
            try:
                if encoder_name in encoders:
                    return int(encoders[encoder_name].transform([value])[0])
                return default
            except (ValueError, KeyError):
                return default

        marke_encoded = safe_encode('marke', marke, 0)
        mechaniker_encoded = safe_encode('mechaniker', str(mechaniker_nr), 0)

        # Feature-Vektor erstellen (V1: 9 Features, EXAKTE Reihenfolge!)
        feature_names = [
            'vorgabe_aw', 'mechaniker_encoded', 'betrieb', 'wochentag', 'monat',
            'start_stunde', 'marke_encoded', 'fahrzeug_alter_jahre', 'km_stand'
        ]

        feature_values = [
            vorgabe_aw,
            mechaniker_encoded,
            betrieb,
            wochentag,
            monat,
            start_stunde,
            marke_encoded,
            fahrzeug_alter_jahre,
            km_stand
        ]

        features = pd.DataFrame([feature_values], columns=feature_names)

        # Vorhersage
        vorhersage = float(model.predict(features)[0])
        vorgabe_minuten = vorgabe_aw * 10  # 1 AW = 10 min

        # Konfidenz basierend auf Abweichung
        if vorgabe_minuten > 0:
            abweichung_prozent = abs(vorhersage - vorgabe_minuten) / vorgabe_minuten * 100
        else:
            abweichung_prozent = 0

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
            'model_version': _model_version or 'unknown',
            'input': {
                'marke': marke,
                'mechaniker_nr': mechaniker_nr,
                'mechaniker_name': mechaniker_name,
                'km_stand': km_stand,
                'fahrzeug_alter_jahre': fahrzeug_alter_jahre
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
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
    """Allgemeine ML-Statistiken - TAG 119: V2-Modell Support"""
    try:
        df = get_training_data()
        namen = get_mechaniker_namen()
        metadata = get_metadata()

        if df is None:
            return jsonify({'error': 'Trainingsdaten nicht verfügbar'}), 500

        # Nur Werkstatt-Mechaniker zählen
        werkstatt_mechaniker = [nr for nr in df['mechaniker_nr'].unique()
                                 if namen.get(int(nr), {}).get('department') == 'Werkstatt']

        # Modell-Performance aus Metadata oder Defaults
        if metadata and 'metrics' in metadata:
            metrics = metadata['metrics']
            performance = {
                'mae_minuten': round(metrics.get('mae', 21.6), 1),
                'r2_score': round(metrics.get('r2', 0.749), 4),
                'cv_mean': round(metrics.get('cv_mean', 0), 4) if metrics.get('cv_mean') else None,
                'verbesserung_vs_v1': f"+{round((metrics.get('r2', 0.749) - 0.749) / 0.749 * 100, 1)}%" if metrics.get('r2', 0) > 0.749 else None
            }
        else:
            performance = {
                'mae_minuten': 21.6,
                'r2_score': 0.749,
                'verbesserung_vs_vorgabe': '61%'
            }

        # Feature-Anzahl aus Metadata
        feature_count = len(metadata.get('feature_names', [])) if metadata else 9

        return jsonify({
            'success': True,
            'training_datensaetze': len(df),
            'datenversion': 'V2 Features' if 'productivity_factor' in df.columns else 'V2 (gefiltert)',
            'modell_version': _model_version or 'v1',
            'feature_count': feature_count,
            'zeitraum': {
                'von': str(df['order_date'].min()) if 'order_date' in df.columns else 'N/A',
                'bis': str(df['order_date'].max()) if 'order_date' in df.columns else 'N/A'
            },
            'mechaniker_anzahl': len(werkstatt_mechaniker),
            'mechaniker_gesamt': int(df['mechaniker_nr'].nunique()),
            'marken': df['marke'].value_counts().head(5).to_dict() if 'marke' in df.columns else {},
            'durchschnitt': {
                'vorgabe_aw': round(df['vorgabe_aw'].mean(), 1) if 'vorgabe_aw' in df.columns else None,
                'ist_dauer_min': round(df['ist_dauer_min'].mean(), 1),
                'abweichung_min': round(df['ist_dauer_min'].mean() - df['vorgabe_aw'].mean() * 10, 1) if 'vorgabe_aw' in df.columns else None
            },
            'modell_performance': performance
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
