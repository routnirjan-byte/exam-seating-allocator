from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.email_builder import plan_emails
from src.email_sender import notify_students
from src.notification_log import already_sent

BASE = dict(subject_code="ADS101", exam_date="2026-11-14", exam_slot="Morning",
            room_id="R001", building="C", floor=0, row=1, bench=1, seat=1)


def make_alloc():
    return pd.DataFrame([
        {**BASE, "roll_no": 1, "name": "Asha", "email": "asha@students.test"},
        {**BASE, "roll_no": 2, "name": "Ben", "email": ""},
        {**BASE, "roll_no": 3, "name": "Chitra", "email": "chitra-at-students.test"},
        {**BASE, "roll_no": 4, "name": "Dev", "email": "dev@students.test", "seat": 2},
    ])


def test_bad_emails_are_skipped():
    status = {p["roll_no"]: p["status"] for p in plan_emails(make_alloc())}
    assert status == {1: "ready", 2: "skipped", 3: "skipped", 4: "ready"}


def test_body_has_room_and_seat():
    body = plan_emails(make_alloc())[0]["body"]
    assert "R001" in body and "seat 1" in body and "Asha" in body


def test_dry_run_never_connects(tmp_path):
    def boom():
        raise AssertionError("dry run must not connect")
    summary, _ = notify_students(make_alloc(), dry_run=True, smtp_factory=boom,
                                 log_path=tmp_path / "log.csv")
    assert summary["dry_run"] == 2 and summary["skipped"] == 2


def test_real_send_uses_mock_server(tmp_path):
    server = MagicMock()
    summary, _ = notify_students(make_alloc(), dry_run=False, smtp_factory=lambda: server,
                                 delay=0, log_path=tmp_path / "log.csv")
    assert summary["sent"] == 2 and server.send_message.call_count == 2


def test_failures_are_counted(tmp_path):
    server = MagicMock()
    server.send_message.side_effect = Exception("boom")
    summary, _ = notify_students(make_alloc(), dry_run=False, smtp_factory=lambda: server,
                                 delay=0, retries=0, log_path=tmp_path / "log.csv")
    assert summary["failed"] == 2


def test_rerun_does_not_email_twice(tmp_path):
    server = MagicMock()
    log = tmp_path / "log.csv"
    notify_students(make_alloc(), dry_run=False, smtp_factory=lambda: server, delay=0, log_path=log)
    notify_students(make_alloc(), dry_run=False, smtp_factory=lambda: server, delay=0, log_path=log)
    assert server.send_message.call_count == 2


def test_example_com_is_refused_for_real_sending(tmp_path):
    fake = make_alloc()
    fake["email"] = [f"s{i}@example.com" for i in range(4)]
    with pytest.raises(ValueError):
        notify_students(fake, dry_run=False, smtp_factory=lambda: MagicMock(),
                        delay=0, log_path=tmp_path / "log.csv")


def test_redirect_goes_to_our_address_and_is_not_logged_as_sent(tmp_path):
    server = MagicMock()
    log = tmp_path / "log.csv"
    summary, _ = notify_students(make_alloc(), dry_run=False, smtp_factory=lambda: server,
                                 delay=0, redirect_to="me@gmail.com", limit=1, log_path=log)
    assert summary["test_sent"] == 1 and summary["sent"] == 0
    assert server.send_message.call_args[0][0]["To"] == "me@gmail.com"
    assert already_sent(log) == set()          # test sends must not count as "sent"


def test_limit_caps_the_number_of_emails(tmp_path):
    summary, _ = notify_students(make_alloc(), dry_run=True, limit=2, log_path=tmp_path / "log.csv")
    assert summary["dry_run"] + summary["skipped"] == 2