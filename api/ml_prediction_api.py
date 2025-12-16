#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - ML Prediction API (TAG 119)
=============================================================================
API-Endpunkte für Auftragsdauer-Vorhersagen.

Endpunkte:
- GET  /api/ml/predict/auftragsdauer - Einzelvorhersage
- POST /api/ml/predict/batch - Batch-Vorhersagen
- GET  /api/ml/model/info - Modell-Informationen
- GET  /api/ml/model/features - Feature-Beschreibung
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
import pickle
import os
import numpy as np
import pandas as pd
from datetime import datetime

ml_prediction_api = Blueprint('ml_prediction_api', __name__, url_prefix='/api/ml')

# Modell-Pfade
MODEL_DIR = "/opt/greiner-portal/data/ml/models"
MODEL_PATH = f"{MODEL_DIR}/auftragsdauer_model.pkl"
ENCODERS_PATH = f"{MODEL_DIR}/label_encoders_v2_tag119.pkl"
METADATA_PATH = f"{MODEL_DIR}/model_metadata_v2_tag119.pkl"

# Globale Variablen für geladenes Modell
_model = None
_encoders = None
_metadata = None


def load_model():
    """Lädt das Modell lazy beim ersten Request"""
    global _model, _encoders, _metadata

    if _model is not None:
        return _model, _encoders, _metadata

    try:
        # Modell laden
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                _model = pickle.load(f)
            print(f"ML-Modell geladen: {MODEL_PATH}")
        else:
            print(f"WARNUNG: Modell nicht gefunden: {MODEL_PATH}")
            return None, None, None

        # Encoders laden
        if os.path.exists(ENCODERS_PATH):
            with open(ENCODERS_PATH, 'rb') as f:
                _encoders = pickle.load(f)

        # Metadata laden
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'rb') as f:
                _metadata = pickle.load(f)

        return _model, _encoders, _metadata

    except Exception as e:
        print(f"Fehler beim Laden des ML-Modells: {e}")
        return None, None, None


def prepare_features(data, encoders=None):
    """
    Bereitet Features für Vorhersage vor.

    Erwartet dict mit:
    - vorgabe_aw: float (Arbeitswerte)
    - marke: str (z.B. "OPEL")
    - betrieb: int (1=Deggendorf, 3=Landau)
    - mechaniker_nr: int (optional)
    - ...weitere Features...
    """
    # Standardwerte
    defaults = {
        'vorgabe_aw': 10,
        'betrieb': 1,
        'wochentag': datetime.now().weekday(),
        'monat': datetime.now().month,
        'start_stunde': 8,
        'kalenderwoche': datetime.now().isocalendar()[1],
        'urgency': 0,
        'anzahl_positionen': 1,
        'anzahl_teile': 0,
        'charge_type': 0,
        'power_kw': 100,
        'cubic_capacity': 1500,
        'km_stand': 50000,
        'fahrzeug_alter_jahre': 5,
        'productivity_factor': 1.0,
        'years_experience': 5,
        'meister': 0,
        'marke': 'OPEL',
        'auftragstyp': 'W',
        'labour_type': 'N'
    }

    # Werte übernehmen
    features = defaults.copy()
    for key, value in data.items():
        if key in features:
            features[key] = value

    # Kategorische Features encodieren
    if encoders:
        for cat_col in ['marke', 'auftragstyp', 'labour_type']:
            if cat_col in encoders:
                le = encoders[cat_col]
                val = str(features.get(cat_col, ''))
                if val in le.classes_:
                    features[f'{cat_col}_encoded'] = le.transform([val])[0]
                else:
                    features[f'{cat_col}_encoded'] = 0  # Default für unbekannte

    return features


def get_feature_vector(features, feature_names):
    """Erstellt Feature-Vektor in der richtigen Reihenfolge"""
    vector = []
    for name in feature_names:
        if name in features:
            vector.append(features[name])
        elif name.endswith('_encoded'):
            # Kategorische Features
            base_name = name.replace('_encoded', '')
            vector.append(features.get(f'{base_name}_encoded', 0))
        else:
            vector.append(0)
    return np.array(vector).reshape(1, -1)


