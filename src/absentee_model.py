import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.allocator import load_students

NUMERIC = ["attendance_pct", "prev_absent_count", "year", "paper_no"]
CATEGORICAL = ["exam_slot", "branch"]
FEATURES = NUMERIC + CATEGORICAL
MODEL_PATH = Path("models/absentee_model.joblib")

CANDIDATES = {
    "logistic_regression": LogisticRegression(max_iter=1000),
    "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=20, random_state=0),
}


def add_features(df):
    """paper_no is the last two digits of the subject code: ADS301 -> 1."""
    out = df.copy()
    out["paper_no"] = out["subject_code"].astype(str).str[-2:].astype(int)
    return out


def simulate_absence(df, seed=7):
    """SIMULATED label (the data has no real absences). Lower attendance, more
    past absences and later papers raise the chance of being absent."""
    rng = np.random.default_rng(seed)
    d = add_features(df)
    logit = (-4.2 + 0.06 * (100 - d["attendance_pct"])
             + 0.22 * d["prev_absent_count"] + 0.12 * (d["paper_no"] - 1))
    p = 1 / (1 + np.exp(-logit))
    return pd.Series((rng.random(len(d)) < p).astype(int), index=df.index, name="absent")


def make_pipeline(estimator):
    prep = ColumnTransformer([("num", StandardScaler(), NUMERIC),
                              ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    return Pipeline([("prep", prep), ("model", estimator)])


def train_and_evaluate(students_df, threshold=0.2):
    """Split BY STUDENT, train every candidate, score on unseen students."""
    data = add_features(students_df).reset_index(drop=True)
    data["absent"] = simulate_absence(data)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(data, groups=data["roll_no"]))
    train, test = data.iloc[train_idx], data.iloc[test_idx]

    rows, fitted = [], {}
    for name, estimator in CANDIDATES.items():
        pipe = make_pipeline(clone(estimator)).fit(train[FEATURES], train["absent"])
        proba = pipe.predict_proba(test[FEATURES])[:, 1]
        flagged = (proba >= threshold).astype(int)
        rows.append({"model": name,
                     "roc_auc": roc_auc_score(test["absent"], proba),
                     "pr_auc": average_precision_score(test["absent"], proba),
                     "precision": precision_score(test["absent"], flagged, zero_division=0),
                     "recall": recall_score(test["absent"], flagged, zero_division=0),
                     "actual_absent_rate": test["absent"].mean(),
                     "mean_predicted": proba.mean()})
        fitted[name] = pipe
    scores = pd.DataFrame(rows).set_index("model")
    best = scores["roc_auc"].idxmax()
    return fitted[best], best, scores, train, test


def predict_absence(model, students_df):
    """Return a copy of students_df with a p_absent column (0 to 1)."""
    out = students_df.copy()
    out["p_absent"] = model.predict_proba(add_features(students_df)[FEATURES])[:, 1]
    return out


def slot_plan(scored):
    """Expected absentees per exam slot, with a rough 95% upper bound."""
    keys = ["exam_date", "exam_slot"]
    g = scored.groupby(keys)["p_absent"]
    plan = pd.DataFrame({"students": g.size(), "expected_absent": g.sum()})
    variance = (scored["p_absent"] * (1 - scored["p_absent"])).groupby(
        [scored[k] for k in keys]).sum()
    plan["likely_max_absent"] = plan["expected_absent"] + 1.645 * np.sqrt(variance)
    return plan.round(1)


if __name__ == "__main__":
    students = pd.read_csv(sys.argv[1]) if len(sys.argv) > 1 else load_students()
    model, best, scores, train, test = train_and_evaluate(students)

    print(scores.round(3).to_string())
    print("best model:", best)
    held_out = predict_absence(model, test)
    print(f"test students: expected absentees {held_out['p_absent'].sum():.1f} "
          f"| actual {int(test['absent'].sum())}")

    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    scored = predict_absence(model, students)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    scored.to_csv("data/processed/absentee_predictions.csv", index=False)
    print(slot_plan(scored).to_string())