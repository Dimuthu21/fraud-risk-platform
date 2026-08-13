"""
src/features.py

Single source of truth for feature engineering — used by the training notebook
AND the FastAPI service, so a live prediction is guaranteed to see the exact
same transformations the model was trained on.
"""

import json
import os
import pandas as pd

SENTINEL_COLS = [
    'prev_address_months_count',
    'bank_months_count',
    'current_address_months_count',
    'session_length_in_minutes',
    'device_distinct_emails_8w',
]

CATEGORICAL_COLS = ['payment_type', 'employment_status', 'housing_status', 'source', 'device_os']

# Persisted list of every column the trained model expects, in order.
# Written once after training; read every time the API needs to align a new request.
TRAIN_COLUMNS_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'train_columns.json')


def add_sentinel_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `<col>_is_unknown` flag for every -1-sentinel column.
    We deliberately do NOT impute here — tree models (our production model)
    handle -1 fine as a natural split point, and the flag preserves the signal
    that 'unknown' itself can carry (e.g. no address history = newer/riskier profile)."""
    df = df.copy()
    for col in SENTINEL_COLS:
        df[f'{col}_is_unknown'] = (df[col] == -1).astype(int)
    return df


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Hand-engineered features on top of the raw + flagged columns."""
    df = df.copy()
    df['velocity_accel_6h_vs_24h'] = df['velocity_6h'] - (df['velocity_24h'] / 4)
    df['credit_to_income_ratio'] = df['proposed_credit_limit'] / (df['income'] + 0.01)
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode the low-cardinality categorical columns."""
    return pd.get_dummies(df, columns=CATEGORICAL_COLS, drop_first=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Full pipeline: sentinel flags -> engineered ratios -> one-hot encoding.
    This is the canonical pipeline for the production (tree-based) model."""
    df = add_sentinel_flags(df)
    df = add_engineered_features(df)
    df = encode_categoricals(df)
    return df


def save_train_columns(train_df: pd.DataFrame, target_col: str = 'fraud_bool'):
    """Call this ONCE, right after finalizing train_df in training.
    Persists the exact column schema the model was trained on."""
    cols = [c for c in train_df.columns if c != target_col]
    os.makedirs(os.path.dirname(TRAIN_COLUMNS_PATH), exist_ok=True)
    with open(TRAIN_COLUMNS_PATH, 'w') as f:
        json.dump(cols, f)


def load_train_columns() -> list:
    with open(TRAIN_COLUMNS_PATH, 'r') as f:
        return json.load(f)


def engineer_features_for_inference(raw_row: dict) -> pd.DataFrame:
    """What the FastAPI /predict endpoint calls. Takes one raw transaction
    (a dict matching the request schema), runs it through the same pipeline,
    then reindexes onto the exact training columns — any category the model
    never saw in training is safely filled with 0 instead of crashing or
    silently misaligning columns."""
    df = pd.DataFrame([raw_row])
    df = engineer_features(df)
    train_cols = load_train_columns()
    df = df.reindex(columns=train_cols, fill_value=0)
    return df