@ml_prediction_api.route('/predict/auftragsdauer', methods=['GET', 'POST'])
def predict_auftragsdauer():
    """
    Vorhersage der Auftragsdauer.

    GET Parameter oder POST JSON:
    - vorgabe_aw: Arbeitswerte (float, required)
    - marke: Fahrzeugmarke (str, optional)
    - betrieb: 1=Deggendorf, 3=Landau (int, optional)
    - mechaniker_nr: Mechaniker-Nummer (int, optional)
    - urgency: Dringlichkeit 0-3 (int, optional)
    - ...weitere Features...

    Returns:
    {
        "success": true,
        "prediction": {
            "ist_dauer_min": 45,
            "ist_dauer_formatted": "45 min",
            "confidence": "high"
        },
        "input": {...}
    }
    """
    model, encoders, metadata = load_model()

    if model is None:
        return jsonify({
            'success': False,
            'error': 'ML-Modell nicht verfügbar'
        }), 503

    try:
        # Daten aus Request
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = {
                'vorgabe_aw': request.args.get('vorgabe_aw', type=float),
                'marke': request.args.get('marke'),
                'betrieb': request.args.get('betrieb', type=int),
                'mechaniker_nr': request.args.get('mechaniker_nr', type=int),
                'urgency': request.args.get('urgency', type=int),
                'anzahl_positionen': request.args.get('anzahl_positionen', type=int),
                'km_stand': request.args.get('km_stand', type=int),
                'fahrzeug_alter_jahre': request.args.get('fahrzeug_alter', type=float)
            }
            # None-Werte entfernen
            data = {k: v for k, v in data.items() if v is not None}

        # Mindestens vorgabe_aw erforderlich
        if 'vorgabe_aw' not in data:
            return jsonify({
                'success': False,
                'error': 'vorgabe_aw ist erforderlich'
            }), 400

        # Features vorbereiten
        features = prepare_features(data, encoders)

        # Feature-Vektor erstellen
        if metadata and 'feature_names' in metadata:
            feature_names = metadata['feature_names']
        else:
            # Fallback: Standard-Feature-Liste
            feature_names = [
                'vorgabe_aw', 'betrieb', 'wochentag', 'monat', 'start_stunde',
                'kalenderwoche', 'urgency', 'anzahl_positionen', 'anzahl_teile',
                'charge_type', 'power_kw', 'cubic_capacity', 'km_stand',
                'fahrzeug_alter_jahre', 'productivity_factor', 'years_experience',
                'meister', 'marke_encoded', 'auftragstyp_encoded', 'labour_type_encoded'
            ]

        X = get_feature_vector(features, feature_names)

        # Vorhersage
        prediction = model.predict(X)[0]

        # Auf realistische Werte begrenzen
        prediction = max(5, min(600, prediction))

        # Confidence basierend auf Varianz
        confidence = 'high' if 10 < prediction < 300 else 'medium'

        return jsonify({
            'success': True,
            'prediction': {
                'ist_dauer_min': round(prediction, 0),
                'ist_dauer_formatted': f"{int(prediction)} min",
                'confidence': confidence
            },
            'input': data,
            'model_version': metadata.get('version', 'unknown') if metadata else 'unknown'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ml_prediction_api.route('/predict/batch', methods=['POST'])
@login_required
def predict_batch():
    """
    Batch-Vorhersagen für mehrere Aufträge.

    POST JSON:
    {
        "auftraege": [
            {"vorgabe_aw": 10, "marke": "OPEL", ...},
            {"vorgabe_aw": 20, "marke": "HYUNDAI", ...}
        ]
    }

    Returns:
    {
        "success": true,
        "predictions": [
            {"index": 0, "ist_dauer_min": 45},
            {"index": 1, "ist_dauer_min": 90}
        ]
    }
    """
    model, encoders, metadata = load_model()

    if model is None:
        return jsonify({
            'success': False,
            'error': 'ML-Modell nicht verfügbar'
        }), 503

    try:
        data = request.get_json() or {}
        auftraege = data.get('auftraege', [])

        if not auftraege:
            return jsonify({
                'success': False,
                'error': 'Keine Aufträge angegeben'
            }), 400

        # Feature-Namen
        if metadata and 'feature_names' in metadata:
            feature_names = metadata['feature_names']
        else:
            feature_names = [
                'vorgabe_aw', 'betrieb', 'wochentag', 'monat', 'start_stunde',
                'kalenderwoche', 'urgency', 'anzahl_positionen', 'anzahl_teile',
                'charge_type', 'power_kw', 'cubic_capacity', 'km_stand',
                'fahrzeug_alter_jahre', 'productivity_factor', 'years_experience',
                'meister', 'marke_encoded', 'auftragstyp_encoded', 'labour_type_encoded'
            ]

        predictions = []
        for i, auftrag in enumerate(auftraege):
            features = prepare_features(auftrag, encoders)
            X = get_feature_vector(features, feature_names)
            pred = model.predict(X)[0]
            pred = max(5, min(600, pred))

            predictions.append({
                'index': i,
                'ist_dauer_min': round(pred, 0),
                'vorgabe_aw': auftrag.get('vorgabe_aw', 0)
            })

        return jsonify({
            'success': True,
            'predictions': predictions,
            'count': len(predictions)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ml_prediction_api.route('/model/info', methods=['GET'])
def model_info():
    """
    Gibt Informationen über das geladene Modell zurück.
    """
    model, encoders, metadata = load_model()

    if model is None:
        return jsonify({
            'success': False,
            'error': 'ML-Modell nicht verfügbar',
            'model_path': MODEL_PATH,
            'model_exists': os.path.exists(MODEL_PATH)
        }), 503

    info = {
        'success': True,
        'model': {
            'type': type(model).__name__,
            'version': metadata.get('version', 'unknown') if metadata else 'unknown',
            'created_at': metadata.get('created_at', 'unknown') if metadata else 'unknown'
        }
    }

    if metadata and 'metrics' in metadata:
        info['metrics'] = metadata['metrics']

    if metadata and 'feature_names' in metadata:
        info['features'] = {
            'count': len(metadata['feature_names']),
            'names': metadata['feature_names']
        }

    return jsonify(info)


@ml_prediction_api.route('/model/features', methods=['GET'])
def model_features():
    """
    Beschreibung aller verfügbaren Features.
    """
    features = {
        'numeric': {
            'vorgabe_aw': 'Arbeitswerte (Herstellervorgabe)',
            'betrieb': 'Standort (1=Deggendorf, 3=Landau)',
            'wochentag': 'Wochentag (0=Mo, 6=So)',
            'monat': 'Monat (1-12)',
            'start_stunde': 'Startzeit (0-23)',
            'kalenderwoche': 'Kalenderwoche (1-52)',
            'urgency': 'Dringlichkeit (0=normal, 3=hoch)',
            'anzahl_positionen': 'Anzahl Arbeitspositionen',
            'anzahl_teile': 'Anzahl Ersatzteile',
            'charge_type': 'Lohnart/Kostenträger',
            'power_kw': 'Motorleistung in kW',
            'cubic_capacity': 'Hubraum in ccm',
            'km_stand': 'Kilometerstand',
            'fahrzeug_alter_jahre': 'Fahrzeugalter in Jahren',
            'productivity_factor': 'Produktivitätsfaktor Mechaniker',
            'years_experience': 'Berufserfahrung Mechaniker (Jahre)',
            'meister': 'Ist Meister (0/1)'
        },
        'categorical': {
            'marke': 'Fahrzeugmarke (OPEL, HYUNDAI, etc.)',
            'auftragstyp': 'Auftragsklassifizierung (W=Werkstatt, G=Garantie, etc.)',
            'labour_type': 'Arbeitstyp (N=Normal, etc.)'
        }
    }

    return jsonify({
        'success': True,
        'features': features
    })


@ml_prediction_api.route('/health', methods=['GET'])
def health():
    """Health-Check für ML-API"""
    model, _, metadata = load_model()

    if model is None:
        return jsonify({
            'status': 'degraded',
            'model_loaded': False,
            'error': 'Modell nicht geladen'
        }), 503

    return jsonify({
        'status': 'ok',
        'model_loaded': True,
        'model_type': type(model).__name__,
        'version': metadata.get('version', 'unknown') if metadata else 'unknown'
    })
