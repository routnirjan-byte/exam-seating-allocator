import re
from email.message import EmailMessage
from pathlib import Path

from src.config import REPORTING_TIME

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEMPLATE_PATH = Path("templates/seat_email.txt")
UPDATE_NOTE = "Your seating has been UPDATED. Please use these details instead of any earlier email.\n\n"


def exam_lines(exams):
    """One two-line block per exam, in date order."""
    lines = []
    for e in exams.sort_values("exam_date").itertuples():
        report = REPORTING_TIME.get(e.exam_slot, "see notice")
        lines.append(f"{e.exam_date} ({e.exam_slot}, report by {report})  {e.subject_code}\n"
                     f"    Room {e.room_id}, {e.building} building, floor {e.floor}: "
                     f"row {e.row}, bench {e.bench}, seat {e.seat}")
    return "\n".join(lines)


def plan_emails(allocation_df, updated_rolls=None):
    """One consolidated email per student. Returns a list of dicts.
    updated_rolls: if given, only those students are included, marked UPDATED."""
    df = allocation_df.copy()
    df["email"] = df["email"].fillna("").astype(str).str.strip()
    owners = df[df["email"] != ""].groupby("email")["roll_no"].nunique()
    shared = set(owners[owners > 1].index)              # one address used by several students
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    updated = updated_rolls is not None

    plans = []
    for roll_no, g in df.groupby("roll_no"):
        if updated and roll_no not in updated_rolls:
            continue
        to = g["email"].iloc[0]
        status, reason = "ready", ""
        if not to:
            status, reason = "skipped", "blank email"
        elif not EMAIL_RE.match(to):
            status, reason = "skipped", "malformed email"
        elif to in shared:
            status, reason = "skipped", "email shared by several students"
        body = template.format(name=g["name"].iloc[0], roll_no=roll_no,
                               note=UPDATE_NOTE if updated else "", details=exam_lines(g))
        plans.append({"roll_no": roll_no, "to": to, "status": status, "reason": reason,
                      "subject": ("UPDATED: " if updated else "") + "Exam seat allotment",
                      "body": body})
    return plans


def build_message(plan, from_addr):
    msg = EmailMessage()
    msg["Subject"] = plan["subject"]
    msg["From"] = from_addr
    msg["To"] = plan["to"]
    msg.set_content(plan["body"])
    return msg
import re
from email.message import EmailMessage
from pathlib import Path

from src.config import REPORTING_TIME

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEMPLATE_PATH = Path("templates/seat_email.txt")
UPDATE_NOTE = "Your seating has been UPDATED. Please use these details instead of any earlier email.\n\n"


def exam_lines(exams):
    """One two-line block per exam, in date order."""
    lines = []
    for e in exams.sort_values("exam_date").itertuples():
        report = REPORTING_TIME.get(e.exam_slot, "see notice")
        lines.append(f"{e.exam_date} ({e.exam_slot}, report by {report})  {e.subject_code}\n"
                     f"    Room {e.room_id}, {e.building} building, floor {e.floor}: "
                     f"row {e.row}, bench {e.bench}, seat {e.seat}")
    return "\n".join(lines)


def plan_emails(allocation_df, updated_rolls=None):
    """One consolidated email per student. Returns a list of dicts.
    updated_rolls: if given, only those students are included, marked UPDATED."""
    df = allocation_df.copy()
    df["email"] = df["email"].fillna("").astype(str).str.strip()
    owners = df[df["email"] != ""].groupby("email")["roll_no"].nunique()
    shared = set(owners[owners > 1].index)              # one address used by several students
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    updated = updated_rolls is not None

    plans = []
    for roll_no, g in df.groupby("roll_no"):
        if updated and roll_no not in updated_rolls:
            continue
        to = g["email"].iloc[0]
        status, reason = "ready", ""
        if not to:
            status, reason = "skipped", "blank email"
        elif not EMAIL_RE.match(to):
            status, reason = "skipped", "malformed email"
        elif to in shared:
            status, reason = "skipped", "email shared by several students"
        body = template.format(name=g["name"].iloc[0], roll_no=roll_no,
                               note=UPDATE_NOTE if updated else "", details=exam_lines(g))
        plans.append({"roll_no": roll_no, "to": to, "status": status, "reason": reason,
                      "subject": ("UPDATED: " if updated else "") + "Exam seat allotment",
                      "body": body})
    return plans


def build_message(plan, from_addr):
    msg = EmailMessage()
    msg["Subject"] = plan["subject"]
    msg["From"] = from_addr
    msg["To"] = plan["to"]
    msg.set_content(plan["body"])
    return msg
