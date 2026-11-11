
import pandas as pd
import os

from config import BRANCHES, YEARS


# --------------------------------
# 1. CLEAN STUDENT DATA
# --------------------------------

def clean_students(df):

    df = df.copy()

    # Remove extra spaces
    df["name"] = df["name"].str.strip()
    df["email"] = df["email"].str.strip().str.lower()
    df["branch"] = df["branch"].str.strip().str.upper()

    # Standardize exam slots
    df["exam_slot"] = df["exam_slot"].str.strip().str.title()

    # Remove duplicate exam records
    df = df.drop_duplicates(
        subset=["roll_no", "subject_code", "exam_date", "exam_slot"]
    )

    # Convert numeric columns
    df["attendance_pct"] = pd.to_numeric(
        df["attendance_pct"], errors="coerce"
    )

    df["prev_absent_count"] = pd.to_numeric(
        df["prev_absent_count"], errors="coerce"
    )

    return df


# --------------------------------
# 2. VALIDATE STUDENT DATA
# --------------------------------

def validate_students(df):

    required_columns = [
        "roll_no", "name", "email", "branch", "year",
        "semester", "subject_code", "exam_date",
        "exam_slot", "attendance_pct", "prev_absent_count"
    ]

    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Check missing values
    if df[required_columns].isnull().any().any():
        raise ValueError("Student data contains missing values")

    # Check valid branches
    if not df["branch"].isin(BRANCHES).all():
        raise ValueError("Invalid branch found")

    # Check valid years
    if not df["year"].isin(YEARS).all():
        raise ValueError("Invalid year found")

    # Check attendance range
    if not df["attendance_pct"].between(0, 100).all():
        raise ValueError("Invalid attendance percentage")

    return True


# --------------------------------
# 3. VALIDATE ROOM DATA
# --------------------------------

def validate_rooms(df):

    required_columns = [
        "room_id", "building", "floor", "rows",
        "benches_per_row", "seats_per_bench",
        "capacity", "available"
    ]

    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Check missing values
    if df[required_columns].isnull().any().any():
        raise ValueError("Room data contains missing values")

    # Check unique room IDs
    if df["room_id"].duplicated().any():
        raise ValueError("Duplicate room IDs found")

    # Check positive dimensions
    dimensions = ["rows", "benches_per_row", "seats_per_bench"]

    if (df[dimensions] <= 0).any().any():
        raise ValueError("Room dimensions must be positive")

    # Check capacity
    expected_capacity = (
        df["rows"] *
        df["benches_per_row"] *
        df["seats_per_bench"]
    )

    if not (df["capacity"] == expected_capacity).all():
        raise ValueError("Incorrect room capacity")

    # Check availability
    if not df["available"].isin([True, False]).all():
        raise ValueError("Invalid availability value")

    return True

def validate_schedule(df):

    required_columns = [
        "exam_date",
        "exam_slot",
        "subject_code",
        "branch",
        "year",
        "reporting_time"
    ]

    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Check missing values
    if df[required_columns].isnull().any().any():
        raise ValueError("Schedule contains missing values")

    # Check duplicate subject codes
    if df["subject_code"].duplicated().any():
        raise ValueError("Duplicate subject codes found")

    # Check valid branches and years
    if not df["branch"].isin(BRANCHES).all():
        raise ValueError("Invalid branch found")

    if not df["year"].isin(YEARS).all():
        raise ValueError("Invalid year found")

    return True

def validate_student_schedule(students_df, schedule_df):

    merged = students_df.merge(
        schedule_df,
        on=[
            "subject_code",
            "exam_date",
            "exam_slot",
            "branch",
            "year"
        ],
        how="left",
        indicator=True
    )

    unmatched = merged[merged["_merge"] == "left_only"]

    if not unmatched.empty:
        raise ValueError(
            f"{len(unmatched)} student exam records "
            "do not match the schedule"
        )

    return True


# --------------------------------
# 4. MAIN PROGRAM
# --------------------------------

if __name__ == "__main__":

    # Load student data
    df = pd.read_csv("data/raw/students.csv")

    print("Original records:", len(df))

    # Clean student data
    cleaned_df = clean_students(df)

    print("After cleaning:", len(cleaned_df))

    # Validate student data
    if validate_students(cleaned_df):
        print("Student validation successful!")

    # Save cleaned data
    os.makedirs("data/processed", exist_ok=True)

    cleaned_df.to_csv(
        "data/processed/cleaned_students.csv",
        index=False
    )

    print("Cleaned dataset saved!")

    # Load room data
    rooms_df = pd.read_csv("data/raw/rooms.csv")

    # Validate room data
    if validate_rooms(rooms_df):
        print("Room validation successful!")

    # Load exam schedule
    schedule_df = pd.read_csv("data/raw/exam_schedule.csv")

    # Validate exam schedule
    if validate_schedule(schedule_df):
        print("Schedule validation successful!")

    if validate_student_schedule(cleaned_df, schedule_df):
        print("Student-schedule consistency successful!")
