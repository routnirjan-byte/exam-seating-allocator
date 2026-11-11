import pandas as pd
import random
import os


import pandas as pd
import random
import os


def generate_dirty_data(input_file, output_file, seed=42):

    # Read the original clean dataset
    df = pd.read_csv(input_file)

    # Create a random generator
    rng = random.Random(seed)

    # 1. Add extra spaces to some student names
    name_indices = rng.sample(list(df.index), 20)

    for index in name_indices:
        df.loc[index, "name"] = "  " + str(df.loc[index, "name"]) + "  "

    # 2. Make some emails invalid
    email_indices = rng.sample(list(df.index), 10)

    for index in email_indices:
        df.loc[index, "email"] = "invalid-email"

    # 3. Add missing values to some attendance records
    missing_indices = rng.sample(list(df.index), 10)

    for index in missing_indices:
        df.loc[index, "attendance_pct"] = None

    # 4. Add invalid attendance percentages
    invalid_indices = rng.sample(list(df.index), 10)

    for index in invalid_indices:
        df.loc[index, "attendance_pct"] = 120

    # Create output folder
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save dirty dataset separately
    df.to_csv(output_file, index=False)

    print("Dirty dataset generated successfully!")
    print("Original records:", len(pd.read_csv(input_file)))
    print("Dirty records:", len(df))
    print("Dirty dataset saved to:", output_file)


if __name__ == "__main__":

    generate_dirty_data(
        input_file="data/processed/cleaned_students.csv",
        output_file="data/raw/dirty_students.csv"
    )
