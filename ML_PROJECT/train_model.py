"""
YouTube View Predictor - Model Training Script
Trains HistGradientBoostingRegressor and saves model + encoder to pkl files.
Run once before starting the web app:  python3 train_model.py
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import r2_score, mean_absolute_error

DATA_PATH = os.path.join(os.path.dirname(__file__), "data_featured.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "encoder.pkl")
COLUMNS_PATH = os.path.join(os.path.dirname(__file__), "feature_columns.pkl")

print("Loading dataset...")
data = pd.read_csv(DATA_PATH, sep=None, engine="python")
print(f"Dataset loaded: {data.shape[0]} rows, {data.shape[1]} columns")

# ── Feature selection (HistGradientModel.ipynb config) ──────────────────────
drop_cols = [
    "video_title", "upload_date", "thumbnail_url", "desc", "tags",
    "video_id", "thumb_hex", "views",
    "follower_count", "thumb_r", "thumb_g", "thumb_b",
]
X = data.drop(columns=[c for c in drop_cols if c in data.columns])
y = np.log1p(data["views"])

# ── Categorical encoding ─────────────────────────────────────────────────────
categorical_cols = ["is_shorts", "category", "default_language", "has_manuel_subtitle"]
cat_cols_present = [c for c in categorical_cols if c in X.columns]

encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
X[cat_cols_present] = encoder.fit_transform(X[cat_cols_present].astype(str))

feature_columns = list(X.columns)
cat_idx = [X.columns.get_loc(col) for col in cat_cols_present]

print(f"Features: {len(feature_columns)}")
print("Feature list:", feature_columns)

# ── Train/test split ─────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ── Model (same config as HistGradientModel.ipynb) ───────────────────────────
print("\nTraining model (this may take a minute)...")
model = HistGradientBoostingRegressor(
    categorical_features=cat_idx,
    max_iter=1500,
    learning_rate=0.04,
    max_depth=15,
    max_leaf_nodes=127,
    min_samples_leaf=15,
    l2_regularization=0.8,
    early_stopping=True,
    random_state=42,
)
model.fit(X_train, y_train)

# ── Evaluate ─────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
print(f"\nModel Performance:")
print(f"  R² Score: {r2:.4f}")
print(f"  MAE (views): {mae:,.0f}")

# ── Save artifacts ───────────────────────────────────────────────────────────
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)
with open(ENCODER_PATH, "wb") as f:
    pickle.dump({"encoder": encoder, "categorical_cols": cat_cols_present}, f)
with open(COLUMNS_PATH, "wb") as f:
    pickle.dump(feature_columns, f)

print(f"\nSaved:")
print(f"  model    → {MODEL_PATH}")
print(f"  encoder  → {ENCODER_PATH}")
print(f"  columns  → {COLUMNS_PATH}")
print("\nDone! Now run: python3 predict_api.py")
