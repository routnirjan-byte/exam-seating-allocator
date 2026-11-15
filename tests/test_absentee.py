import pandas as pd

from src.absentee_model import (add_features, predict_absence, simulate_absence,
                                slot_plan, train_and_evaluate)
from src.allocator import load_students

students = load_students()
model, best, scores, train, test = train_and_evaluate(students)


def test_paper_number_comes_from_subject_code():
    assert add_features(pd.DataFrame({"subject_code": ["ADS301", "EE405"]}))["paper_no"].tolist() == [1, 5]


def test_simulated_absence_rate_is_reasonable():
    assert 0.02 < simulate_absence(students).mean() < 0.20


def test_low_attendance_means_more_absence():
    absent = simulate_absence(students)
    low = absent[students["attendance_pct"] < 65].mean()
    high = absent[students["attendance_pct"] > 90].mean()
    assert low > high


def test_no_student_is_in_both_train_and_test():
    assert not set(train["roll_no"]) & set(test["roll_no"])


def test_model_beats_guessing():
    assert scores["roc_auc"].max() > 0.60


def test_predictions_are_probabilities():
    scored = predict_absence(model, students)
    assert len(scored) == len(students)
    assert scored["p_absent"].between(0, 1).all()


def test_slot_plan_adds_up():
    scored = predict_absence(model, students)
    plan = slot_plan(scored)
    assert abs(plan["expected_absent"].sum() - scored["p_absent"].sum()) < 1
    assert (plan["likely_max_absent"] >= plan["expected_absent"]).all()