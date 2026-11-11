
import random
import pandas as pd
from faker import Faker
import os

from config import (
    BRANCHES,
    BRANCH_WEIGHTS,
    YEARS,
    SEMESTER_BY_YEAR,
    build_schedule
)


def generate_students(students_per_year=100, seed=42):


     # Initialize Faker and random generator
    fake = Faker("en_IN")
    fake.seed_instance(seed)

    rng = random.Random(seed)

    # Local random generator for reproducibility
    rng = random.Random(seed)

    

    # Generate examination schedule
    schedule_df = pd.DataFrame(build_schedule())

    students = []
    roll_number = 1

    # Generate students for each academic year
    for year in YEARS:

        # Select branches according to configured weights
        selected_branches = rng.choices(
            BRANCHES,
            weights=[BRANCH_WEIGHTS[b] for b in BRANCHES],
            k=students_per_year
        )

        for branch in selected_branches:

            name = fake.name()

            email = f"student{roll_number:04d}@example.com"

            attendance = round(rng.uniform(55, 100), 2)
            absent_count = rng.randint(0, 4)

            semester = SEMESTER_BY_YEAR[year]

            # Find all exams for this branch and year
            exams = schedule_df[
                (schedule_df["branch"] == branch) &
                (schedule_df["year"] == year)
            ]

            # One record per student per examination
            for _, exam in exams.iterrows():

                students.append({
                    "roll_no": roll_number,
                    "name": name,
                    "email": email,
                    "branch": branch,
                    "year": year,
                    "semester": semester,
                    "subject_code": exam["subject_code"],
                    "exam_date": exam["exam_date"],
                    "exam_slot": exam["exam_slot"],
                    "attendance_pct": attendance,
                    "prev_absent_count": absent_count
                })

            roll_number += 1

    return pd.DataFrame(students)


if __name__ == "__main__":

    df = generate_students(
        students_per_year=100,
        seed=42
    )

    os.makedirs("data/raw", exist_ok=True)

    df.to_csv("data/raw/students.csv", index=False)

    print("Student data generated successfully!")
    print("Total exam records:", len(df))
    print(df.head())
