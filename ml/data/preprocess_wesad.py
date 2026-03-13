"""
FitGenix ML — WESAD Dataset Preprocessing
Extract HR-based features from WESAD for stress detection.
"""
import pandas as pd
import numpy as np
import os, sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import WESAD_DIR, PROCESSED_DIR


def parse_respiban_header(filepath: Path) -> dict:
    """Parse RespiBAN header to get sampling rate and sensor info."""
    info = {"sample_rate": 700, "sensors": []}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# sample rate:"):
                    info["sample_rate"] = int(line.split(":")[-1].strip().replace("Hz", ""))
                elif line.startswith("# column"):
                    info["sensors"].append(line)
                elif not line.startswith("#") and line:
                    break  # data starts
    except Exception:
        pass
    return info


def extract_hr_features_from_subject(subject_dir: Path) -> dict | None:
    """
    Extract HR-based features from a single WESAD subject.
    RespiBAN sensor columns (typical):
    col 0: ECG, col 1: EDA, col 2: EMG, col 3: Temp, col 4: XYZ Accel (3), col 7: Respiration

    We focus on ECG to derive HR features.
    """
    subject_id = subject_dir.name
    respiban_file = subject_dir / f"{subject_id}_respiban.txt"
    quest_file = subject_dir / f"{subject_id}_quest.csv"

    if not respiban_file.exists():
        return None

    # Parse quest file for timing info
    quest_data = {}
    try:
        with open(quest_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("# ORDER"):
                    quest_data["order"] = [x.strip() for x in line.split(";")[1:] if x.strip()]
                elif line.startswith("# START"):
                    quest_data["start"] = [float(x) for x in line.split(";")[1:] if x.strip()]
                elif line.startswith("# END"):
                    quest_data["end"] = [float(x) for x in line.split(";")[1:] if x.strip()]
    except Exception as e:
        print(f"  Warning parsing quest for {subject_id}: {e}")
        return None

    # Load RespiBAN data (skip header lines starting with #)
    try:
        data_lines = []
        with open(respiban_file, "r") as f:
            for line in f:
                if not line.startswith("#") and line.strip():
                    vals = line.strip().split("\t")
                    if len(vals) >= 2:
                        try:
                            data_lines.append([float(v) for v in vals])
                        except ValueError:
                            continue
                if len(data_lines) > 5_000_000:
                    break  # Cap for memory

        if not data_lines:
            return None

        data = np.array(data_lines, dtype=np.float32)
    except Exception as e:
        print(f"  Warning loading respiban for {subject_id}: {e}")
        return None

    sample_rate = 700  # Default RespiBAN rate
    ecg = data[:, 0] if data.shape[1] > 0 else None

    if ecg is None or len(ecg) < sample_rate * 60:
        return None

    # Simple R-peak detection (threshold-based for feature extraction)
    # This is a simplified approach — in production, use Pan-Tompkins or similar
    features_list = []
    labels = []

    # Extract features per 60-second window
    window_size = sample_rate * 60  # 60 seconds
    step_size = sample_rate * 30   # 30-second overlap

    for start in range(0, len(ecg) - window_size, step_size):
        window = ecg[start:start + window_size]
        time_sec = start / sample_rate

        # Determine label from quest timing
        label = determine_label(time_sec, quest_data)
        if label is None:
            continue

        # HR-derived features from ECG window
        feats = compute_hr_features(window, sample_rate)
        if feats is not None:
            features_list.append(feats)
            labels.append(label)

    if not features_list:
        return None

    return {
        "subject_id": subject_id,
        "features": np.array(features_list, dtype=np.float32),
        "labels": np.array(labels, dtype=np.int32),
    }


def determine_label(time_sec: float, quest_data: dict) -> int | None:
    """
    Map timepoint to stress label.
    TSST (Trier Social Stress Test) = 1 (stress)
    Baseline, Meditation, Amusement = 0 (non-stress)
    """
    order = quest_data.get("order", [])
    starts = quest_data.get("start", [])
    ends = quest_data.get("end", [])

    time_min = time_sec / 60.0

    stress_conditions = {"TSST"}
    non_stress_conditions = {"Base", "Medi 1", "Medi 2", "Fun"}

    for i, condition in enumerate(order):
        if i >= len(starts) or i >= len(ends):
            continue
        try:
            s, e = float(starts[i]), float(ends[i])
        except (ValueError, TypeError):
            continue
        if s <= time_min <= e:
            clean = condition.strip()
            if clean in stress_conditions:
                return 1
            elif clean in non_stress_conditions:
                return 0
            return None

    return None


def compute_hr_features(ecg_window: np.ndarray, sample_rate: int) -> np.ndarray | None:
    """
    Compute HR-based features from ECG window.
    Returns: [hr_mean, hr_std, hr_max, hr_range, rmssd_proxy,
              signal_energy, zcr, peak_count]
    """
    # Normalize ECG
    ecg = (ecg_window - ecg_window.mean()) / (ecg_window.std() + 1e-8)

    # Simple peak detection (threshold-based)
    threshold = 0.6 * ecg.max()
    min_distance = int(sample_rate * 0.4)  # min 0.4s between peaks (max 150 bpm)

    peaks = []
    i = 0
    while i < len(ecg):
        if ecg[i] > threshold:
            # Find local max
            start = i
            while i < len(ecg) and ecg[i] > threshold:
                i += 1
            peak = start + np.argmax(ecg[start:i])
            if not peaks or (peak - peaks[-1]) >= min_distance:
                peaks.append(peak)
        else:
            i += 1

    if len(peaks) < 3:
        return None

    # RR intervals in ms
    rr_intervals = np.diff(peaks) / sample_rate * 1000

    # HR from RR
    hr_values = 60000 / rr_intervals  # bpm
    hr_values = hr_values[(hr_values > 40) & (hr_values < 200)]  # physiological range

    if len(hr_values) < 2:
        return None

    hr_mean = hr_values.mean()
    hr_std = hr_values.std()
    hr_max = hr_values.max()
    hr_range = hr_values.max() - hr_values.min()

    # RMSSD (root mean square of successive differences)
    rr_diffs = np.diff(rr_intervals)
    rmssd = np.sqrt(np.mean(rr_diffs ** 2)) if len(rr_diffs) > 0 else 0

    # Signal energy
    signal_energy = np.sum(ecg ** 2) / len(ecg)

    # Zero crossing rate
    zcr = np.sum(np.abs(np.diff(np.sign(ecg)))) / (2 * len(ecg))

    # Peak count (normalized by window duration)
    peak_rate = len(peaks) / (len(ecg) / sample_rate)

    return np.array([hr_mean, hr_std, hr_max, hr_range, rmssd,
                     signal_energy, zcr, peak_rate], dtype=np.float32)


def preprocess_wesad() -> dict:
    """Process all WESAD subjects and build train dataset."""
    print("[WESAD Preprocess] Processing subjects...")

    all_features = []
    all_labels = []
    subject_ids = []

    subject_dirs = sorted(WESAD_DIR.iterdir())
    for sdir in tqdm(subject_dirs, desc="WESAD subjects", unit="subject"):
        if not sdir.is_dir() or not sdir.name.startswith("S"):
            continue

        print(f"  Processing {sdir.name}...", end=" ")
        result = extract_hr_features_from_subject(sdir)

        if result is not None:
            all_features.append(result["features"])
            all_labels.append(result["labels"])
            subject_ids.extend([result["subject_id"]] * len(result["labels"]))
            print(f"{len(result['labels'])} windows "
                  f"(stress: {(result['labels']==1).sum()}, "
                  f"non-stress: {(result['labels']==0).sum()})")
        else:
            print("skipped (no valid data)")

    if not all_features:
        print("  WARNING: No valid WESAD data extracted. Using synthetic stress data instead.")
        return generate_synthetic_stress_data()

    X = np.vstack(all_features)
    y = np.concatenate(all_labels)
    subjects = np.array(subject_ids)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(
        PROCESSED_DIR / "wesad_processed.npz",
        X=X, y=y, subjects=subjects,
    )

    print(f"[WESAD Preprocess] Total: {len(y)} windows")
    print(f"  Stress: {(y==1).sum()}, Non-stress: {(y==0).sum()}")
    print(f"  Features per window: {X.shape[1]}")
    print(f"  Subjects: {len(set(subjects))}")

    return {"X": X, "y": y, "subjects": subjects}


def generate_synthetic_stress_data(n_samples: int = 2000) -> dict:
    """Fallback: generate synthetic stress detection data if WESAD fails."""
    np.random.seed(42)

    n_stress = n_samples // 3
    n_calm = n_samples - n_stress

    # Non-stress: lower HR, higher HRV
    calm_features = np.column_stack([
        np.random.normal(72, 8, n_calm),     # hr_mean
        np.random.normal(4, 1.5, n_calm),    # hr_std
        np.random.normal(85, 10, n_calm),    # hr_max
        np.random.normal(15, 5, n_calm),     # hr_range
        np.random.normal(45, 15, n_calm),    # rmssd (higher = calmer)
        np.random.normal(0.5, 0.15, n_calm), # signal_energy
        np.random.normal(0.3, 0.05, n_calm), # zcr
        np.random.normal(1.2, 0.15, n_calm), # peak_rate
    ])

    # Stress: higher HR, lower HRV
    stress_features = np.column_stack([
        np.random.normal(92, 12, n_stress),    # hr_mean (higher)
        np.random.normal(8, 3, n_stress),      # hr_std (higher)
        np.random.normal(115, 15, n_stress),   # hr_max (higher)
        np.random.normal(30, 10, n_stress),    # hr_range (wider)
        np.random.normal(25, 10, n_stress),    # rmssd (lower = stressed)
        np.random.normal(0.7, 0.2, n_stress),  # signal_energy
        np.random.normal(0.35, 0.06, n_stress),# zcr
        np.random.normal(1.5, 0.2, n_stress),  # peak_rate
    ])

    X = np.vstack([calm_features, stress_features]).astype(np.float32)
    y = np.array([0] * n_calm + [1] * n_stress, dtype=np.int32)

    # Shuffle
    perm = np.random.permutation(len(y))
    X, y = X[perm], y[perm]

    subjects = np.array([f"synth_{i % 15}" for i in range(len(y))])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(PROCESSED_DIR / "wesad_processed.npz", X=X, y=y, subjects=subjects)

    print(f"[Synthetic Stress] Generated {len(y)} samples (stress: {(y==1).sum()})")
    return {"X": X, "y": y, "subjects": subjects}


STRESS_FEATURE_NAMES = [
    "hr_mean", "hr_std", "hr_max", "hr_range", "rmssd",
    "signal_energy", "zcr", "peak_rate",
]


if __name__ == "__main__":
    preprocess_wesad()
