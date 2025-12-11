#!/usr/bin/env python3
"""
=============================================================================
GREINER DRIVE - ML Modell: Auftragsdauer-Vorhersage
=============================================================================
Trainiert ein Modell das vorhersagt wie lange ein Auftrag WIRKLICH dauert.

Features:
- Vorgabe-AW (Hersteller)
- Marke (Opel, Hyundai, etc.)
- Mechaniker
- Wochentag, Uhrzeit
- Fahrzeugalter
- km-Stand

Target:
- IST-Dauer in Minuten
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os

print("=" * 60)
print("GREINER DRIVE - ML Modell Training")
print("=" * 60)

# =============================================================================
# 1. DATEN LADEN
# =============================================================================
print("\n[1/5] Lade Trainingsdaten...")

df = pd.read_csv("/opt/greiner-portal/data/ml/auftraege_mit_zeiten_v2.csv")
print(f"   Datensätze: {len(df):,}")

# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================
print("\n[2/5] Feature Engineering...")

# Nur relevante Spalten
features = ['vorgabe_aw', 'mechaniker_nr', 'betrieb', 'wochentag', 'monat', 
            'start_stunde', 'marke', 'fahrzeug_alter_jahre', 'km_stand']
target = 'ist_dauer_min'

# Fehlende Werte behandeln
df['km_stand'] = df['km_stand'].fillna(df['km_stand'].median())
df['fahrzeug_alter_jahre'] = df['fahrzeug_alter_jahre'].fillna(df['fahrzeug_alter_jahre'].median())
df['marke'] = df['marke'].fillna('Unbekannt')
df['start_stunde'] = df['start_stunde'].fillna(8)

# Kategorische Variablen encodieren
le_marke = LabelEncoder()
df['marke_encoded'] = le_marke.fit_transform(df['marke'].astype(str))

le_mechaniker = LabelEncoder()
df['mechaniker_encoded'] = le_mechaniker.fit_transform(df['mechaniker_nr'].astype(str))

# Feature-Matrix erstellen
X = df[['vorgabe_aw', 'mechaniker_encoded', 'betrieb', 'wochentag', 'monat',
        'start_stunde', 'marke_encoded', 'fahrzeug_alter_jahre', 'km_stand']].copy()

# NaN durch 0 ersetzen
X = X.fillna(0)

y = df[target]

print(f"   Features: {list(X.columns)}")
print(f"   Samples: {len(X):,}")

# =============================================================================
# 3. TRAIN/TEST SPLIT
# =============================================================================
print("\n[3/5] Train/Test Split...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Training: {len(X_train):,}")
print(f"   Test: {len(X_test):,}")

# =============================================================================
# 4. MODELL TRAINIEREN
# =============================================================================
print("\n[4/5] Trainiere Modelle...")

# Random Forest
print("   Training Random Forest...")
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    min_samples_split=10,
    n_jobs=-1,
    random_state=42
)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)

# Gradient Boosting
print("   Training Gradient Boosting...")
gb_model = GradientBoostingRegressor(
    n_estimators=100,
    max_depth=8,
    learning_rate=0.1,
    random_state=42
)
gb_model.fit(X_train, y_train)
gb_pred = gb_model.predict(X_test)

# =============================================================================
# 5. EVALUATION
# =============================================================================
print("\n[5/5] Evaluation...")

def evaluate_model(name, y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"\n   {name}:")
    print(f"      MAE:  {mae:.1f} min (Ø Fehler)")
    print(f"      RMSE: {rmse:.1f} min")
    print(f"      R²:   {r2:.3f} (Erklärungskraft)")
    return mae, rmse, r2

# Baseline: Nur Vorgabe-AW * 10 (als Minuten)
baseline_pred = X_test['vorgabe_aw'] * 10
evaluate_model("Baseline (Vorgabe × 10)", y_test, baseline_pred)

rf_mae, rf_rmse, rf_r2 = evaluate_model("Random Forest", y_test, rf_pred)
gb_mae, gb_rmse, gb_r2 = evaluate_model("Gradient Boosting", y_test, gb_pred)

# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================
print("\n" + "=" * 60)
print("FEATURE IMPORTANCE (Random Forest)")
print("=" * 60)

feature_names = ['vorgabe_aw', 'mechaniker', 'betrieb', 'wochentag', 'monat',
                 'start_stunde', 'marke', 'fahrzeug_alter', 'km_stand']
importances = rf_model.feature_importances_

for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"   {name:20s} {imp:.3f} {bar}")

# =============================================================================
# MODELL SPEICHERN
# =============================================================================
print("\n" + "=" * 60)
print("SPEICHERE MODELLE...")
print("=" * 60)

model_dir = "/opt/greiner-portal/data/ml/models"
os.makedirs(model_dir, exist_ok=True)

# Bestes Modell speichern
best_model = rf_model if rf_mae < gb_mae else gb_model
best_name = "RandomForest" if rf_mae < gb_mae else "GradientBoosting"

with open(f"{model_dir}/auftragsdauer_model.pkl", 'wb') as f:
    pickle.dump(best_model, f)

with open(f"{model_dir}/label_encoders.pkl", 'wb') as f:
    pickle.dump({'marke': le_marke, 'mechaniker': le_mechaniker}, f)

print(f"✅ Bestes Modell: {best_name}")
print(f"✅ Gespeichert: {model_dir}/auftragsdauer_model.pkl")

# =============================================================================
# BEISPIEL-VORHERSAGEN
# =============================================================================
print("\n" + "=" * 60)
print("BEISPIEL-VORHERSAGEN")
print("=" * 60)

# Zufällige Testfälle
sample_indices = np.random.choice(X_test.index, size=5, replace=False)

print(f"\n{'Vorgabe AW':>12} {'Marke':>10} {'Mechaniker':>12} {'IST':>8} {'Vorhersage':>12} {'Fehler':>8}")
print("-" * 70)

for idx in sample_indices:
    row = X_test.loc[idx]
    actual = y_test.loc[idx]
    pred = best_model.predict([row.values])[0]
    error = pred - actual
    
    marke_name = le_marke.inverse_transform([int(row['marke_encoded'])])[0][:10]
    mech_nr = le_mechaniker.inverse_transform([int(row['mechaniker_encoded'])])[0]
    
    print(f"{row['vorgabe_aw']:>12.1f} {marke_name:>10} {mech_nr:>12} {actual:>8.0f} {pred:>12.0f} {error:>+8.0f}")

print("\n✅ MODELL TRAINING ABGESCHLOSSEN!")
