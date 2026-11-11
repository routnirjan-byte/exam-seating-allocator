import datetime as dt
from itertools import product

#branch weightages
BRANCH_WEIGHTS = {"ADS": 0.30, "IT": 0.20, "ECE": 0.18,
                  "MECH": 0.12, "CIVIL": 0.10, "EE": 0.10}
BRANCHES = list(BRANCH_WEIGHTS)
YEARS = [1, 2, 3, 4]

#exam dates for sem
EXAM_DATES = [dt.date(2026, 11, d) for d in (14, 16, 20, 22, 30)]

# yrs 1 and 2 morning, yrs3 and 4 afternoon
SLOT_BY_YEAR = {1: "Morning", 2: "Morning", 3: "Afternoon", 4: "Afternoon"}
REPORTING_TIME = {"Morning": "10:30", "Afternoon": "14:00"}


def subject_code(branch, year, n):
    """Subject n (1 to 5) of a branch and year, e.g. ADS301 = ADS, year 3, subject 1."""
    return f"{branch}{year}{n:02d}"


def build_schedule():
    """One row per paper: 6 branches x 4 years x 5 subjects = 120 papers."""
    rows = []
    for branch, year in product(BRANCHES, YEARS):
        for n, exam_date in enumerate(EXAM_DATES, start=1):
            slot = SLOT_BY_YEAR[year]
            rows.append({
                "exam_date": exam_date,
                "exam_slot": slot,
                "subject_code": subject_code(branch, year, n),
                "branch": branch,
                "year": year,
                "reporting_time": REPORTING_TIME[slot],
            })
    return rows