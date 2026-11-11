import pandas as pd
import os

from config import build_schedule


def generate_exam_schedule():

    schedule = build_schedule()

    df = pd.DataFrame(schedule)

    return df


if __name__ == "__main__":

    df = generate_exam_schedule()

    os.makedirs("data/raw", exist_ok=True)

    df.to_csv("data/raw/exam_schedule.csv", index=False)

    print("Exam schedule generated successfully!")
    print("Total exams:", len(df))
    print(df.head())