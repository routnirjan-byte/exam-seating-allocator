import html
import io
import os
import re
import smtplib
import ssl
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.email_builder import plan_emails

load_dotenv()

# ---- one-time theme bootstrap ----
THEME_CONFIG = """[theme]
base = "dark"
primaryColor = "#34D399"
backgroundColor = "#0B1210"
secondaryBackgroundColor = "#131C18"
textColor = "#E6EFEA"
font = "sans serif"

[client]
toolbarMode = "minimal"
showSidebarNavigation = false
"""
_cfg = Path(".streamlit/config.toml")
THEME_CREATED = False
if not _cfg.exists():
    _cfg.parent.mkdir(exist_ok=True)
    _cfg.write_text(THEME_CONFIG)
    THEME_CREATED = True


# =========================================================
# 1. PAGE CONFIG (sidebar enabled)
# =========================================================

st.set_page_config(
    page_title="Exam Seating & Notification Centre",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. STYLING
# =========================================================

ACCENT = "#34D399"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
    .stApp { background: #0B1210; }

    /* hide only top toolbar/menu/footer; KEEP sidebar visible */
    [data-testid="stToolbar"],
    #MainMenu, footer { display: none !important; visibility: hidden; }

    [data-testid="stSidebar"] {
        background: #0F1714;
        border-right: 1px solid #1F2B26;
    }

    .block-container { max-width: 1320px; padding-top: 1.2rem; padding-bottom: 3rem; }

    h1, h2, h3, h4 { color: #F0F5F2; letter-spacing: -0.01em; }
    hr { border-color: #1F2B26; margin: 1.4rem 0; }

    /* top bar */
    .topbar { display:flex; align-items:center; justify-content:space-between;
              padding: 6px 0 16px 0; border-bottom: 1px solid #1F2B26; margin-bottom: 18px; }
    .brand { display:flex; align-items:center; gap:12px; }
    .logo { width:36px; height:36px; border-radius:10px; background:#34D399; color:#06281C;
            display:flex; align-items:center; justify-content:center; font-weight:700; }
    .brand-title { color:#F0F5F2; font-size:17px; font-weight:600; line-height:1.2; }
    .brand-sub { color:#7F9188; font-size:12px; }
    .badge { font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
             color:#34D399; background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.3);
             padding:4px 10px; border-radius:999px; }

    /* page heading */
    .page-title { color:#F0F5F2; font-size:24px; font-weight:700; margin:12px 0 2px 0; }
    .page-sub { color:#8FA197; font-size:14px; margin-bottom:16px; }
    .section-title { color:#F0F5F2; font-size:16px; font-weight:600; margin: 4px 0 10px 0; }

    /* KPI cards */
    .kpi { background:#131C18; border:1px solid #22302A; border-radius:14px; padding:16px 18px; }
    .kpi-label { color:#8FA197; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; }
    .kpi-value { color:#F0F5F2; font-size:26px; font-weight:700; margin-top:6px; }

    /* email preview */
    .mail { background:#131C18; border:1px solid #22302A; border-radius:14px; overflow:hidden; }
    .mail-head { padding:16px 20px; border-bottom:1px solid #22302A; }
    .mail-row { display:flex; gap:12px; font-size:14px; padding:3px 0; }
    .mail-key { color:#7F9188; width:64px; flex-shrink:0; }
    .mail-val { color:#E6EFEA; }
    .mail-body { padding:20px; color:#D6E2DB; font-size:14px; line-height:1.65; white-space:pre-wrap; }

    /* seating grid */
    .grid-wrap { display:grid; gap:10px; margin-top:12px; }
    .seat-card { border-radius:10px; padding:10px 12px; border:1px solid rgba(255,255,255,0.12);
                 font-size:12px; line-height:1.35; }
    .seat-roll { font-weight:700; font-size:13px; color:#FFFFFF; }
    .seat-meta { color:#E6EFEA; opacity:0.9; font-size:11px; }
    .legend-chip { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px;
                   font-weight:600; margin:0 6px 6px 0; color:#FFFFFF; }

    .pill { display:inline-block; font-size:12px; font-weight:600; padding:4px 12px; border-radius:999px; }
    .pill-ok { color:#34D399; background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.3); }
    .pill-warn { color:#FBBF24; background:rgba(251,191,36,.1); border:1px solid rgba(251,191,36,.3); }
    .pill-err { color:#F87171; background:rgba(248,113,113,.1); border:1px solid rgba(248,113,113,.3); }

    /* dark widget styling */
    .stApp, .stApp p, .stApp label { color: #E6EFEA; }
    [data-testid="stWidgetLabel"] p { color: #AEBDB5; }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div, input {
        background:#131C18 !important; color:#E6EFEA !important; border-color:#22302A !important; }
    [data-baseweb="popover"] ul { background:#131C18 !important; }
    [data-baseweb="popover"] li { color:#E6EFEA !important; }

    .stButton > button, .stDownloadButton > button {
        border-radius: 10px; border: 1px solid #2C4A3C; background:#131C18; color:#E6EFEA; }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:#34D399; color:#34D399; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; border-color:#22302A; }
    [data-testid="stDataFrame"] { border:1px solid #22302A; border-radius:12px; overflow:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. PATHS & CONSTANTS
# =========================================================

ALLOCATION_PATH = Path("data/processed/allocation.csv")
LOG_PATH = Path("logs/email_log.csv")
ABSENTEE_PATH = Path("data/processed/absentee_predictions.csv")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SUBJECT_PALETTE = [
    "#065F46", "#1E3A8A", "#5B21B6", "#9D174D",
    "#9A3412", "#115E59", "#3F6212", "#854D0E",
]


# =========================================================
# 4. SMTP CONFIG (ENV VARS OR STREAMLIT SECRETS ONLY)
# =========================================================

def get_smtp_config() -> dict:
    """Read SMTP settings from environment variables or Streamlit secrets."""
    def _read(key: str, default: str = "") -> str:
        val = os.getenv(key)
        if val:
            return str(val).strip()
        try:
            if key in st.secrets:
                return str(st.secrets[key]).strip()
            if "smtp" in st.secrets and key in st.secrets["smtp"]:
                return str(st.secrets["smtp"][key]).strip()
        except Exception:
            pass
        return default

    return {
        "host": _read("SMTP_HOST", "smtp.gmail.com"),
        "port": int(_read("SMTP_PORT", "465") or "465"),
        "user": _read("SMTP_USER", ""),
        "password": _read("SMTP_PASSWORD", ""),
        "from_name": _read("FROM_NAME", "Exam Cell"),
    }


def smtp_is_configured(cfg: dict) -> bool:
    return bool(cfg["host"] and cfg["port"] and cfg["user"] and cfg["password"])


def open_smtp_connection(cfg: dict):
    if cfg["port"] == 465:
        ctx = ssl.create_default_context()
        server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx, timeout=20)
    else:
        server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
        server.starttls(context=ssl.create_default_context())
    server.login(cfg["user"], cfg["password"])
    return server


def send_single_smtp_email(server, cfg: dict, to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    server.send_message(msg)


def append_email_log(records: list[dict]):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame(records)
    if LOG_PATH.exists() and LOG_PATH.stat().st_size > 0:
        old_df = pd.read_csv(LOG_PATH)
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(LOG_PATH, index=False)


# =========================================================
# 5. SAMPLE DATA, VALIDATION & ALLOCATION ENGINE
# =========================================================

def build_sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load sample data from disk if available, otherwise synthesize realistic datasets."""
    if ALLOCATION_PATH.exists():
        existing = pd.read_csv(ALLOCATION_PATH)
        student_cols = [c for c in ["roll_no", "name", "email", "subject_code", "exam_date", "exam_slot"] if c in existing.columns]
        students = existing[student_cols].drop_duplicates().reset_index(drop=True)
        rooms = (
            existing.groupby(["room_id", "building", "floor"], as_index=False)
            .agg(
                rows=("row", "max"),
                benches_per_row=("bench", "max"),
                seats_per_bench=("seat", "max"),
            )
        )
        rooms["capacity"] = rooms["rows"] * rooms["benches_per_row"] * rooms["seats_per_bench"]
        return students, rooms

    # Fallback built-in sample dataset (includes intentional bad emails for validation demo)
    subjects = ["AI301", "DS302", "CS303", "ML304"]
    rows_s = []
    for i in range(1, 49):
        email = f"student{i:02d}@college.edu"
        if i == 12:
            email = ""  # missing email
        elif i == 25:
            email = "invalid-email-format"  # bad email
        rows_s.append({
            "roll_no": f"CS26{i:03d}",
            "name": f"Student {i:02d}",
            "email": email,
            "subject_code": subjects[(i - 1) % len(subjects)],
            "exam_date": "2026-12-01" if i <= 32 else "2026-12-03",
            "exam_slot": "Morning" if i % 2 else "Afternoon",
        })
    students = pd.DataFrame(rows_s)

    rooms = pd.DataFrame([
        {"room_id": "A-101", "building": "Main", "floor": 1, "rows": 4, "benches_per_row": 3, "seats_per_bench": 2, "capacity": 24},
        {"room_id": "A-102", "building": "Main", "floor": 1, "rows": 4, "benches_per_row": 3, "seats_per_bench": 2, "capacity": 24},
        {"room_id": "B-201", "building": "Annex", "floor": 2, "rows": 3, "benches_per_row": 3, "seats_per_bench": 2, "capacity": 18},
        {"room_id": "B-202", "building": "Annex", "floor": 2, "rows": 3, "benches_per_row": 3, "seats_per_bench": 2, "capacity": 18},
    ])
    return students, rooms


def validate_inputs(students: pd.DataFrame | None, rooms: pd.DataFrame | None) -> dict:
    """Return structured warnings and email validation counts."""
    warnings = []
    missing_emails = 0
    invalid_emails = 0

    if students is not None and not students.empty:
        req_s = {"roll_no", "name", "subject_code", "exam_date", "exam_slot"}
        missing_cols = req_s - set(students.columns)
        if missing_cols:
            warnings.append(f"Students CSV missing required columns: {', '.join(sorted(missing_cols))}")

        if "roll_no" in students.columns and "exam_date" in students.columns and "exam_slot" in students.columns:
            dup_count = int(students.duplicated(subset=["roll_no", "exam_date", "exam_slot"]).sum())
            if dup_count > 0:
                warnings.append(f"{dup_count} duplicate student-slot entries found.")

        if "email" not in students.columns:
            missing_emails = len(students)
            warnings.append("Students CSV has no 'email' column — all students will be skipped during notifications.")
        else:
            emails = students["email"].fillna("").astype(str).str.strip()
            missing_emails = int((emails == "").sum())
            non_empty = emails[emails != ""]
            invalid_emails = int((~non_empty.str.match(EMAIL_RE)).sum())
            if missing_emails > 0 or invalid_emails > 0:
                warnings.append(
                    f"Email validation: {missing_emails} missing and {invalid_emails} invalid email(s) "
                    f"({missing_emails + invalid_emails} total unmailable)."
                )

    if rooms is not None and not rooms.empty:
        req_r = {"room_id"}
        missing_r = req_r - set(rooms.columns)
        if missing_r:
            warnings.append(f"Rooms CSV missing required columns: {', '.join(sorted(missing_r))}")
        if "capacity" in rooms.columns:
            bad_cap = int((pd.to_numeric(rooms["capacity"], errors="coerce").fillna(0) <= 0).sum())
            if bad_cap > 0:
                warnings.append(f"{bad_cap} room(s) have missing or non-positive capacity.")

    return {
        "warnings": warnings,
        "missing_emails": missing_emails,
        "invalid_emails": invalid_emails,
    }


def _normalize_rooms(rooms: pd.DataFrame) -> pd.DataFrame:
    df = rooms.copy()
    if "building" not in df.columns:
        df["building"] = "Main"
    if "floor" not in df.columns:
        df["floor"] = 1
    if "seats_per_bench" not in df.columns:
        df["seats_per_bench"] = 2
    if "benches_per_row" not in df.columns:
        df["benches_per_row"] = 3
    if "rows" not in df.columns:
        cap = pd.to_numeric(df.get("capacity", 24), errors="coerce").fillna(24).astype(int)
        per_row = (df["benches_per_row"] * df["seats_per_bench"]).clip(lower=1)
        df["rows"] = ((cap + per_row - 1) // per_row).clip(lower=1)
    if "capacity" not in df.columns:
        df["capacity"] = df["rows"] * df["benches_per_row"] * df["seats_per_bench"]
    return df


def _order_students_by_mixing(slot_df: pd.DataFrame, mixing_priority: str) -> pd.DataFrame:
    if mixing_priority.startswith("Low"):
        return slot_df.sort_values(["subject_code", "roll_no"]).reset_index(drop=True)

    # Round-robin interleave subjects (High / Medium)
    groups = [
        g.sort_values("roll_no").to_dict("records")
        for _, g in slot_df.groupby("subject_code", sort=True)
    ]
    groups.sort(key=len, reverse=True)
    step = 1 if mixing_priority.startswith("High") else 2
    ordered = []
    while any(groups):
        for g in groups:
            for _ in range(step):
                if g:
                    ordered.append(g.pop(0))
    return pd.DataFrame(ordered)


def generate_seating_allocation(
    students: pd.DataFrame,
    rooms: pd.DataFrame,
    buffer_pct: int = 10,
    mixing_priority: str = "High (Interleave subjects)",
    unavailable_rooms: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Allocate seats per (exam_date, exam_slot) respecting buffer %, mixing, and room availability."""
    unavailable_set = set(unavailable_rooms or [])
    r_df = _normalize_rooms(rooms)
    active_rooms = r_df[~r_df["room_id"].astype(str).isin(unavailable_set)].reset_index(drop=True)

    issues = []
    if active_rooms.empty:
        return pd.DataFrame(), ["No available rooms left for allocation."]

    # Build seat pool per room applying buffer %
    room_seat_pools = []
    for r in active_rooms.itertuples():
        raw_seats = []
        for rw in range(1, int(r.rows) + 1):
            for bn in range(1, int(r.benches_per_row) + 1):
                for st_no in range(1, int(r.seats_per_bench) + 1):
                    raw_seats.append({
                        "room_id": str(r.room_id),
                        "building": str(r.building),
                        "floor": int(r.floor),
                        "row": rw,
                        "bench": bn,
                        "seat": st_no,
                    })
        eff_cap = max(1, int(len(raw_seats) * (1 - buffer_pct / 100.0)))
        room_seat_pools.extend(raw_seats[:eff_cap])

    s_df = students.copy()
    if "email" not in s_df.columns:
        s_df["email"] = ""

    allocated_rows = []
    for (edate, eslot), slot_group in s_df.groupby(["exam_date", "exam_slot"], sort=True):
        ordered = _order_students_by_mixing(slot_group, mixing_priority)
        if len(ordered) > len(room_seat_pools):
            overflow = len(ordered) - len(room_seat_pools)
            issues.append(
                f"{edate} ({eslot}): {overflow} student(s) could not be seated "
                f"(need {len(ordered)}, available {len(room_seat_pools)} after {buffer_pct}% buffer)."
            )
        for stu, seat_info in zip(ordered.to_dict("records"), room_seat_pools):
            allocated_rows.append({
                "roll_no": str(stu["roll_no"]),
                "name": str(stu["name"]),
                "email": str(stu.get("email", "") if pd.notna(stu.get("email", "")) else "").strip(),
                "subject_code": str(stu["subject_code"]),
                "exam_date": str(edate),
                "exam_slot": str(eslot),
                **seat_info,
            })

    return pd.DataFrame(allocated_rows), issues


def find_affected_rolls(old_df: pd.DataFrame, new_df: pd.DataFrame) -> set[str]:
    """Return roll numbers whose room or seat changed after re-allocation."""
    key_cols = ["roll_no", "exam_date", "exam_slot"]
    pos_cols = ["room_id", "row", "bench", "seat"]
    if old_df.empty or new_df.empty:
        return set()
    merged = old_df[key_cols + pos_cols].merge(
        new_df[key_cols + pos_cols], on=key_cols, how="outer", suffixes=("_old", "_new")
    )
    changed_mask = False
    for c in pos_cols:
        changed_mask = changed_mask | (merged[f"{c}_old"].astype(str) != merged[f"{c}_new"].astype(str))
    return set(merged.loc[changed_mask, "roll_no"].astype(str).unique())


# =========================================================
# 6. PURE-PYTHON PRINTABLE PDF NOTICE-BOARD GENERATOR
# =========================================================

def _pdf_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_notice_board_pdf(df: pd.DataFrame) -> bytes:
    """Build a clean, multi-page printable PDF notice-board sheet without external PDF libraries."""
    lines_per_page = 46
    pages_lines: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []

    def push(text: str, bold: bool = False):
        nonlocal current
        if len(current) >= lines_per_page:
            pages_lines.append(current)
            current = []
        current.append((text[:95], bold))

    push("EXAMINATION SEATING NOTICE-BOARD SHEET", bold=True)
    push(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Total Records: {len(df)}", bold=False)
    push("-" * 92, bold=False)

    grouped = df.sort_values(["exam_date", "exam_slot", "room_id", "row", "bench", "seat"]).groupby(
        ["exam_date", "exam_slot", "room_id", "building", "floor"], sort=True
    )
    for (edate, eslot, room_id, bldg, floor), grp in grouped:
        if len(current) > lines_per_page - 5:
            pages_lines.append(current)
            current = []
        push(f"ROOM {room_id} ({bldg}, Floor {floor})  |  {edate} - {eslot}  |  Students: {len(grp)}", bold=True)
        push(f"{'ROLL NO':<14} {'NAME':<26} {'SUBJECT':<12} {'ROW':<5} {'BENCH':<7} {'SEAT':<5}", bold=True)
        for r in grp.itertuples():
            push(
                f"{str(r.roll_no):<14} {str(r.name)[:24]:<26} {str(r.subject_code):<12} "
                f"{str(r.row):<5} {str(r.bench):<7} {str(r.seat):<5}",
                bold=False,
            )
        push("", bold=False)

    if current:
        pages_lines.append(current)

    # Assemble minimal valid PDF 1.4
    objects: list[bytes] = []
    # Obj 1: Catalog, Obj 2: Pages, Obj 3: Font Regular (Courier), Obj 4: Font Bold (Courier-Bold)
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    page_obj_ids = []
    content_obj_ids = []
    next_id = 5
    for _ in pages_lines:
        page_obj_ids.append(next_id)
        content_obj_ids.append(next_id + 1)
        next_id += 2

    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>\nendobj\n".encode())
    objects.append(b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>\nendobj\n")

    for pid, cid, plines in zip(page_obj_ids, content_obj_ids, pages_lines):
        stream_cmds = ["BT", "36 800 Td", "15 TL"]
        for txt, is_bold in plines:
            font_ref = "/F2" if is_bold else "/F1"
            size = 10 if is_bold else 9
            stream_cmds.append(f"{font_ref} {size} Tf ({_pdf_escape(txt)}) Tj T*")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin-1", errors="replace")

        objects.append(
            f"{pid} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {cid} 0 R >>\nendobj\n".encode()
        )
        objects.append(
            f"{cid} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode()
            + stream_bytes
            + b"\nendstream\nendobj\n"
        )

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(buf.tell())
        buf.write(obj)

    xref_pos = buf.tell()
    buf.write(f"xref\n0 {len(objects) + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        buf.write(f"{off:010d} 00000 n \n".encode())

    buf.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode()
    )
    return buf.getvalue()


# =========================================================
# 7. UI HELPERS
# =========================================================

def page_header(title: str, subtitle: str):
    st.markdown(
        f'<div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def section(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpis(items):
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def bar(series: pd.Series, height: int = 260):
    df = series.reset_index()
    df.columns = ["label", "value"]
    df["label"] = df["label"].astype(str)
    chart = (
        alt.Chart(df)
        .mark_bar(color=ACCENT, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("label:N", sort=None, title=None, axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("value:Q", title=None),
            tooltip=["label", "value"],
        )
        .properties(height=height)
        .configure(background="transparent")
        .configure_axis(labelColor="#8FA197", gridColor="#1A2520", domain=False, tickColor="#1A2520")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def table(df: pd.DataFrame):
    st.dataframe(df, hide_index=True, use_container_width=True)


def safe_plan_emails(df: pd.DataFrame, updated_rolls: set[str] | None = None) -> list[dict]:
    if updated_rolls:
        try:
            return plan_emails(df, updated_rolls=updated_rolls)
        except TypeError:
            return plan_emails(df, updated_rolls)
    return plan_emails(df)


# =========================================================
# 8. SESSION STATE INIT
# =========================================================

if "students_df" not in st.session_state:
    st.session_state["students_df"] = None
if "rooms_df" not in st.session_state:
    st.session_state["rooms_df"] = None
if "allocation" not in st.session_state:
    st.session_state["allocation"] = pd.read_csv(ALLOCATION_PATH) if ALLOCATION_PATH.exists() else None
if "unavailable_rooms" not in st.session_state:
    st.session_state["unavailable_rooms"] = []
if "affected_rolls" not in st.session_state:
    st.session_state["affected_rolls"] = set()
if "last_send_results" not in st.session_state:
    st.session_state["last_send_results"] = []
if "alloc_issues" not in st.session_state:
    st.session_state["alloc_issues"] = []


# =========================================================
# 9. SIDEBAR: UPLOADS, SAMPLE DATA, VALIDATION & CONTROLS
# =========================================================

with st.sidebar:
    st.markdown("### 1. Data Input")
    stu_file = st.file_uploader("Upload Students CSV", type=["csv"], key="stu_csv")
    room_file = st.file_uploader("Upload Rooms CSV", type=["csv"], key="room_csv")

    if stu_file is not None:
        st.session_state["students_df"] = pd.read_csv(stu_file)
    if room_file is not None:
        st.session_state["rooms_df"] = pd.read_csv(room_file)

    if st.button("Load Sample Data", use_container_width=True):
        s_sample, r_sample = build_sample_data()
        st.session_state["students_df"] = s_sample
        st.session_state["rooms_df"] = r_sample
        st.session_state["unavailable_rooms"] = []
        st.session_state["affected_rolls"] = set()
        st.success(f"Loaded {len(s_sample)} student rows & {len(r_sample)} rooms.")

    # Validation feedback
    st.markdown("---")
    st.markdown("### 2. Validation Feedback")
    val_report = validate_inputs(st.session_state["students_df"], st.session_state["rooms_df"])
    if st.session_state["students_df"] is None and st.session_state["rooms_df"] is None:
        st.caption("Upload CSVs or click **Load Sample Data** to validate.")
    else:
        if val_report["warnings"]:
            for w in val_report["warnings"]:
                st.warning(w)
        else:
            st.success("All student, room, and email checks passed.")

    # Parameter controls
    st.markdown("---")
    st.markdown("### 3. Allocation Parameters")
    buffer_pct = st.slider("Room Capacity Buffer (%)", min_value=0, max_value=50, value=10, step=5)
    mixing_priority = st.selectbox(
        "Subject Mixing Priority",
        [
            "High (Interleave subjects)",
            "Medium (Alternate pairs)",
            "Low (Group by subject)",
        ],
    )

    st.markdown("---")
    can_generate = (
        st.session_state["students_df"] is not None
        and st.session_state["rooms_df"] is not None
    )
    if st.button("Generate Allocation", type="primary", use_container_width=True, disabled=not can_generate):
        new_alloc, issues = generate_seating_allocation(
            st.session_state["students_df"],
            st.session_state["rooms_df"],
            buffer_pct=buffer_pct,
            mixing_priority=mixing_priority,
            unavailable_rooms=st.session_state["unavailable_rooms"],
        )
        st.session_state["allocation"] = new_alloc
        st.session_state["alloc_issues"] = issues
        st.session_state["affected_rolls"] = set()
        if not new_alloc.empty:
            ALLOCATION_PATH.parent.mkdir(parents=True, exist_ok=True)
            new_alloc.to_csv(ALLOCATION_PATH, index=False)
            st.success(f"Generated {len(new_alloc)} seat assignments.")


# =========================================================
# 10. TOP BAR & GUARD
# =========================================================

st.markdown(
    '<div class="topbar">'
    '<div class="brand"><div class="logo">EN</div>'
    '<div><div class="brand-title">Exam Seating &amp; Notification Centre</div>'
    '<div class="brand-sub">Allocation engine, room seating grids &amp; student notifications</div></div></div>'
    '<span class="badge">Exam Cell Workspace</span>'
    '</div>',
    unsafe_allow_html=True,
)

if THEME_CREATED:
    st.info("Theme file created. Restart the app once (Ctrl+C, then `python -m streamlit run ui/notify.py`) to apply it.")

# Show validation warnings prominently in main area too if present
if val_report["warnings"]:
    with st.expander(f"Data Validation Warnings ({len(val_report['warnings'])})", expanded=True):
        for w in val_report["warnings"]:
            st.warning(w)

for issue in st.session_state.get("alloc_issues", []):
    st.error(issue)

allocation = st.session_state["allocation"]
if allocation is None or allocation.empty:
    st.info("No allocation loaded yet. Use the **Sidebar** to upload CSVs or click **Load Sample Data** → **Generate Allocation**.")
    st.stop()


# =========================================================
# 11. DOWNLOADS BAR (CSV + PRINTABLE PDF NOTICE-BOARD SHEET)
# =========================================================

dl_c1, dl_c2, dl_c3 = st.columns([2, 1, 1])
with dl_c1:
    st.caption(
        f"Active Allocation: **{allocation['roll_no'].nunique():,} students** · "
        f"**{len(allocation):,} seats** · **{allocation['room_id'].nunique():,} rooms**"
    )
with dl_c2:
    st.download_button(
        "Download Allocation CSV",
        data=allocation.to_csv(index=False),
        file_name="exam_allocation.csv",
        mime="text/csv",
        use_container_width=True,
    )
with dl_c3:
    pdf_bytes = generate_notice_board_pdf(allocation)
    st.download_button(
        "Download PDF Notice Sheet",
        data=pdf_bytes,
        file_name="notice_board_seating.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# =========================================================
# 12. RESULTS TABS
# =========================================================

tabs = st.tabs([
    "Metrics Dashboard",
    "Room-wise Seating Grid",
    "Student Search",
    "Edge-Case Panel",
    "Notify Students",
    "History",
])


# ----- TAB 1: METRICS DASHBOARD -----
with tabs[0]:
    page_header("Metrics Dashboard", "Overview of seating utilization, subject spread, and email readiness.")

    email_series = allocation["email"].fillna("").astype(str).str.strip() if "email" in allocation.columns else pd.Series([""] * len(allocation))
    bad_email_count = int((~email_series.str.match(EMAIL_RE)).sum())

    kpis([
        ("Students", f"{allocation['roll_no'].nunique():,}"),
        ("Seat Records", f"{len(allocation):,}"),
        ("Subjects", f"{allocation['subject_code'].nunique():,}"),
        ("Rooms Used", f"{allocation['room_id'].nunique():,}"),
        ("Missing/Invalid Emails", f"{bad_email_count:,}"),
    ])

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section("Students by Subject")
            bar(allocation.groupby("subject_code")["roll_no"].nunique().sort_values(ascending=False))
    with c2:
        with st.container(border=True):
            section("Students by Exam Date")
            bar(allocation.groupby("exam_date")["roll_no"].nunique())

    st.write("")
    section("Room Utilization Summary")
    room_summary = (
        allocation.groupby(["room_id", "building", "floor"])
        .agg(
            students=("roll_no", "nunique"),
            records=("roll_no", "count"),
            subjects=("subject_code", "nunique"),
        )
        .reset_index()
        .sort_values("students", ascending=False)
    )
    table(room_summary)

    if ABSENTEE_PATH.exists():
        st.write("")
        with st.expander("Absentee Analytics (Advisory)"):
            abs_df = pd.read_csv(ABSENTEE_PATH)
            table(abs_df.head(20))


# ----- TAB 2: ROOM-WISE SEATING GRID (COLORED BY SUBJECT) -----
with tabs[1]:
    page_header("Room-wise Seating Grid", "Visual seating map color-coded by subject.")

    fc1, fc2, fc3 = st.columns(3)
    dates = sorted(allocation["exam_date"].astype(str).unique())
    sel_date = fc1.selectbox("Exam Date", dates, key="grid_date")

    date_df = allocation[allocation["exam_date"].astype(str) == sel_date]
    slots = sorted(date_df["exam_slot"].astype(str).unique())
    sel_slot = fc2.selectbox("Exam Slot", slots, key="grid_slot")

    slot_df = date_df[date_df["exam_slot"].astype(str) == sel_slot]
    rooms_in_slot = sorted(slot_df["room_id"].astype(str).unique())
    sel_room = fc3.selectbox("Room", rooms_in_slot, key="grid_room")

    room_df = slot_df[slot_df["room_id"].astype(str) == sel_room].sort_values(["row", "bench", "seat"])

    # Subject color map & legend
    all_subjects = sorted(allocation["subject_code"].astype(str).unique())
    subj_colors = {s: SUBJECT_PALETTE[i % len(SUBJECT_PALETTE)] for i, s in enumerate(all_subjects)}

    legend_html = "".join(
        f'<span class="legend-chip" style="background:{subj_colors[s]};">{html.escape(s)}</span>'
        for s in sorted(room_df["subject_code"].astype(str).unique())
    )
    st.markdown(f"<div style='margin:8px 0 12px 0;'>{legend_html}</div>", unsafe_allow_html=True)

    if room_df.empty:
        st.info("No students seated in this room for the selected slot.")
    else:
        max_benches = int(room_df["bench"].max())
        max_seats = int(room_df["seat"].max())
        cols_per_row = max(2, min(6, max_benches * max_seats))

        cards_html = []
        for r in room_df.itertuples():
            bg = subj_colors.get(str(r.subject_code), "#1F2937")
            cards_html.append(
                f'<div class="seat-card" style="background:{bg};">'
                f'<div class="seat-roll">{html.escape(str(r.roll_no))}</div>'
                f'<div class="seat-meta">{html.escape(str(r.name))}</div>'
                f'<div class="seat-meta"><b>{html.escape(str(r.subject_code))}</b> · '
                f'R{r.row} B{r.bench} S{r.seat}</div>'
                f'</div>'
            )
        st.markdown(
            f'<div class="grid-wrap" style="grid-template-columns: repeat({cols_per_row}, minmax(130px, 1fr));">'
            + "".join(cards_html)
            + "</div>",
            unsafe_allow_html=True,
        )


# ----- TAB 3: STUDENT SEARCH BY ROLL NUMBER -----
with tabs[2]:
    page_header("Student Search", "Look up any student's seat allotment by roll number or name.")

    query = st.text_input("Enter Roll Number or Student Name", placeholder="e.g. CS26001 or Student 01")
    filtered = allocation.copy()
    if query.strip():
        filtered = filtered[
            filtered["roll_no"].astype(str).str.contains(query.strip(), case=False, na=False)
            | filtered["name"].astype(str).str.contains(query.strip(), case=False, na=False)
        ]

    kpis([
        ("Matching Students", f"{filtered['roll_no'].nunique():,}"),
        ("Matching Exam Seats", f"{len(filtered):,}"),
    ])
    st.write("")
    display_cols = [
        c for c in [
            "roll_no", "name", "email", "subject_code", "exam_date",
            "exam_slot", "room_id", "building", "floor", "row", "bench", "seat",
        ] if c in filtered.columns
    ]
    table(filtered[display_cols])


# ----- TAB 4: EDGE-CASE PANEL (MARK ROOM UNAVAILABLE & RE-ALLOCATE) -----
with tabs[3]:
    page_header("Edge-Case Panel", "Mark rooms unavailable and re-allocate affected students.")

    if st.session_state["students_df"] is None or st.session_state["rooms_df"] is None:
        st.info("Load or upload Students & Rooms CSVs in the sidebar to enable dynamic room re-allocation.")
        if st.button("Extract Students & Rooms From Current Allocation"):
            s_ext, r_ext = build_sample_data()
            st.session_state["students_df"] = s_ext
            st.session_state["rooms_df"] = r_ext
            st.rerun()
    else:
        all_room_ids = sorted(st.session_state["rooms_df"]["room_id"].astype(str).unique())
        marked_unavail = st.multiselect(
            "Mark Room(s) Unavailable",
            options=all_room_ids,
            default=[r for r in st.session_state["unavailable_rooms"] if r in all_room_ids],
        )

        if st.button("Re-allocate Without Selected Room(s)", type="primary"):
            old_alloc = allocation.copy()
            st.session_state["unavailable_rooms"] = marked_unavail
            new_alloc, issues = generate_seating_allocation(
                st.session_state["students_df"],
                st.session_state["rooms_df"],
                buffer_pct=buffer_pct,
                mixing_priority=mixing_priority,
                unavailable_rooms=marked_unavail,
            )
            st.session_state["alloc_issues"] = issues
            if not new_alloc.empty:
                affected = find_affected_rolls(old_alloc, new_alloc)
                st.session_state["allocation"] = new_alloc
                st.session_state["affected_rolls"] = affected
                ALLOCATION_PATH.parent.mkdir(parents=True, exist_ok=True)
                new_alloc.to_csv(ALLOCATION_PATH, index=False)
                st.success(
                    f"Re-allocation complete. **{len(affected)} student(s)** had their room/seat changed. "
                    f"Go to **Notify Students** to email affected students only."
                )
                st.rerun()
            else:
                st.error("Re-allocation failed — not enough remaining rooms.")

        if st.session_state["affected_rolls"]:
            section(f"Affected Students ({len(st.session_state['affected_rolls'])})")
            aff_df = allocation[allocation["roll_no"].astype(str).isin(st.session_state["affected_rolls"])]
            table(aff_df[["roll_no", "name", "email", "exam_date", "exam_slot", "room_id", "row", "bench", "seat"]])


# ----- TAB 5: NOTIFY STUDENTS -----
with tabs[4]:
    page_header("Notify Students", "Preview, test, dry-run, and dispatch student seating emails safely.")

    smtp_cfg = get_smtp_config()
    smtp_ready = smtp_is_configured(smtp_cfg)

    if smtp_ready:
        st.markdown(
            f'<span class="pill pill-ok">SMTP Configured</span> &nbsp; '
            f'Host: <code>{html.escape(smtp_cfg["host"])}:{smtp_cfg["port"]}</code> · '
            f'Sender: <code>{html.escape(smtp_cfg["user"])}</code> (loaded from environment/secrets)',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="pill pill-err">SMTP Not Configured</span> &nbsp; '
            'Set <code>SMTP_HOST</code>, <code>SMTP_PORT</code>, <code>SMTP_USER</code>, and '
            '<code>SMTP_PASSWORD</code> in <code>.env</code> or <code>.streamlit/secrets.toml</code>.',
            unsafe_allow_html=True,
        )

    st.write("")
    affected_rolls = st.session_state.get("affected_rolls", set())
    email_plans = safe_plan_emails(allocation, updated_rolls=affected_rolls if affected_rolls else None)
    ready_plans = [p for p in email_plans if p["status"] == "ready"]
    skipped_plans = [p for p in email_plans if p["status"] != "ready"]

    kpis([
        ("Total Students", f"{len(email_plans):,}"),
        ("Ready to Send", f"{len(ready_plans):,}"),
        ("Skipped (Missing/Invalid Email)", f"{len(skipped_plans):,}"),
        ("Affected by Re-allocation", f"{len(affected_rolls):,}"),
    ])

    # ---- 5A. PREVIEW ----
    st.markdown("---")
    section("1. Email Preview")
    student_options = {f"{p['roll_no']} — {p['to'] or '(no email)'}": p for p in email_plans}
    selected_plan = None
    if student_options:
        sel_label = st.selectbox("Pick any roll number to preview exact email", list(student_options.keys()), key="notif_prev")
        selected_plan = student_options[sel_label]
        status_html = (
            '<span class="pill pill-ok">Ready</span>'
            if selected_plan["status"] == "ready"
            else f'<span class="pill pill-warn">Skipped: {html.escape(str(selected_plan.get("reason", "")))}</span>'
        )
        st.markdown(
            '<div class="mail">'
            '<div class="mail-head">'
            f'<div class="mail-row"><span class="mail-key">To</span><span class="mail-val">{html.escape(str(selected_plan["to"]))}</span></div>'
            f'<div class="mail-row"><span class="mail-key">Subject</span><span class="mail-val">{html.escape(str(selected_plan["subject"]))}</span></div>'
            f'<div class="mail-row"><span class="mail-key">Status</span><span>{status_html}</span></div>'
            '</div>'
            f'<div class="mail-body">{html.escape(str(selected_plan["body"]))}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ---- 5B. SEND TEST EMAIL ----
    st.markdown("---")
    section("2. Send Test Email")
    tc1, tc2 = st.columns([3, 1])
    test_addr = tc1.text_input("Your test email address", placeholder="you@example.com", key="test_email_input")
    tc2.write("")
    tc2.write("")
    if tc2.button("Send Test Email", use_container_width=True, disabled=not smtp_ready):
        if not EMAIL_RE.match(test_addr.strip()):
            st.error("Enter a valid email address.")
        elif selected_plan is None:
            st.error("No email plan available to sample.")
        else:
            try:
                with open_smtp_connection(smtp_cfg) as srv:
                    send_single_smtp_email(
                        srv, smtp_cfg, test_addr.strip(),
                        f"[TEST] {selected_plan['subject']}", selected_plan["body"],
                    )
                append_email_log([{
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "roll_no": selected_plan["roll_no"],
                    "to": test_addr.strip(),
                    "subject": f"[TEST] {selected_plan['subject']}",
                    "status": "test_sent",
                    "reason": "",
                }])
                st.success(f"Test email sent to {test_addr.strip()}.")
            except Exception as exc:
                st.error(f"Test email failed: {exc}")

    # ---- 5C. DRY RUN (DEFAULT) ----
    st.markdown("---")
    section("3. Dry Run (Default — No Emails Sent)")
    dry_df = pd.DataFrame([
        {
            "roll_no": p["roll_no"],
            "recipient": p["to"],
            "subject": p["subject"],
            "status": "dry_run_ready" if p["status"] == "ready" else "skipped",
            "reason": p.get("reason", ""),
        }
        for p in email_plans
    ])
    table(dry_df)

    # Helper to execute batch sending with progress bar & throttling
    def _run_batch_send(target_plans: list[dict], label: str):
        results = []
        progress = st.progress(0, text=f"{label}: starting...")
        total = max(1, len(target_plans))

        try:
            server = open_smtp_connection(smtp_cfg)
        except Exception as exc:
            st.error(f"Could not connect to SMTP server: {exc}")
            return

        try:
            for idx, plan in enumerate(target_plans, start=1):
                ts = datetime.now().isoformat(timespec="seconds")
                if plan["status"] != "ready":
                    results.append({
                        "timestamp": ts,
                        "roll_no": plan["roll_no"],
                        "to": plan["to"],
                        "subject": plan["subject"],
                        "status": "skipped",
                        "reason": plan.get("reason", "Invalid/missing email"),
                    })
                else:
                    try:
                        send_single_smtp_email(server, smtp_cfg, plan["to"], plan["subject"], plan["body"])
                        results.append({
                            "timestamp": ts,
                            "roll_no": plan["roll_no"],
                            "to": plan["to"],
                            "subject": plan["subject"],
                            "status": "sent",
                            "reason": "",
                        })
                        time.sleep(0.4)  # gentle throttling
                    except Exception as exc:
                        results.append({
                            "timestamp": ts,
                            "roll_no": plan["roll_no"],
                            "to": plan["to"],
                            "subject": plan["subject"],
                            "status": "failed",
                            "reason": str(exc),
                        })
                progress.progress(idx / total, text=f"{label}: {idx}/{len(target_plans)} processed")
        finally:
            try:
                server.quit()
            except Exception:
                pass

        progress.empty()
        append_email_log(results)
        st.session_state["last_send_results"] = results

    # ---- 5D. SEND ALL / RESEND FAILED / EMAIL AFFECTED ONLY ----
    st.markdown("---")
    section("4. Dispatch Emails")

    confirm_send = st.checkbox(
        f"I have reviewed the allocation and want to email {len(ready_plans)} student(s)",
        key="confirm_send_all",
    )

    bc1, bc2, bc3 = st.columns(3)

    if bc1.button(
        f"Send All ({len(ready_plans)})",
        type="primary",
        use_container_width=True,
        disabled=(not confirm_send or not smtp_ready or len(ready_plans) == 0),
    ):
        _run_batch_send(email_plans, "Sending all")

    failed_rolls = {
        r["roll_no"] for r in st.session_state.get("last_send_results", []) if r["status"] == "failed"
    }
    if bc2.button(
        f"Resend Failed ({len(failed_rolls)})",
        use_container_width=True,
        disabled=(not smtp_ready or len(failed_rolls) == 0),
    ):
        retry_plans = [p for p in email_plans if p["roll_no"] in failed_rolls]
        _run_batch_send(retry_plans, "Resending failed")

    affected_plans = [p for p in email_plans if str(p["roll_no"]) in affected_rolls]
    if bc3.button(
        f"Email Affected Students Only ({len(affected_plans)})",
        use_container_width=True,
        disabled=(not smtp_ready or len(affected_plans) == 0),
    ):
        _run_batch_send(affected_plans, "Emailing affected students")

    # ---- 5E. PROGRESS & STATUS TABLE + LOG DOWNLOAD ----
    if st.session_state["last_send_results"]:
        st.markdown("---")
        section("5. Last Dispatch Summary")
        res_df = pd.DataFrame(st.session_state["last_send_results"])
        kpis([
            ("Sent", int((res_df["status"] == "sent").sum())),
            ("Failed", int((res_df["status"] == "failed").sum())),
            ("Skipped", int((res_df["status"] == "skipped").sum())),
        ])
        st.write("")
        table(res_df)
        st.download_button(
            "Download Dispatch Log (CSV)",
            data=res_df.to_csv(index=False),
            file_name="email_dispatch_log.csv",
            mime="text/csv",
        )


# ----- TAB 6: HISTORY -----
with tabs[5]:
    page_header("Notification History", "Persistent audit log of all test, dry-run, and live dispatches.")

    if LOG_PATH.exists() and LOG_PATH.stat().st_size > 0:
        logs = pd.read_csv(LOG_PATH)
        status_col = logs["status"].astype(str)
        kpis([
            ("Sent", int((status_col == "sent").sum())),
            ("Failed", int((status_col == "failed").sum())),
            ("Skipped", int((status_col == "skipped").sum())),
            ("Test Sent", int((status_col == "test_sent").sum())),
        ])
        st.write("")
        sel_status = st.selectbox("Filter by status", ["All Statuses"] + sorted(status_col.unique()))
        view = logs if sel_status == "All Statuses" else logs[status_col == sel_status]
        if "timestamp" in view.columns:
            view = view.sort_values("timestamp", ascending=False)
        table(view)
        st.download_button(
            "Download Full Notification Log (CSV)",
            data=logs.to_csv(index=False),
            file_name="notification_history.csv",
            mime="text/csv",
        )
    else:
        st.info("No notification history recorded yet.")


# =========================================================
# 13. FOOTER
# =========================================================

st.markdown(
    '<div style="text-align:center;padding:28px 0 0 0;color:#5F7068;font-size:12px;">'
    'Exam Seating &amp; Notification Centre &middot; Academic Administration'
    '</div>',
    unsafe_allow_html=True,
)