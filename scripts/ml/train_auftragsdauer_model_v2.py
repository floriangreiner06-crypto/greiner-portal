#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GREINER DRIVE - ML Modell V2: Auftragsdauer-Vorhersage (TAG 119)
=============================================================================

Verbesserungen gegenüber V1:
- XGBoost statt RandomForest (bessere Performance)
- 22 Features statt 9
- GridSearchCV für Hyperparameter-Tuning
- 5-Fold Cross-Validation
- Feature Importance Analyse

Target: R² > 0.85 (vorher: 0.749)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# XGBoost importieren (falls verfügbar)
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("WARNUNG: XGBoost nicht installiert. Verwende GradientBoosting als Fallback.")
    print("Installation: pip install xgboost")

# LightGBM importieren (falls verfügbar)
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


# =============================================================================
# KONFIGURATION
# =============================================================================
DATA_PATH = "/opt/greiner-portal/data/ml/auftraege_features_v5.csv"
MODEL_DIR = "/opt/greiner-portal/data/ml/models"
MODEL_VERSION = "v2_tag119"

# Feature-Konfiguration
CATEGORICAL_FEATURES = ['marke', 'auftragstyp', 'labour_type']
NUMERIC_FEATURES = [
    # SOLL-Zeit (wichtigster Prädiktor!)
    'soll_dauer_min', 'soll_aw', 'vorgabe_aw',
    # Auftragsfeatures
    'betrieb', 'anzahl_positionen', 'anzahl_teile', 'charge_type', 'urgency',
    # Zeitfeatures
    'wochentag', 'monat', 'start_stunde', 'kalenderwoche',
    # Fahrzeugfeatures
    'power_kw', 'cubic_capacity', 'km_stand', 'fahrzeug_alter_jahre',
    # Mechanikerfeatures
    'productivity_factor', 'years_experience', 'meister'
]
TARGET = 'ist_dauer_min'


def load_and_prepare_data(filepath):
    """Lädt Daten und bereitet Features vor"""
    print("\n[1/6] DATEN LADEN")
    print("-" * 50)

    df = pd.read_csv(filepath)
    print(f"Datensätze geladen: {len(df):,}")

    # Outlier entfernen (IST-Dauer > 600 Minuten = 10 Stunden)
    initial_count = len(df)
    df = df[df[TARGET] <= 600]
    df = df[df[TARGET] >= 5]  # Mindestens 5 Minuten
    print(f"Nach Outlier-Entfernung: {len(df):,} ({initial_count - len(df)} entfernt)")

    return df


def encode_features(df, label_encoders=None):
    """Encodiert kategorische Features"""
    print("\n[2/6] FEATURE ENCODING")
    print("-" * 50)

    if label_encoders is None:
        label_encoders = {}
        fit_mode = True
    else:
        fit_mode = False

    df_encoded = df.copy()

    for col in CATEGORICAL_FEATURES:
        if col not in df_encoded.columns:
            continue

        if fit_mode:
            le = LabelEncoder()
            df_encoded[f'{col}_encoded'] = le.fit_transform(df_encoded[col].astype(str))
            label_encoders[col] = le
            print(f"  {col}: {len(le.classes_)} Kategorien")
        else:
            le = label_encoders[col]
            # Unbekannte Kategorien auf -1 setzen
            df_encoded[f'{col}_encoded'] = df_encoded[col].apply(
                lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
            )

    return df_encoded, label_encoders


def prepare_feature_matrix(df):
    """Erstellt Feature-Matrix X und Target y"""
    print("\n[3/6] FEATURE MATRIX")
    print("-" * 50)

    # Feature-Spalten zusammenstellen
    feature_cols = NUMERIC_FEATURES.copy()
    for col in CATEGORICAL_FEATURES:
        encoded_col = f'{col}_encoded'
        if encoded_col in df.columns:
            feature_cols.append(encoded_col)

    # Nur vorhandene Spalten verwenden
    available_cols = [c for c in feature_cols if c in df.columns]
    missing_cols = [c for c in feature_cols if c not in df.columns]

    if missing_cols:
        print(f"  WARNUNG: Fehlende Spalten: {missing_cols}")

    X = df[available_cols].copy()

    # NaN behandeln
    X = X.fillna(0)

    y = df[TARGET]

    print(f"  Features: {len(available_cols)}")
    print(f"  Samples: {len(X):,}")
    print(f"  Feature-Liste: {available_cols}")

    return X, y, available_cols


