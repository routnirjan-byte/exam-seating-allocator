from pathlib import Path

import numpy as np
import pandas as pd

from src.rooms import find_violations, neighbors, normalize_rooms, seat_positions

OUT_COLS = ["roll_no", "name", "email", "subject_code", "exam_date", "exam_slot",
            "room_id", "building", "floor", "row", "bench", "seat"]


def load_students():
    cleaned = Path("data/processed/cleaned_students.csv")
    return pd.read_csv(cleaned if cleaned.exists() else "data/raw/students.csv")


def room_quotas(n_students, capacities):
    """Split students over rooms in proportion to capacity."""
    caps = np.array(capacities)
    raw = n_students * caps / caps.sum()
    quotas = np.floor(raw).astype(int)
    leftover = n_students - quotas.sum()
    for i in np.argsort(-(raw - quotas))[:leftover]:      # biggest fractions get the extras
        quotas[i] += 1
    return quotas


def allocate_slot(slot_df, rooms, rng):
    pools = {}                                            # subject -> student indexes
    for subject, g in slot_df.groupby("subject_code"):
        idx = list(g.index)
        rng.shuffle(idx)
        pools[subject] = idx

    caps = rooms["capacity"].tolist()
    quotas = room_quotas(min(len(slot_df), sum(caps)), caps)

    placed = []
    for (_, room), quota in zip(rooms.iterrows(), quotas):
        R, B, S = int(room["rows"]), int(room["benches_per_row"]), int(room["seats_per_bench"])
        seats = seat_positions(room)
        if quota < len(seats):                            # spread empty seats evenly
            keep = np.floor(np.linspace(0, len(seats), quota, endpoint=False)).astype(int)
            seats = [seats[i] for i in keep]

        grid = {}                                         # seat -> subject seated there
        for pos in seats:
            blocked = {grid[nb] for nb in neighbors(*pos, R, B, S) if nb in grid}
            options = [s for s, lst in pools.items() if lst and s not in blocked]
            if not options:                               # every subject clashes
                options = [s for s, lst in pools.items() if lst]
            if not options:
                break
            subject = max(options, key=lambda s: (len(pools[s]), s))
            student = pools[subject].pop()
            grid[pos] = subject
            placed.append((student, room["room_id"], *pos))
    return placed


def allocate(students_df, rooms_df, seed=42):
    rng = np.random.default_rng(seed)
    rooms = normalize_rooms(rooms_df)
    rooms = (rooms[rooms["available"]]
             .sort_values("capacity", ascending=False).reset_index(drop=True))
    if rooms.empty:
        raise ValueError("No available rooms")
    students = students_df.reset_index(drop=True)

    parts = []
    for (date, slot), slot_df in students.groupby(["exam_date", "exam_slot"]):
        placed = pd.DataFrame(allocate_slot(slot_df, rooms, rng),
                              columns=["idx", "room_id", "row", "bench", "seat"])
        if len(placed) < len(slot_df):
            print(f"WARNING {date} {slot}: only {len(placed)} of {len(slot_df)} students seated")
        info = students.loc[placed["idx"], ["roll_no", "name", "email", "subject_code",
                                            "exam_date", "exam_slot"]].reset_index(drop=True)
        parts.append(pd.concat([info, placed.drop(columns="idx")], axis=1))

    result = pd.concat(parts, ignore_index=True)
    result = result.merge(rooms[["room_id", "building", "floor"]], on="room_id", how="left")
    return result[OUT_COLS]


if __name__ == "__main__":
    students = load_students()
    rooms = pd.read_csv("data/raw/rooms.csv")
    alloc = allocate(students, rooms)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    alloc.to_csv("data/processed/allocation.csv", index=False)
    print(f"seated {len(alloc)} of {len(students)} | adjacent violations: {len(find_violations(alloc, rooms))}")