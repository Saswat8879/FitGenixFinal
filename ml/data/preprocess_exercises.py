"""
FitGenix ML — Exercise Dataset Preprocessing
Loads megaGymDataset.csv, cleans, and creates exercise feature vectors.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    EXERCISE_CSV, EXERCISE_BODY_PARTS, EXERCISE_EQUIPMENT,
    EXERCISE_TYPES, EXERCISE_LEVELS, PROCESSED_DIR,
)


def load_and_preprocess_exercises() -> pd.DataFrame:
    """
    Load megaGymDataset.csv and produce a clean exercise table with features.
    Returns DataFrame with exercise_id and feature columns.
    """
    df = pd.read_csv(EXERCISE_CSV)

    # Drop unnamed index column if present
    if "Unnamed: 0" in df.columns or df.columns[0] == "":
        df = df.iloc[:, 1:]

    # Rename for consistency
    df.columns = [c.strip() for c in df.columns]
    col_map = {
        "Title": "name", "Desc": "description", "Type": "type",
        "BodyPart": "body_part", "Equipment": "equipment",
        "Level": "level", "Rating": "rating", "RatingDesc": "rating_desc",
    }
    df = df.rename(columns=col_map)

    # Drop rows with missing name
    df = df.dropna(subset=["name"]).reset_index(drop=True)
    df["exercise_id"] = df.index

    # Clean type → map to our categories
    df["type"] = df["type"].fillna("Strength").str.strip()
    type_map = {
        "Strength": "Strength", "Cardio": "Cardio", "Stretching": "Flexibility",
        "Plyometrics": "Strength", "Powerlifting": "Strength",
        "Olympic Weightlifting": "Strength", "Strongman": "Strength",
    }
    df["type"] = df["type"].map(lambda x: type_map.get(x, "Strength"))

    # Clean body_part → map to our categories
    df["body_part"] = df["body_part"].fillna("Other").str.strip()
    bp_map = {}
    for bp in EXERCISE_BODY_PARTS:
        bp_map[bp] = bp
    bp_map.update({
        "Quadriceps": "Legs", "Hamstrings": "Legs", "Calves": "Legs",
        "Glutes": "Legs", "Adductors": "Legs",
        "Middle Back": "Back", "Lower Back": "Back", "Lats": "Back", "Traps": "Back",
        "Biceps": "Arms", "Triceps": "Arms", "Forearms": "Arms",
        "Neck": "Other",
    })
    df["body_part"] = df["body_part"].map(lambda x: bp_map.get(x, "Other"))

    # Clean equipment
    df["equipment"] = df["equipment"].fillna("None").str.strip()
    eq_map = {}
    for eq in EXERCISE_EQUIPMENT:
        eq_map[eq] = eq
    eq_map.update({
        "Body Only": "None", "Other": "None", "Cable": "Machine",
        "E-Z Curl Bar": "Barbell", "Kettlebells": "Dumbbell",
        "Exercise Ball": "None", "Medicine Ball": "None",
        "Foam Roll": "None",
    })
    df["equipment"] = df["equipment"].map(lambda x: eq_map.get(x, "None"))

    # Level → numeric
    df["level"] = df["level"].fillna("Intermediate").str.strip()
    df["difficulty"] = df["level"].map(EXERCISE_LEVELS).fillna(2).astype(int)

    # Rating → numeric, fill missing
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    rating_max = df["rating"].max()
    if rating_max > 0:
        df["rating_norm"] = df["rating"] / rating_max
    else:
        df["rating_norm"] = 0.0

    # Is compound (heuristic: "Full Body" or exercises with multiple body parts in name)
    compound_keywords = ["squat", "deadlift", "bench press", "clean", "snatch",
                         "thruster", "burpee", "row", "pull-up", "push-up"]
    df["is_compound"] = df["name"].str.lower().apply(
        lambda n: int(any(kw in n for kw in compound_keywords))
    )

    # Estimated cardio intensity (heuristic)
    df["cardio_intensity"] = 0.0
    df.loc[df["type"] == "Cardio", "cardio_intensity"] = 0.7
    cardio_keywords = ["run", "sprint", "jump", "burpee", "cycle", "row"]
    for kw in cardio_keywords:
        mask = df["name"].str.lower().str.contains(kw, na=False)
        df.loc[mask, "cardio_intensity"] = df.loc[mask, "cardio_intensity"].clip(lower=0.5) + 0.2

    df["cardio_intensity"] = df["cardio_intensity"].clip(0, 1)

    # Injury risk heuristic
    high_risk_kw = ["deadlift", "snatch", "clean and jerk", "behind the neck"]
    df["injury_risk"] = 0.2
    for kw in high_risk_kw:
        df.loc[df["name"].str.lower().str.contains(kw, na=False), "injury_risk"] = 0.6
    df.loc[df["difficulty"] == 3, "injury_risk"] += 0.1
    df["injury_risk"] = df["injury_risk"].clip(0, 1)

    # One-hot encode type, body_part, equipment
    for col, categories in [("type", EXERCISE_TYPES), ("body_part", EXERCISE_BODY_PARTS),
                            ("equipment", EXERCISE_EQUIPMENT)]:
        for cat in categories:
            df[f"{col}_{cat}"] = (df[col] == cat).astype(int)

    # Select final feature columns
    feature_cols = (
        [f"type_{t}" for t in EXERCISE_TYPES] +
        [f"body_part_{bp}" for bp in EXERCISE_BODY_PARTS] +
        [f"equipment_{eq}" for eq in EXERCISE_EQUIPMENT] +
        ["difficulty", "is_compound", "cardio_intensity", "injury_risk", "rating_norm"]
    )

    # Save
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df[["exercise_id", "name", "type", "body_part", "equipment", "level",
        "description"] + feature_cols].to_csv(
        PROCESSED_DIR / "exercises_clean.csv", index=False
    )

    exercise_features = df[feature_cols].values.astype(np.float32)
    np.save(PROCESSED_DIR / "exercise_features.npy", exercise_features)
    joblib.dump(feature_cols, PROCESSED_DIR / "exercise_feature_names.joblib")

    print(f"[Exercise Preprocess] {len(df)} exercises, {len(feature_cols)} features")
    print(f"  Types: {df['type'].value_counts().to_dict()}")
    print(f"  Body parts: {df['body_part'].value_counts().to_dict()}")
    print(f"  Equipment: {df['equipment'].value_counts().to_dict()}")

    return df


if __name__ == "__main__":
    load_and_preprocess_exercises()
