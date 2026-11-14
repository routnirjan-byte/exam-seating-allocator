
import pandas as pd

from src.rooms import (
    find_violations,
    neighbors,
    normalize_rooms,
    seat_positions
)


def make_grid(group):
    """Create a mapping of seat positions to subject codes."""
    return {
        (int(r.row), int(r.bench), int(r.seat)): r.subject_code
        for r in group.itertuples()
    }


def count_group_violations(group, room, strict=False):
    """Count adjacent students with the same subject in one room."""

    grid = make_grid(group)

    R = int(room["rows"])
    B = int(room["benches_per_row"])
    S = int(room["seats_per_bench"])

    count = 0

    for pos, subject in grid.items():
        for nb in neighbors(*pos, R, B, S, strict):
            if nb > pos and grid.get(nb) == subject:
                count += 1

    return count


def position_conflicts(grid, pos, subject, room, strict=False):
    """Count same-subject neighbours around one seat."""

    R = int(room["rows"])
    B = int(room["benches_per_row"])
    S = int(room["seats_per_bench"])

    return sum(
        grid.get(nb) == subject
        for nb in neighbors(*pos, R, B, S, strict)
    )


def repair_group(group, room, max_passes=5, strict=False):
    """Try moving or swapping students to reduce violations."""

    group = group.copy()

    for _ in range(max_passes):

        changed = False

        for idx in list(group.index):

            row = group.loc[idx]

            pos = (int(row["row"]), int(row["bench"]), int(row["seat"]))
            subject = row["subject_code"]

            grid = make_grid(group)

            # Skip students who have no adjacency conflict.
            if position_conflicts(grid, pos, subject, room, strict) == 0:
                continue

            before = count_group_violations(group, room, strict)

            # STEP 1: Try moving the student to an empty seat.

            occupied = set(grid)

            for new_pos in seat_positions(room):

                if new_pos in occupied:
                    continue

                trial = group.copy()
                trial.loc[idx, ["row", "bench", "seat"]] = list(new_pos)

                trial_grid = make_grid(trial)

                after = count_group_violations(trial, room, strict)

                if (
                    position_conflicts(
                        trial_grid, new_pos, subject, room, strict
                    ) == 0
                    and after < before
                ):
                    group = trial
                    changed = True
                    break

            if changed:
                continue

            # STEP 2: If moving fails, try swapping with another student.

            for other_idx in list(group.index):

                if other_idx == idx:
                    continue

                other = group.loc[other_idx]

                other_subject = other["subject_code"]

                if other_subject == subject:
                    continue

                other_pos = (
                    int(other["row"]),
                    int(other["bench"]),
                    int(other["seat"])
                )

                trial = group.copy()

                trial.loc[idx, ["row", "bench", "seat"]] = list(other_pos)
                trial.loc[other_idx, ["row", "bench", "seat"]] = list(pos)

                trial_grid = make_grid(trial)

                after = count_group_violations(trial, room, strict)

                first_clear = position_conflicts(
                    trial_grid, other_pos, subject, room, strict
                ) == 0

                second_clear = position_conflicts(
                    trial_grid, pos, other_subject, room, strict
                ) == 0

                if first_clear and second_clear and after < before:
                    group = trial
                    changed = True
                    break

            if changed:
                continue

        if not changed:
            break

    return group


def repair_allocation(allocation_df, rooms_df, max_passes=5, strict=False):
    """Repair adjacency violations across all exam sessions and rooms."""

    required = {
        "exam_date", "exam_slot", "room_id",
        "subject_code", "row", "bench", "seat"
    }

    missing = required - set(allocation_df.columns)

    if missing:
        raise ValueError(f"Missing allocation columns: {sorted(missing)}")

    if max_passes < 1:
        raise ValueError("max_passes must be at least 1")

    result = allocation_df.copy()

    rooms = normalize_rooms(rooms_df).set_index("room_id")

    for (date, slot, room_id), indexes in result.groupby(
        ["exam_date", "exam_slot", "room_id"]
    ).groups.items():

        if room_id not in rooms.index:
            raise ValueError(f"Room {room_id} not found in rooms data")

        room = rooms.loc[room_id]

        group = result.loc[list(indexes)].copy()

        repaired = repair_group(
            group,
            room,
            max_passes=max_passes,
            strict=strict
        )

        result.loc[repaired.index, ["row", "bench", "seat"]] = (
            repaired[["row", "bench", "seat"]]
        )

    return result


if __name__ == "__main__":

    allocation = pd.read_csv("data/processed/allocation.csv")
    rooms = pd.read_csv("data/raw/rooms.csv")

    before = len(find_violations(allocation, rooms))

    repaired = repair_allocation(allocation, rooms)

    after = len(find_violations(repaired, rooms))

    repaired.to_csv(
        "data/processed/repaired_allocation.csv",
        index=False
    )

    print(f"Violations before repair: {before}")
    print(f"Violations after repair: {after}")
    print(f"Students retained: {len(repaired)}")
    print("Repaired allocation saved!")

