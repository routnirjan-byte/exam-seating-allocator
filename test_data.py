import pandas as pd

# Read the CSV file
df = pd.read_csv("data/raw/fake_exam_seating.csv")

# Display first 5 records
print(df.head())

# Display dataset dimensions
print("Shape:", df.shape)

# Display information about columns
print(df.info())

print("Total seats:", len(df))

print("Seats in R101:",
      len(df[df["room_id"] == "R101"]))

print("Students in R102:",
      len(df[(df["room_id"] == "R102") &
             (df["seat_status"] == "ASSIGNED")]))

print("Vacant seats:",
      len(df[df["seat_status"] == "VACANT"]))