# Data schema (the contract)

## students.csv (one row = one student writing one exam)
roll_no, name, email, branch, year, semester, subject_code,
exam_date, exam_slot, attendance_pct, prev_absent_count

## rooms.csv
room_id, building, floor, rows, benches_per_row, seats_per_bench,
capacity, available

## exam_schedule.csv
exam_date, exam_slot, subject_code, branch, year, reporting_time

## allocation table (output of allocate())
roll_no, name, email, subject_code, exam_date, exam_slot,
room_id, building, floor, row, bench, seat

## Rules
- capacity = rows * benches_per_row * seats_per_bench
- Adjacent seats = same bench (left/right) and the bench directly in front or behind
- All emails are fake @example.com addresses
- Function: allocate(students_df, rooms_df) -> allocation_df