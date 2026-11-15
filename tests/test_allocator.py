import pandas as pd

from src.allocator import allocate, load_students
from src.rooms import find_violations, normalize_rooms

students = load_students()
rooms = normalize_rooms(pd.read_csv("data/raw/rooms.csv"))
alloc = allocate(students, rooms)


def test_everyone_is_seated():
    assert len(alloc) == len(students)


def test_no_adjacent_same_subject():
    assert len(find_violations(alloc, rooms)) == 0


def test_no_double_booked_seat():
    assert not alloc.duplicated(["exam_date", "exam_slot", "room_id", "row", "bench", "seat"]).any()


def test_unavailable_rooms_not_used():
    off = set(rooms.loc[~rooms["available"], "room_id"])
    assert not set(alloc["room_id"]) & off