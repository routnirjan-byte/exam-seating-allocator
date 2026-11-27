import html
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.email_builder import plan_emails

# ---- one-time theme bootstrap (replaces the separate config.toml step) ----
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
# 1. PAGE CONFIG (sidebar disabled)
# =========================================================

st.set_page_config(
    page_title="Exam Notification Centre",
    layout="wide",
    initial_sidebar_state="collapsed",
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

    /* remove sidebar, header, footer chrome */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    #MainMenu, footer { display: none !important; visibility: hidden; }

    .block-container { max-width: 1280px; padding-top: 1.5rem; padding-bottom: 3rem; }

    h1, h2, h3, h4 { color: #F0F5F2; letter-spacing: -0.01em; }
    hr { border-color: #1F2B26; margin: 1.6rem 0; }

    /* top bar */
    .topbar { display:flex; align-items:center; justify-content:space-between;
              padding: 6px 0 18px 0; border-bottom: 1px solid #1F2B26; margin-bottom: 18px; }
    .brand { display:flex; align-items:center; gap:12px; }
    .logo { width:36px; height:36px; border-radius:10px; background:#34D399; color:#06281C;
            display:flex; align-items:center; justify-content:center; font-weight:700; }
    .brand-title { color:#F0F5F2; font-size:17px; font-weight:600; line-height:1.2; }
    .brand-sub { color:#7F9188; font-size:12px; }
    .badge { font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
             color:#34D399; background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.3);
             padding:4px 10px; border-radius:999px; }

    /* page heading */
    .page-title { color:#F0F5F2; font-size:26px; font-weight:700; margin:18px 0 2px 0; }
    .page-sub { color:#8FA197; font-size:14px; margin-bottom:18px; }
    .section-title { color:#F0F5F2; font-size:16px; font-weight:600; margin: 4px 0 10px 0; }

    /* KPI cards */
    .kpi { background:#131C18; border:1px solid #22302A; border-radius:14px; padding:18px 20px; }
    .kpi-label { color:#8FA197; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; }
    .kpi-value { color:#F0F5F2; font-size:30px; font-weight:700; margin-top:6px; }

    /* email preview */
    .mail { background:#131C18; border:1px solid #22302A; border-radius:14px; overflow:hidden; }
    .mail-head { padding:16px 20px; border-bottom:1px solid #22302A; }
    .mail-row { display:flex; gap:12px; font-size:14px; padding:3px 0; }
    .mail-key { color:#7F9188; width:64px; flex-shrink:0; }
    .mail-val { color:#E6EFEA; }
    .mail-body { padding:20px; color:#D6E2DB; font-size:14px; line-height:1.65; white-space:pre-wrap; }

    .pill { display:inline-block; font-size:12px; font-weight:600; padding:4px 12px; border-radius:999px; }
    .pill-ok { color:#34D399; background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.3); }
    .pill-warn { color:#FBBF24; background:rgba(251,191,36,.1); border:1px solid rgba(251,191,36,.3); }

    /* dark widget fallback */
    .stApp, .stApp p, .stApp label { color: #E6EFEA; }
    [data-testid="stWidgetLabel"] p { color: #AEBDB5; }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div, input {
        background:#131C18 !important; color:#E6EFEA !important; border-color:#22302A !important; }
    [data-baseweb="popover"] ul { background:#131C18 !important; }
    [data-baseweb="popover"] li { color:#E6EFEA !important; }

    /* widgets */
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
# 3. DATA
# =========================================================

ALLOCATION_PATH = Path("data/processed/allocation.csv")
LOG_PATH = Path("logs/email_log.csv")
ABSENTEE_PATH = Path("data/processed/absentee_predictions.csv")

if not ALLOCATION_PATH.exists():
    st.error("Allocation file not found.")
    st.stop()


@st.cache_data
def load_allocation(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data
def build_plans(df: pd.DataFrame):
    return plan_emails(df)


allocation = load_allocation(str(ALLOCATION_PATH))
email_plans = build_plans(allocation)

total_students = allocation["roll_no"].nunique()
total_records = len(allocation)
total_subjects = allocation["subject_code"].nunique()
total_dates = allocation["exam_date"].nunique()
total_rooms = allocation["room_id"].nunique()


# =========================================================
# 4. UI HELPERS
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


def bar(series: pd.Series, height: int = 280):
    df = series.reset_index()
    df.columns = ["label", "value"]
    df["label"] = df["label"].astype(str)
    chart = (
        alt.Chart(df)
        .mark_bar(color=ACCENT, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("label:N", sort=None, title=None, axis=alt.Axis(labelAngle=-40)),
            y=alt.Y("value:Q", title=None),
            tooltip=["label", "value"],
        )
        .properties(height=height)
        .configure(background="transparent")
        .configure_axis(labelColor="#8FA197", gridColor="#1A2520", domain=False, tickColor="#1A2520")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart)


def table(df: pd.DataFrame):
    st.dataframe(df, hide_index=True)


# =========================================================
# 5. TOP BAR + NAVIGATION
# =========================================================

st.markdown(
    '<div class="topbar">'
    '<div class="brand"><div class="logo">EN</div>'
    '<div><div class="brand-title">Exam Notification Centre</div>'
    '<div class="brand-sub">Seating allocation &amp; notification management</div></div></div>'
    '<span class="badge">Demo &middot; Synthetic data</span>'
    '</div>',
    unsafe_allow_html=True,
)

if THEME_CREATED:
    st.info("Theme file created. Restart the app once (Ctrl+C, then streamlit run notify.py) to apply it.")

PAGES = [
    "Dashboard",
    "Seat Allocation",
    "Room Management",
    "Absentee Analytics",
    "Notifications",
    "History",
]

if hasattr(st, "segmented_control"):
    page = st.segmented_control(
        "Navigation", PAGES, default=PAGES[0],
        label_visibility="collapsed", key="nav",
    ) or PAGES[0]
else:
    page = st.radio("Navigation", PAGES, horizontal=True, label_visibility="collapsed", key="nav")


# =========================================================
# 6. DASHBOARD
# =========================================================

if page == "Dashboard":

    page_header("Dashboard", "Overview of the examination allocation system.")

    kpis([
        ("Students", f"{total_students:,}"),
        ("Allocation records", f"{total_records:,}"),
        ("Subjects", f"{total_subjects:,}"),
        ("Exam dates", f"{total_dates:,}"),
        ("Rooms", f"{total_rooms:,}"),
    ])

    st.write("")
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            section("Students by subject")
            bar(allocation.groupby("subject_code")["roll_no"].nunique().sort_values(ascending=False))

    with c2:
        with st.container(border=True):
            section("Students by exam date")
            bar(allocation.groupby("exam_date")["roll_no"].nunique())

    st.write("")
    section("Room distribution")
    room_summary = (
        allocation.groupby(["room_id", "building", "floor"])
        .agg(students=("roll_no", "nunique"),
             allocation_records=("roll_no", "count"),
             subjects=("subject_code", "nunique"))
        .reset_index()
        .sort_values("students", ascending=False)
    )
    table(room_summary)

    st.write("")
    section("Recent allocation records")
    table(allocation[["roll_no", "name", "subject_code", "exam_date",
                      "exam_slot", "room_id", "seat"]].head(10))


# =========================================================
# 7. SEAT ALLOCATION
# =========================================================

elif page == "Seat Allocation":

    page_header("Seat Allocation", "Search, filter and inspect seating assignments.")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)

        subjects = sorted(allocation["subject_code"].astype(str).unique())
        selected_subject = c1.selectbox("Subject", ["All Subjects"] + subjects)

        filtered = allocation.copy()
        if selected_subject != "All Subjects":
            filtered = filtered[filtered["subject_code"].astype(str) == selected_subject]

        dates = sorted(filtered["exam_date"].astype(str).unique())
        selected_date = c2.selectbox("Exam date", ["All Dates"] + dates)
        if selected_date != "All Dates":
            filtered = filtered[filtered["exam_date"].astype(str) == selected_date]

        rooms = sorted(filtered["room_id"].astype(str).unique())
        selected_room = c3.selectbox("Room", ["All Rooms"] + rooms)
        if selected_room != "All Rooms":
            filtered = filtered[filtered["room_id"].astype(str) == selected_room]

        search = st.text_input("Search student", placeholder="Name or roll number...")
        if search:
            filtered = filtered[
                filtered["name"].astype(str).str.contains(search, case=False, na=False)
                | filtered["roll_no"].astype(str).str.contains(search, case=False, na=False)
            ]

    st.write("")
    kpis([
        ("Students in view", f"{filtered['roll_no'].nunique():,}"),
        ("Records in view", f"{len(filtered):,}"),
    ])

    st.write("")
    display_columns = ["roll_no", "name", "email", "subject_code", "exam_date",
                       "exam_slot", "room_id", "building", "floor", "row", "bench", "seat"]
    table(filtered[display_columns])

    st.download_button(
        "Download filtered allocation",
        data=filtered[display_columns].to_csv(index=False),
        file_name="filtered_allocation.csv",
        mime="text/csv",
    )


# =========================================================
# 8. ROOM MANAGEMENT
# =========================================================

elif page == "Room Management":

    page_header("Room Management", "Room distribution and allocation statistics.")

    room_summary = (
        allocation.groupby(["room_id", "building", "floor"])
        .agg(students=("roll_no", "nunique"),
             allocation_records=("roll_no", "count"),
             subjects=("subject_code", "nunique"),
             exam_dates=("exam_date", "nunique"))
        .reset_index()
        .sort_values("room_id")
    )

    kpis([
        ("Rooms used", f"{room_summary['room_id'].nunique():,}"),
        ("Allocation records", f"{room_summary['allocation_records'].sum():,}"),
        ("Buildings", f"{room_summary['building'].nunique():,}"),
    ])

    st.write("")
    with st.container(border=True):
        section("Students per room")
        bar(room_summary.set_index("room_id")["students"])

    st.write("")
    section("Room details")
    table(room_summary)

    st.write("")
    section("Inspect a room")
    selected_room = st.selectbox(
        "Select room",
        sorted(allocation["room_id"].astype(str).unique()),
        key="room_inspect",
    )
    room_students = allocation[allocation["room_id"].astype(str) == selected_room]
    st.caption(f"{room_students['roll_no'].nunique()} students in {selected_room}")
    table(room_students[["roll_no", "name", "subject_code", "exam_date",
                         "exam_slot", "row", "bench", "seat"]])


# =========================================================
# 9. ABSENTEE ANALYTICS
# =========================================================

elif page == "Absentee Analytics":

    page_header("Absentee Analytics", "Advisory output from the absentee prediction model.")

    if ABSENTEE_PATH.exists():
        absentee_data = pd.read_csv(ABSENTEE_PATH)

        kpis([("Rows", f"{len(absentee_data):,}"),
              ("Columns", f"{len(absentee_data.columns):,}")])
        st.write("")

        if "p_absent" in absentee_data.columns:
            with st.container(border=True):
                section("Absence probability distribution")
                bins = pd.cut(absentee_data["p_absent"], bins=10, include_lowest=True)
                counts = bins.value_counts().sort_index()
                counts.index = counts.index.astype(str)
                bar(counts)
                st.caption("Advisory only. These probabilities must not be used to deny or change seating.")

        elif "predicted_absent" in absentee_data.columns:
            with st.container(border=True):
                section("Predicted absence categories")
                bar(absentee_data["predicted_absent"].value_counts())

        st.write("")
        section("Prediction data")
        table(absentee_data.head(20))
        st.caption("Columns: " + ", ".join(absentee_data.columns))

    else:
        st.info("Absentee prediction data is not available yet. Generate the prediction file from the model first.")


# =========================================================
# 10. NOTIFICATIONS
# =========================================================

elif page == "Notifications":

    page_header("Notifications", "Preview consolidated examination notification plans.")

    ready_count = sum(1 for p in email_plans if p["status"] == "ready")
    skipped_count = sum(1 for p in email_plans if p["status"] == "skipped")

    kpis([("Ready for preview", f"{ready_count:,}"), ("Skipped", f"{skipped_count:,}")])
    st.write("")

    student_options = {f"{p['roll_no']} - {p['to']}": p for p in email_plans}

    if student_options:
        selected = st.selectbox("Select student", list(student_options.keys()), key="notification_preview")
        plan = student_options[selected]

        if plan["status"] == "ready":
            status_html = '<span class="pill pill-ok">Ready</span>'
        else:
            status_html = f'<span class="pill pill-warn">Skipped: {html.escape(str(plan["reason"]))}</span>'

        st.write("")
        st.markdown(
            '<div class="mail">'
            '<div class="mail-head">'
            f'<div class="mail-row"><span class="mail-key">To</span><span class="mail-val">{html.escape(str(plan["to"]))}</span></div>'
            f'<div class="mail-row"><span class="mail-key">Subject</span><span class="mail-val">{html.escape(str(plan["subject"]))}</span></div>'
            f'<div class="mail-row"><span class="mail-key">Status</span><span>{status_html}</span></div>'
            '</div>'
            f'<div class="mail-body">{html.escape(str(plan["body"]))}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No notification plans available.")

    st.caption("This page previews notification plans. It does not send emails.")


# =========================================================
# 11. HISTORY
# =========================================================

elif page == "History":

    page_header("Notification History", "Records of notification testing and processing.")

    if LOG_PATH.exists():
        logs = pd.read_csv(LOG_PATH)

        if not logs.empty:
            status = logs["status"].astype(str)
            kpis([
                ("Sent", int((status == "sent").sum())),
                ("Failed", int((status == "failed").sum())),
                ("Dry runs", int((status == "dry_run").sum())),
                ("Skipped", int((status == "skipped").sum())),
                ("Test sent", int((status == "test_sent").sum())),
            ])
            st.write("")

            selected_status = st.selectbox(
                "Filter by status", ["All Statuses"] + sorted(status.unique())
            )
            history = logs if selected_status == "All Statuses" else logs[status == selected_status]
            history = history.sort_values("timestamp", ascending=False)

            table(history)

            st.download_button(
                "Download notification history",
                data=logs.to_csv(index=False),
                file_name="notification_history.csv",
                mime="text/csv",
            )
        else:
            st.info("The notification log is currently empty.")
    else:
        st.info("No notification history available yet.")


# =========================================================
# 12. FOOTER
# =========================================================

st.markdown(
    '<div style="text-align:center;padding:28px 0 0 0;color:#5F7068;font-size:12px;">'
    'Exam Notification Centre &middot; Academic Administration &middot; Demo environment'
    '</div>',
    unsafe_allow_html=True,
)
