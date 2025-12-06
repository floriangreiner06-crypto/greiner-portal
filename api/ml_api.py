#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - ML API: Werkstatt-Vorhersagen
=============================================================================
REST API für Machine Learning Vorhersagen:
- /api/ml/auftragsdauer - Auftragsdauer vorhersagen
- /api/ml/mechaniker-ranking - Mechaniker-Effizienz
- /api/ml/health - Health-Check
"""

from flask import Blueprint, jsonify, request
import pickle
import numpy as np
import pandas as pd
import os

# Blueprint erstellen
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/ml')

# =============================================================================
# MODELL LADEN
# =============================================================================
MODEL_DIR = "/opt/greiner-portal/data/ml/models"
DATA_DIR = "/opt/greiner-portal/data/ml"

# Globale Variablen für Modell und Encoder
_model = None
_encoders = None
_training_data = None

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
    """Lädt Trainingsdaten für Statistiken"""
    global _training_data
    if _training_data is None:
        data_path = f"{DATA_DIR}/auftraege_mit_zeiten.csv"
        if os.path.exists(data_path):
            _training_data = pd.read_csv(data_path)
    return _training_data


# =============================================================================
# HEALTH CHECK
# =============================================================================
@ml_api.route('/health', methods=['GET'])
def health_check():
    """Health-Check für ML-API"""
    try:
        model = get_model()
        encoders = get_encoders()
        
        return jsonify({
            'status': 'ok',
            'model_loaded': model is not None,
            'encoders_loaded': encoders is not None,
            'available_endpoints': [
                '/api/ml/auftragsdauer',
                '/api/ml/mechaniker-ranking',
                '/api/ml/statistik'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
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
        "konfidenz": "hoch"
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
        
        # Defaults für optionale Felder
        vorgabe_aw = float(data.get('vorgabe_aw', 5))
        mechaniker_nr = data.get('mechaniker_nr', 5008)
        betrieb = int(data.get('betrieb', 1))
        marke = data.get('marke', 'Opel')
        km_stand = float(data.get('km_stand', 50000))
        fahrzeug_alter = float(data.get('fahrzeug_alter_jahre', 3))
        wochentag = int(data.get('wochentag', 1))
        monat = int(data.get('monat', 6))
        start_stunde = int(data.get('start_stunde', 8))
        
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
    
    Query-Parameter:
    - marke: Filter nach Marke (optional)
    - limit: Anzahl Ergebnisse (default: 20)
    
    Response: Liste der Mechaniker mit Effizienz-Score
    """
    try:
        marke = request.args.get('marke')
        limit = request.args.get('limit', 20, type=int)
        
        df = get_training_data()
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
        
        # Sortieren nach Effizienz (höher = besser)
        ranking = ranking.sort_values('effizienz', ascending=False).head(limit)
        
        result = []
        for _, row in ranking.iterrows():
            result.append({
                'mechaniker_nr': int(row['mechaniker_nr']),
                'anzahl_auftraege': int(row['anzahl_auftraege']),
                'avg_vorgabe_aw': round(row['avg_vorgabe_aw'], 1),
                'avg_ist_minuten': round(row['avg_ist_min'], 1),
                'effizienz_prozent': row['effizienz_prozent'],
                'bewertung': 'schnell' if row['effizienz'] > 1.1 else ('normal' if row['effizienz'] > 0.9 else 'langsam')
            })
        
        return jsonify({
            'success': True,
            'filter_marke': marke,
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
    """Allgemeine ML-Statistiken"""
    try:
        df = get_training_data()
        if df is None:
            return jsonify({'error': 'Trainingsdaten nicht verfügbar'}), 500
        
        return jsonify({
            'success': True,
            'training_datensaetze': len(df),
            'zeitraum': {
                'von': str(df['order_date'].min()),
                'bis': str(df['order_date'].max())
            },
            'mechaniker_anzahl': int(df['mechaniker_nr'].nunique()),
            'marken': df['marke'].value_counts().head(5).to_dict(),
            'durchschnitt': {
                'vorgabe_aw': round(df['vorgabe_aw'].mean(), 1),
                'ist_dauer_min': round(df['ist_dauer_min'].mean(), 1),
                'abweichung_min': round(df['ist_dauer_min'].mean() - df['vorgabe_aw'].mean() * 10, 1)
            },
            'modell_performance': {
                'mae_minuten': 25.3,
                'r2_score': 0.714,
                'verbesserung_vs_vorgabe': '61%'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
