import csv
from datetime import datetime
from pathlib import Path

LOG = Path("logs/email_log.csv")
FIELDS = ["timestamp", "roll_no", "to", "status", "reason"]


def log_result(roll_no, to, status, reason="", path=LOG):
    """Append one line: who, to which address, and what happened."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({"timestamp": datetime.now().isoformat(timespec="seconds"),
                         "roll_no": roll_no, "to": to, "status": status, "reason": reason})


def already_sent(path=LOG):
    """Roll numbers (as text) that already received a real email."""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as f:
        return {row["roll_no"] for row in csv.DictReader(f) if row["status"] == "sent"}
    
