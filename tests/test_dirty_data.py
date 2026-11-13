
import pandas as pd

from data_validation import clean_students, validate_students


# Read the dirty dataset
df = pd.read_csv("data/raw/dirty_students.csv")

# Test duplicate removal
duplicate_test_df = pd.concat(
    [df, df.iloc[[0]]],
    ignore_index=True
)

print("Records before duplicate removal:", len(duplicate_test_df))

duplicate_cleaned_df = clean_students(duplicate_test_df)

print("Records after duplicate removal:", len(duplicate_cleaned_df))

print("Dirty records:", len(df))

# Try cleaning the data
cleaned_df = clean_students(df)

print("Attendance values above 100:", (cleaned_df["attendance_pct"] > 100).sum())

# Create a test copy with valid emails
attendance_test_df = cleaned_df.copy()
attendance_test_df["email"] = "student@example.com"

# Test attendance validation
try:
    validate_students(attendance_test_df)

except ValueError as error:
    print("Attendance test caught an error!")
    print("Reason:", error)

print("Missing values before:", df["attendance_pct"].isnull().sum())

print("Missing values after:", cleaned_df["attendance_pct"].isnull().sum())

print("\nBefore cleaning:")
print(df["attendance_pct"].head(15).to_list())

print("\nAfter cleaning:")
print(cleaned_df["attendance_pct"].head(15).to_list())

print("Cleaning completed!")

# Try validating the data
try:
    validate_students(cleaned_df)
    print("All student records are valid!")

except ValueError as error:
    print("Validation caught an error!")
    print("Reason:", error)


# Test invalid branch
branch_test_df = cleaned_df.copy()

# Make all emails valid for this test
branch_test_df["email"] = "student@example.com"

# Introduce an invalid branch
branch_test_df.loc[branch_test_df.index[0], "branch"] = "XYZ"

try:
    validate_students(branch_test_df)

except ValueError as error:
    print("Branch test caught an error!")
    print("Reason:", error)
