import pandas as pd


def normalize_rooms(df):
    """Accept benches_per_row x seats_per_bench, or rows x columns (one seat
    per bench). Recomputes capacity and fills building, floor, available."""
    df = df.copy()
    if "benches_per_row" not in df.columns:
        if "columns" not in df.columns:
            raise ValueError("rooms need 'benches_per_row' or 'columns'")
        df["benches_per_row"] = df["columns"]
    if "seats_per_bench" not in df.columns:
        df["seats_per_bench"] = 1
    df["capacity"] = df["rows"] * df["benches_per_row"] * df["seats_per_bench"]
    if "building" not in df.columns:
        df["building"] = "Main"
    if "floor" not in df.columns:
        df["floor"] = 0
    if "available" not in df.columns:
        df["available"] = True
    return df


def seat_positions(room):
    """All seats of one room as (row, bench, seat), 1-based, in reading order."""
    return [(r, b, s)
            for r in range(1, int(room["rows"]) + 1)
            for b in range(1, int(room["benches_per_row"]) + 1)
            for s in range(1, int(room["seats_per_bench"]) + 1)]


def neighbors(row, bench, seat, rows, benches_per_row, seats_per_bench, strict=False):
    """Seats that count as adjacent: left/right on the same bench, and the same
    position on the bench in front or behind. When a bench has one seat (or
    strict=True), the seat on the neighbouring bench also counts."""
    out = []
    if seat > 1:
        out.append((row, bench, seat - 1))
    if seat < seats_per_bench:
        out.append((row, bench, seat + 1))
    if row > 1:
        out.append((row - 1, bench, seat))
    if row < rows:
        out.append((row + 1, bench, seat))
    if strict or seats_per_bench == 1:
        if seat == 1 and bench > 1:
            out.append((row, bench - 1, seats_per_bench))
        if seat == seats_per_bench and bench < benches_per_row:
            out.append((row, bench + 1, 1))
    return out


def find_violations(allocation_df, rooms_df, strict=False):
    """List every pair of adjacent seats holding the same subject."""
    rooms = normalize_rooms(rooms_df).set_index("room_id")
    found = []
    for (date, slot, room_id), g in allocation_df.groupby(["exam_date", "exam_slot", "room_id"]):
        room = rooms.loc[room_id]
        R, B, S = int(room["rows"]), int(room["benches_per_row"]), int(room["seats_per_bench"])
        grid = {(r.row, r.bench, r.seat): r.subject_code for r in g.itertuples()}
        for pos, subject in grid.items():
            for nb in neighbors(*pos, R, B, S, strict):
                if nb > pos and grid.get(nb) == subject:      # count each pair once
                    found.append({"exam_date": date, "exam_slot": slot, "room_id": room_id,
                                  "seat_a": pos, "seat_b": nb, "subject_code": subject})
    return pd.DataFrame(found, columns=["exam_date", "exam_slot", "room_id",
                                        "seat_a", "seat_b", "subject_code"])
