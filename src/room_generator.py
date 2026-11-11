import random
import pandas as pd
import os

def generate_rooms(seed=42):

    rng = random.Random(seed)

    rooms = []

    buildings = ["A", "B", "C"]

    for i in range(1, 11):

        building = rng.choice(buildings)

        floor = rng.randint(0, 3)

        rows = rng.randint(4, 6)

        benches_per_row = rng.randint(3, 5)

        seats_per_bench = 2

        capacity = rows * benches_per_row * seats_per_bench

        available = True

        rooms.append({
            "room_id": f"R{i:03d}",
            "building": building,
            "floor": floor,
            "rows": rows,
            "benches_per_row": benches_per_row,
            "seats_per_bench": seats_per_bench,
            "capacity": capacity,
            "available": available
        })

    return pd.DataFrame(rooms)

if __name__ == "__main__":

    df = generate_rooms(seed=42)

    os.makedirs("data/raw", exist_ok=True)

    df.to_csv("data/raw/rooms.csv", index=False)

    print("Room data generated successfully!")
    print(df)