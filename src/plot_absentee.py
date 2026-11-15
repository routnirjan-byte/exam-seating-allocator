from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw to a file, no window
import matplotlib.pyplot as plt
import pandas as pd

from src.absentee_model import slot_plan

scored = pd.read_csv("data/processed/absentee_predictions.csv")
plan = slot_plan(scored).reset_index()
labels = plan["exam_date"].astype(str).str[5:] + " " + plan["exam_slot"].str[:3]

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(labels, plan["expected_absent"], label="expected absentees")
ax.plot(labels, plan["likely_max_absent"], color="red", marker="o", label="likely maximum (95%)")
ax.set_ylabel("students")
ax.set_title("Expected absentees per exam slot (simulated labels)")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
Path("assets").mkdir(exist_ok=True)
plt.savefig("assets/absentee_per_slot.png", dpi=150)
print("saved assets/absentee_per_slot.png")