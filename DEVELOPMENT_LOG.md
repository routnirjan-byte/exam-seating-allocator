
# Exam Seating Allocator — Development Log

## Day 1 — Project Setup & Synthetic Data Generation
- Set up the project repository and Python virtual environment.
- Installed required Python libraries.
- Explored the project structure and requirements.
- Created synthetic student data using Faker and Pandas.
- Generated sample exam seating data and a seating plan.

## Day 2 — Data Generation, Cleaning & Validation
- Created a room generator to generate room details and capacities.
- Created an exam schedule generator using the shared configuration.
- Implemented student data cleaning and validation.
- Added checks for email formats, attendance percentages, branches and missing values.
- Implemented student-schedule consistency validation.
- Created dirty student data to simulate incorrect records.
- Tested data cleaning, invalid records and duplicate removal.
- Pushed the updated files and datasets to GitHub.

## Day 3, 4 & 5 – Project Development, LinkedIn Documentation & Seating Conflict Repair

- Continued developing the Exam Seating Allocation System and worked on integrating the data generation, preprocessing, validation and seating allocation modules.
- Prepared a professional LinkedIn post highlighting the real-world problem of time-consuming manual examination seating arrangements, our proposed solution and the technical progress made by the team.
- Executed the seating allocation algorithm using the generated student, room and examination schedule datasets.
- Successfully generated seating arrangements for 2,000 student records.
- Verified the allocation for duplicate student records, duplicate seat assignments, missing values and adjacent same-subject students.
- Developed `src/repair.py` to detect and resolve seating conflicts using seat relocation and student swapping.
- Implemented functions for creating seat mappings, counting violations and checking neighbouring seat conflicts.
- Generated `repaired_allocation.csv` containing the repaired seating arrangement.
- Created `test_repair_manual.py` to test the repair mechanism by deliberately introducing an artificial seating conflict.
- Successfully reduced the artificially introduced violations from 1 to 0 while retaining all 2,000 student records.
- Pushed the completed repair module, test script and repaired allocation output to GitHub.

