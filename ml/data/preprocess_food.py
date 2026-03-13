"""
FitGenix ML — Food/Nutrition Dataset Preprocessing
Loads USDA FoodData Central + IFCT2017, builds compact nutrition table.
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import joblib
import sys, os
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    USDA_DIR, IFCT_CSV, FOOD_NUTRITION_COLS, FOOD_DIET_TAGS,
    MEAL_TYPES, CUISINE_TYPES, PROCESSED_DIR,
)


def load_usda_foods(max_foods: int = 3000) -> pd.DataFrame:
    """
    Load USDA FoodData Central and extract a compact nutrition table.
    Uses the nutrient.csv + food_nutrient.csv + food.csv + food_category.csv.
    Since food.csv and food_nutrient.csv are large, we use chunked reading.
    """
    # Load nutrient definitions
    nutrients_df = pd.read_csv(USDA_DIR / "nutrient.csv")

    # Map nutrient IDs to our columns
    nutrient_map = {
        1008: "calories",       # Energy (kcal)
        1003: "protein_g",      # Protein
        1005: "carbs_g",        # Carbohydrate
        1004: "fat_g",          # Total lipid (fat)
        1079: "fiber_g",        # Fiber, total dietary
        2000: "sugar_g",        # Sugars, total
        1093: "sodium_mg",      # Sodium
        1258: "sat_fat_g",      # Fatty acids, total saturated
        1253: "cholesterol_mg", # Cholesterol
        1092: "potassium_mg",   # Potassium
    }
    target_nutrient_ids = set(nutrient_map.keys())

    # Load food categories
    cat_df = pd.read_csv(USDA_DIR / "food_category.csv")
    cat_dict = dict(zip(cat_df["id"], cat_df["description"]))

    # Load food_nutrient in chunks (it's very large)
    print("[Food Preprocess] Reading food_nutrient.csv in chunks...")
    nutrient_data = {}
    chunk_size = 100_000
    try:
        for chunk in tqdm(pd.read_csv(USDA_DIR / "food_nutrient.csv", chunksize=chunk_size),
                          desc="Reading food_nutrient.csv", unit="chunk"):
            # Filter to target nutrients
            mask = chunk["nutrient_id"].isin(target_nutrient_ids)
            filtered = chunk[mask][["fdc_id", "nutrient_id", "amount"]].copy()
            for _, row in filtered.iterrows():
                fdc_id = int(row["fdc_id"])
                col_name = nutrient_map.get(int(row["nutrient_id"]))
                if col_name:
                    if fdc_id not in nutrient_data:
                        nutrient_data[fdc_id] = {}
                    nutrient_data[fdc_id][col_name] = float(row["amount"])

            if len(nutrient_data) >= max_foods * 3:
                break
    except Exception as e:
        print(f"  Warning reading food_nutrient.csv: {e}")
        print("  Proceeding with partial data...")

    # Load food names in chunks
    print("[Food Preprocess] Reading food.csv in chunks...")
    food_records = []
    try:
        for chunk in tqdm(pd.read_csv(USDA_DIR / "food.csv", chunksize=chunk_size),
                          desc="Reading food.csv", unit="chunk"):
            # Only keep foods that have nutrient data
            valid = chunk[chunk["fdc_id"].isin(nutrient_data.keys())]
            for _, row in valid.iterrows():
                fdc_id = int(row["fdc_id"])
                record = {
                    "food_id": fdc_id,
                    "name": str(row.get("description", "")),
                    "category_id": row.get("food_category_id", None),
                    **nutrient_data.get(fdc_id, {}),
                }
                food_records.append(record)
            if len(food_records) >= max_foods:
                break
    except Exception as e:
        print(f"  Warning reading food.csv: {e}")

    usda_df = pd.DataFrame(food_records[:max_foods])

    # Map category
    if "category_id" in usda_df.columns:
        usda_df["category"] = usda_df["category_id"].map(cat_dict).fillna("Other")
    else:
        usda_df["category"] = "Other"

    # Fill missing nutrition with 0
    for col in FOOD_NUTRITION_COLS:
        if col not in usda_df.columns:
            usda_df[col] = 0.0
        usda_df[col] = usda_df[col].fillna(0.0)

    usda_df["source"] = "USDA"
    usda_df["cuisine"] = "American"

    print(f"  Loaded {len(usda_df)} USDA foods")
    return usda_df


def load_ifct_foods(max_foods: int = 1000) -> pd.DataFrame:
    """Load Indian Food Composition Tables (IFCT2017)."""
    df = pd.read_csv(IFCT_CSV)

    # Map IFCT columns to our schema
    col_map = {
        "code": "food_id",
        "name": "name",
        "enerc": "calories",     # Energy kcal
        "protcnt": "protein_g",
        "choavldf": "carbs_g",   # Available carbohydrates
        "fatce": "fat_g",
        "fibtg": "fiber_g",      # Total fiber
        "fasat": "sat_fat_g",
        "cholc": "cholesterol_mg",
        "na": "sodium_mg",
        "k": "potassium_mg",
    }

    ifct_df = pd.DataFrame()
    for src_col, tgt_col in col_map.items():
        if src_col in df.columns:
            ifct_df[tgt_col] = pd.to_numeric(df[src_col], errors="coerce").fillna(0)
        else:
            ifct_df[tgt_col] = 0

    if "name" in df.columns:
        ifct_df["name"] = df["name"]
    if "code" in df.columns:
        ifct_df["food_id"] = df["code"]

    # Sugar approximation (not directly in IFCT — use free sugars if available)
    ifct_df["sugar_g"] = 0.0
    if "fsugar" in df.columns:
        ifct_df["sugar_g"] = pd.to_numeric(df["fsugar"], errors="coerce").fillna(0)

    # Fill missing
    for col in FOOD_NUTRITION_COLS:
        if col not in ifct_df.columns:
            ifct_df[col] = 0.0

    ifct_df["source"] = "IFCT"
    ifct_df["cuisine"] = "Indian"
    ifct_df["category"] = "Indian Food"

    ifct_df = ifct_df.head(max_foods)
    print(f"  Loaded {len(ifct_df)} IFCT foods")
    return ifct_df


def assign_diet_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Heuristic diet tag assignment based on nutrition values."""
    # low_gi: low sugar AND high fiber relative to carbs
    df["low_gi"] = ((df["sugar_g"] < 5) & (df["fiber_g"] > 3)).astype(int)

    # low_sodium
    df["low_sodium"] = (df["sodium_mg"] < 140).astype(int)  # per serving

    # diabetic_friendly: low GI + moderate carbs
    df["diabetic_friendly"] = ((df["low_gi"] == 1) & (df["carbs_g"] < 30)).astype(int)

    # heart_healthy: low sat fat, low sodium, has fiber
    df["heart_healthy"] = (
        (df["sat_fat_g"] < 2) & (df["sodium_mg"] < 300) & (df["fiber_g"] > 2)
    ).astype(int)

    # vegetarian (heuristic from category keywords)
    meat_keywords = ["beef", "pork", "chicken", "turkey", "fish", "seafood", "meat",
                     "lamb", "bacon", "sausage", "poultry"]
    df["vegetarian"] = (~df["name"].str.lower().str.contains(
        "|".join(meat_keywords), na=False
    )).astype(int)

    # vegan
    animal_keywords = meat_keywords + ["milk", "cheese", "egg", "butter", "cream",
                                        "yogurt", "whey", "casein", "honey"]
    df["vegan"] = (~df["name"].str.lower().str.contains(
        "|".join(animal_keywords), na=False
    )).astype(int)

    return df