def train_models(X_train, y_train, X_test, y_test, do_grid_search=True):
    """Trainiert verschiedene Modelle und vergleicht sie"""
    print("\n[4/6] MODELL-TRAINING")
    print("-" * 50)

    results = {}

    # ------------- XGBoost -------------
    if HAS_XGBOOST:
        print("\n  Training XGBoost...")

        if do_grid_search:
            # GridSearchCV für beste Hyperparameter
            param_grid = {
                'n_estimators': [100, 200],
                'max_depth': [6, 10, 15],
                'learning_rate': [0.05, 0.1],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            }

            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                random_state=42,
                n_jobs=-1
            )

            print("    GridSearchCV läuft (kann 2-5 Minuten dauern)...")
            grid_search = GridSearchCV(
                xgb_model, param_grid,
                cv=3, scoring='r2', n_jobs=-1, verbose=0
            )
            grid_search.fit(X_train, y_train)

            xgb_best = grid_search.best_estimator_
            print(f"    Beste Parameter: {grid_search.best_params_}")
        else:
            # Schnelles Training mit guten Default-Werten
            xgb_best = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='reg:squarederror',
                random_state=42,
                n_jobs=-1
            )
            xgb_best.fit(X_train, y_train)

        xgb_pred = xgb_best.predict(X_test)
        results['XGBoost'] = {
            'model': xgb_best,
            'predictions': xgb_pred,
            'mae': mean_absolute_error(y_test, xgb_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, xgb_pred)),
            'r2': r2_score(y_test, xgb_pred)
        }
        print(f"    R²: {results['XGBoost']['r2']:.4f}")

    # ------------- LightGBM -------------
    if HAS_LIGHTGBM:
        print("\n  Training LightGBM...")

        lgb_model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=10,
            learning_rate=0.1,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)

        lgb_pred = lgb_model.predict(X_test)
        results['LightGBM'] = {
            'model': lgb_model,
            'predictions': lgb_pred,
            'mae': mean_absolute_error(y_test, lgb_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, lgb_pred)),
            'r2': r2_score(y_test, lgb_pred)
        }
        print(f"    R²: {results['LightGBM']['r2']:.4f}")

    # ------------- Random Forest (Baseline) -------------
    print("\n  Training Random Forest (Baseline)...")

    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        n_jobs=-1,
        random_state=42
    )
    rf_model.fit(X_train, y_train)

    rf_pred = rf_model.predict(X_test)
    results['RandomForest'] = {
        'model': rf_model,
        'predictions': rf_pred,
        'mae': mean_absolute_error(y_test, rf_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, rf_pred)),
        'r2': r2_score(y_test, rf_pred)
    }
    print(f"    R²: {results['RandomForest']['r2']:.4f}")

    # ------------- Gradient Boosting (Fallback) -------------
    print("\n  Training Gradient Boosting...")

    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=8,
        learning_rate=0.1,
        random_state=42
    )
    gb_model.fit(X_train, y_train)

    gb_pred = gb_model.predict(X_test)
    results['GradientBoosting'] = {
        'model': gb_model,
        'predictions': gb_pred,
        'mae': mean_absolute_error(y_test, gb_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, gb_pred)),
        'r2': r2_score(y_test, gb_pred)
    }
    print(f"    R²: {results['GradientBoosting']['r2']:.4f}")

    return results


def cross_validate_best_model(best_model, X, y, cv=5):
    """Führt Cross-Validation für das beste Modell durch"""
    print("\n[5/6] CROSS-VALIDATION (5-Fold)")
    print("-" * 50)

    cv_scores = cross_val_score(best_model, X, y, cv=cv, scoring='r2', n_jobs=-1)

    print(f"  Fold R² Scores: {[f'{s:.4f}' for s in cv_scores]}")
    print(f"  Mean R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    return cv_scores


def analyze_feature_importance(model, feature_names, top_n=15):
    """Analysiert Feature Importance"""
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE")
    print("=" * 60)

    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        print("  Modell unterstützt keine Feature Importance")
        return

    # Sortieren
    indices = np.argsort(importances)[::-1]

    print(f"\nTop {top_n} Features:")
    for i, idx in enumerate(indices[:top_n]):
        bar = "█" * int(importances[idx] * 50)
        print(f"  {i+1:2d}. {feature_names[idx]:25s} {importances[idx]:.4f} {bar}")


def save_model(model, label_encoders, feature_names, metrics, version):
    """Speichert das Modell und zugehörige Daten"""
    print("\n[6/6] MODELL SPEICHERN")
    print("-" * 50)

    os.makedirs(MODEL_DIR, exist_ok=True)

    # Modell speichern
    model_path = f"{MODEL_DIR}/auftragsdauer_model_{version}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  Modell: {model_path}")

    # Label Encoders speichern
    encoders_path = f"{MODEL_DIR}/label_encoders_{version}.pkl"
    with open(encoders_path, 'wb') as f:
        pickle.dump(label_encoders, f)
    print(f"  Encoders: {encoders_path}")

    # Metadata speichern
    metadata = {
        'version': version,
        'feature_names': feature_names,
        'metrics': metrics,
        'model_type': type(model).__name__,
        'created_at': pd.Timestamp.now().isoformat()
    }
    metadata_path = f"{MODEL_DIR}/model_metadata_{version}.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"  Metadata: {metadata_path}")

    # Symlink für aktuelles Modell
    current_link = f"{MODEL_DIR}/auftragsdauer_model.pkl"
    if os.path.exists(current_link):
        os.remove(current_link)
    os.symlink(model_path, current_link)
    print(f"  Symlink: {current_link} -> {model_path}")


