import pandas as pd

from src.rooms import find_violations, neighbors, normalize_rooms, seat_positions

ROOMS = pd.DataFrame([{"room_id": "T-01", "rows": 2, "benches_per_row": 2, "seats_per_bench": 2}])


def make_alloc(subjects):
    positions = seat_positions(normalize_rooms(ROOMS).iloc[0])
    rows = [{"exam_date": "d1", "exam_slot": "Morning", "room_id": "T-01",
             "row": p[0], "bench": p[1], "seat": p[2], "subject_code": s}
            for p, s in zip(positions, subjects)]
    return pd.DataFrame(rows)


def test_seat_count():
    assert len(seat_positions({"rows": 5, "benches_per_row": 6, "seats_per_bench": 2})) == 60


def test_corner_seat_has_two_neighbors():
    nb = neighbors(1, 1, 1, rows=3, benches_per_row=3, seats_per_bench=2)
    assert sorted(nb) == [(1, 1, 2), (2, 1, 1)]


def test_middle_seat_has_three_neighbors():
    assert len(neighbors(2, 2, 1, rows=3, benches_per_row=3, seats_per_bench=2)) == 3


def test_single_seat_bench_has_four_neighbors():
    assert len(neighbors(2, 2, 1, rows=3, benches_per_row=3, seats_per_bench=1)) == 4


def test_columns_format_is_accepted():
    r = normalize_rooms(pd.DataFrame([{"room_id": "R101", "rows": 5, "columns": 6}]))
    assert r.loc[0, "capacity"] == 30 and r.loc[0, "seats_per_bench"] == 1


def test_all_same_subject_gives_eight_violations():
    assert len(find_violations(make_alloc(["A"] * 8), ROOMS)) == 8


def test_checkerboard_has_no_violations():
    assert len(find_violations(make_alloc(list("ABABBABA")), ROOMS)) == 0