def assign_meal_types(df: pd.DataFrame) -> pd.DataFrame:
    """Heuristic meal type assignment."""
    df["meal_type"] = "lunch"  # default

    breakfast_kw = ["cereal", "oat", "pancake", "waffle", "toast", "egg", "breakfast",
                    "muesli", "granola", "smoothie", "juice", "milk"]
    snack_kw = ["bar", "chip", "cookie", "fruit", "nut", "yogurt", "cracker", "snack"]
    dinner_kw = ["curry", "stew", "roast", "grilled", "baked", "pasta", "rice", "noodle"]

    name_lower = df["name"].str.lower()
    df.loc[name_lower.str.contains("|".join(breakfast_kw), na=False), "meal_type"] = "breakfast"
    df.loc[name_lower.str.contains("|".join(snack_kw), na=False), "meal_type"] = "snack"
    df.loc[name_lower.str.contains("|".join(dinner_kw), na=False), "meal_type"] = "dinner"

    return df


def build_food_embeddings(df: pd.DataFrame, n_components: int = 8) -> np.ndarray:
    """PCA on nutrition features → food embeddings."""
    X = df[FOOD_NUTRITION_COLS].values.astype(np.float32)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=n_components, random_state=42)
    embeddings = pca.fit_transform(X_scaled)

    joblib.dump(scaler, PROCESSED_DIR / "food_nutrition_scaler.joblib")
    joblib.dump(pca, PROCESSED_DIR / "food_pca.joblib")

    explained = pca.explained_variance_ratio_.sum()
    print(f"  Food PCA: {n_components} components, {explained:.1%} variance explained")

    return embeddings.astype(np.float32)


def load_and_preprocess_food() -> pd.DataFrame:
    """Full food preprocessing pipeline."""
    print("[Food Preprocess] Loading datasets...")

    # Load from both sources
    usda_df = load_usda_foods(max_foods=2000)
    ifct_df = load_ifct_foods(max_foods=500)

    # Combine
    common_cols = list(set(usda_df.columns) & set(ifct_df.columns))
    combined = pd.concat([usda_df[common_cols], ifct_df[common_cols]], ignore_index=True)

    # Drop rows with zero calories (invalid)
    combined = combined[combined["calories"] > 0].reset_index(drop=True)
    combined["food_id"] = range(len(combined))

    # Assign tags and meal types
    combined = assign_diet_tags(combined)
    combined = assign_meal_types(combined)

    # Build embeddings
    food_embeddings = build_food_embeddings(combined)
    np.save(PROCESSED_DIR / "food_embeddings.npy", food_embeddings)

    # Save clean table
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(PROCESSED_DIR / "foods_clean.csv", index=False)

    print(f"[Food Preprocess] Total: {len(combined)} foods")
    print(f"  Cuisines: {combined['cuisine'].value_counts().to_dict()}")
    print(f"  Meal types: {combined['meal_type'].value_counts().to_dict()}")

    return combined


if __name__ == "__main__":
    load_and_preprocess_food()
