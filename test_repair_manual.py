import pandas as pd

from src.repair import repair_allocation
from src.rooms import find_violations, neighbors, normalize_rooms

allocation = pd.read_csv("data/processed/allocation.csv")
rooms_df = pd.read_csv("data/raw/rooms.csv")

test_data = allocation.copy()
rooms = normalize_rooms(rooms_df).set_index("room_id")

conflict_created = False

# Find two neighbouring students in the same room and exam session.
for (date, slot, room_id), group in test_data.groupby(
    ["exam_date", "exam_slot", "room_id"]
):
    room = rooms.loc[room_id]

    positions = {
        (int(r.row), int(r.bench), int(r.seat)): idx
        for idx, r in group.iterrows()
    }

    for pos, idx in positions.items():

        adjacent_seats = neighbors(
            *pos,
            int(room["rows"]),
            int(room["benches_per_row"]),
            int(room["seats_per_bench"])
        )

        for adjacent in adjacent_seats:

            if adjacent in positions and adjacent > pos:

                other_idx = positions[adjacent]

                # Artificially create a same-subject conflict.
                test_data.loc[other_idx, "subject_code"] = (
                    test_data.loc[idx, "subject_code"]
                )

                conflict_created = True
                break

        if conflict_created:
            break

    if conflict_created:
        break

if not conflict_created:
    raise RuntimeError("Could not find neighbouring seats for the test.")

before = len(find_violations(test_data, rooms_df))

repaired = repair_allocation(test_data, rooms_df)

after = len(find_violations(repaired, rooms_df))

print("Artificial conflict created!")
print("Violations before repair:", before)
print("Violations after repair:", after)
print("Students retained:", len(repaired))

if after < before:
    print("SUCCESS: Repair reduced the violations!")
else:
    print("Repair did not reduce the violations. Further investigation needed.")