def print_comparison(results, y_test):
    """Druckt Vergleichstabelle aller Modelle"""
    print("\n" + "=" * 70)
    print("MODELL-VERGLEICH")
    print("=" * 70)

    # Baseline: Nur Vorgabe-AW * 10
    # (nicht mehr verfügbar ohne X_test)

    print(f"\n{'Modell':<20} {'MAE (min)':<12} {'RMSE (min)':<12} {'R²':<10}")
    print("-" * 54)

    for name, data in sorted(results.items(), key=lambda x: -x[1]['r2']):
        print(f"{name:<20} {data['mae']:<12.1f} {data['rmse']:<12.1f} {data['r2']:<10.4f}")

    # Bestes Modell markieren
    best_name = max(results.keys(), key=lambda k: results[k]['r2'])
    best_r2 = results[best_name]['r2']

    print("\n" + "=" * 70)
    print(f"BESTES MODELL: {best_name} (R² = {best_r2:.4f})")
    print("=" * 70)

    # Verbesserung gegenüber V1
    v1_r2 = 0.749  # Aus altem Training
    improvement = (best_r2 - v1_r2) / v1_r2 * 100
    print(f"\nVerbesserung gegenüber V1 (R² = {v1_r2:.3f}):")
    print(f"  → +{improvement:.1f}% relative Verbesserung")

    return best_name


def main(data_path=DATA_PATH, do_grid_search=True):
    """Hauptfunktion"""
    print("=" * 70)
    print("GREINER DRIVE - ML Modell Training V2 (TAG 119)")
    print("=" * 70)

    # 1. Daten laden
    df = load_and_prepare_data(data_path)

    # 2. Features encodieren
    df_encoded, label_encoders = encode_features(df)

    # 3. Feature Matrix erstellen
    X, y, feature_names = prepare_feature_matrix(df_encoded)

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\n  Training Set: {len(X_train):,}")
    print(f"  Test Set: {len(X_test):,}")

    # 4. Modelle trainieren
    results = train_models(X_train, y_train, X_test, y_test, do_grid_search)

    # 5. Vergleich und bestes Modell wählen
    best_name = print_comparison(results, y_test)
    best_model = results[best_name]['model']
    best_metrics = {
        'mae': results[best_name]['mae'],
        'rmse': results[best_name]['rmse'],
        'r2': results[best_name]['r2']
    }

    # 6. Cross-Validation für bestes Modell
    cv_scores = cross_validate_best_model(best_model, X, y)
    best_metrics['cv_mean'] = cv_scores.mean()
    best_metrics['cv_std'] = cv_scores.std()

    # 7. Feature Importance
    analyze_feature_importance(best_model, feature_names)

    # 8. Modell speichern
    save_model(best_model, label_encoders, feature_names, best_metrics, MODEL_VERSION)

    # Beispiel-Vorhersagen
    print("\n" + "=" * 70)
    print("BEISPIEL-VORHERSAGEN")
    print("=" * 70)

    sample_indices = np.random.choice(X_test.index, size=min(5, len(X_test)), replace=False)
    print(f"\n{'AW':<8} {'IST (min)':<12} {'Vorhersage':<12} {'Fehler':<10}")
    print("-" * 42)

    for idx in sample_indices:
        row = X_test.loc[idx]
        actual = y_test.loc[idx]
        pred = best_model.predict([row.values])[0]
        error = pred - actual

        aw = row.get('vorgabe_aw', row.get('total_aw', 0))
        print(f"{aw:<8.1f} {actual:<12.0f} {pred:<12.0f} {error:>+10.0f}")

    print("\n" + "=" * 70)
    print("TRAINING ABGESCHLOSSEN!")
    print("=" * 70)

    return best_model, label_encoders, feature_names


if __name__ == "__main__":
    # Kommandozeilenargumente
    do_grid_search = '--fast' not in sys.argv

    # Daten-Pfad (erstes Argument das kein Flag ist)
    data_path = DATA_PATH
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            data_path = arg
            break

    if '--fast' in sys.argv:
        print("HINWEIS: Schnellmodus (ohne GridSearch)")

    main(data_path, do_grid_search)
