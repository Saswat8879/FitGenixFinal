import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    DIABETES_CSV, DIABETES_FEATURES, DIABETES_TARGET,
    DIABETES_ZERO_IMPUTE_COLS, PROCESSED_DIR, RANDOM_SEED, TEST_SIZE,
)


def load_and_preprocess_diabetes() -> dict:

    df = pd.read_csv(DIABETES_CSV)
    assert list(df.columns) == DIABETES_FEATURES + [DIABETES_TARGET], \
        f"Unexpected columns: {list(df.columns)}"

    # Replace zeros with NaN for columns where 0 is physiologically impossible
    for col in DIABETES_ZERO_IMPUTE_COLS:
        df[col] = df[col].replace(0, np.nan)

    X = df[DIABETES_FEATURES].copy()
    y = df[DIABETES_TARGET].values

    # Impute missing values (median strategy — robust to outliers)
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=DIABETES_FEATURES)

    # Feature engineering
    X_imputed["BMI_Age"] = X_imputed["BMI"] * X_imputed["Age"] / 100.0
    X_imputed["Glucose_BMI_ratio"] = X_imputed["Glucose"] / X_imputed["BMI"].clip(lower=1)

    feature_names = list(X_imputed.columns)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_imputed.values, y, test_size=TEST_SIZE,
        stratify=y, random_state=RANDOM_SEED,
    )

    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Save artifacts
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(imputer, PROCESSED_DIR / "diabetes_imputer.joblib")
    joblib.dump(scaler, PROCESSED_DIR / "diabetes_scaler.joblib")
    joblib.dump(feature_names, PROCESSED_DIR / "diabetes_feature_names.joblib")

    print(f"[Diabetes Preprocess] Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"  Positive rate — train: {y_train.mean():.3f}, test: {y_test.mean():.3f}")

    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "scaler": scaler, "imputer": imputer,
        "feature_names": feature_names,
    }


if __name__ == "__main__":
    data = load_and_preprocess_diabetes()
    # Save processed arrays for quick re-use
    np.savez(
        PROCESSED_DIR / "diabetes_processed.npz",
        X_train=data["X_train"], X_test=data["X_test"],
        y_train=data["y_train"], y_test=data["y_test"],
    )
    print(f"Saved to {PROCESSED_DIR / 'diabetes_processed.npz'}")
