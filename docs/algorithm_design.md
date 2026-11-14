# Allocation algorithm design

## 1.Goal
Seat every student in an available room so that no two adjacent seats hold
the same subject, while keeping room usage balanced. A pair of adjacent seats
with the same subject is called a violation. The target is zero violations.

## 2.Inputs and output
- Input: students.csv (one row per student per exam) and rooms.csv
- Output: an allocation table with room_id, building, floor, row, bench and
  seat for every student-exam (see docs/data_schema.md)
- Size of the current test data: 400 students, 5 papers each, 2,000 exam
  records over 10 slots, at most 200 students in one slot, 358 usable seats.

## 3. The room as a grid
A seat is written as (row, bench, seat), all numbered from 1.
Row 1 is the front of the room. Benches run left to right. Seats run left
to right on a bench.

Example: 3 rows, 3 benches per row, 2 seats per bench.

            Bench 1   Bench 2   Bench 3
    Row 1   [1][2]    [1][2]    [1][2]     <- front of room
    Row 2   [1][2]    [1][2]    [1][2]
    Row 3   [1][2]    [1][2]    [1][2]

A room file may give rows x benches_per_row x seats_per_bench, or only
rows x columns. In the second case each column is treated as a bench with
one seat. capacity = rows x benches_per_row x seats_per_bench.

## 4. What "adjacent" means
Seat (r, b, s) is adjacent to:
- (r, b, s-1) and (r, b, s+1): the other seats on the same bench
- (r-1, b, s) and (r+1, b, s): same position, bench in front or behind
- if a bench has only one seat: also the seats on the benches to the left
  and right (so such a seat has up to 4 neighbours)
Diagonal seats are not counted. A strict mode, which also counts the seat
across the gap on the next bench, exists for later use.
There is exactly one definition of adjacency, the function neighbors() in
src/rooms.py. If the college rule changes, only that function changes.

## 5. Why one slot at a time
A slot is one exam date plus Morning or Afternoon. Students from different
slots never sit in the same room together, so every slot is an independent
problem that uses the same set of rooms.

## 6. Steps for one slot
1. Group the slot's students by subject_code (these are the "pools").
2. Shuffle each pool, so the result does not depend on roll-number order.
3. Compute a quota for each available room, proportional to its capacity,
   so every room is equally full (balanced utilisation). Rounding leftovers
   go to the rooms with the biggest fractions.
4. For each room, if the quota is smaller than the number of seats, spread
   the used seats evenly. The empty seats act as separators.
5. Visit the chosen seats in reading order (row, then bench, then seat).
6. At each seat, find the subjects of the neighbours that are already seated.
   Pick the subject with the MOST students left that is not one of those.
   Seat one student from it.
7. If every remaining subject clashes with a neighbour, seat the largest
   remaining pool anyway. This is a violation, and the repair step deals
   with it.

## 7. Pseudocode
for each slot (date, session):
    pools = students grouped by subject, each pool shuffled
    quotas = students split across available rooms in proportion to capacity
    for each room, quota in zip(rooms, quotas):
        seats = all seats of the room in reading order
        if quota < len(seats): keep only 'quota' seats, evenly spread
        for each seat in seats:
            blocked = subjects of already-seated neighbours
            options = subjects with students left and not in blocked
            if options is empty: options = all subjects with students left
            subject = option with the most students left
            seat one student from that subject

## 8. Why the largest subject first
Imagine three subjects with 10, 10 and 2 students. If the small group is used
up first, the last seats can only be filled from the two big groups, and
students of the same subject end up side by side. Taking from the largest
pool first keeps the remaining groups as balanced as possible, so there are
still different subjects available to put between each other until the end.

## 9. Why checking left and front is enough
Seats are filled in reading order. When a seat is being filled, the seats
before it (left on the same bench, the previous bench for one-seat benches,
and the row in front) are already occupied, but its right and back neighbours
are still empty. So every adjacent pair is checked exactly once, at the moment
its second seat is filled. Checking all four directions would repeat the work.

## 10. Repair step (second pass)
Greedy never undoes a choice, so a tight room can leave violations. The repair
step finds every seat that has a same-subject neighbour and tries:
1. Move the student to a free seat where no neighbour clashes.
2. Otherwise swap with another student so that both new seats are clash-free.
It repeats for a limited number of passes and stops when nothing improves.
Results are reported as "violations before repair -> after repair".

## 11. Known limits
- If one subject is more than about half of a slot, zero violations is
  impossible. We report the count and never hide it.
- If a slot has more students than usable seats, the extra students are
  reported as unseated.
- The allocator is a heuristic. It is fast and explainable, but it does not
  guarantee an optimal answer. An exact solver (OR-Tools) on one small room
  can be used later to compare.

## 12. Edge cases
- Room becomes unavailable: re-run that slot, or move only the students
  from that room.
- Student added late: place them in the nearest valid empty seat. The
  function returns the affected students.
- Missing or invalid email: the student still gets a seat. The email step
  skips them and logs the reason (see docs/email_design.md).
- Re-allocation: only affected students are emailed an UPDATED message.

## 13. How we measure success
- adjacent violations (target 0), before and after repair
- coverage: percentage of students seated (target 100%)
- room utilisation: mean and spread across rooms
- average number of branches per bench (mixing)
- comparison against the baseline allocator (class-by-class seating)
- runtime for 400, 3,000 and 10,000 students