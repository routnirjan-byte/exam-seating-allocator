import os
import smtplib
import ssl
import time

import pandas as pd
from dotenv import load_dotenv

from src.email_builder import build_message, plan_emails
from src.notification_log import LOG, already_sent, log_result


def _connect():
    host, user = os.getenv("SMTP_HOST"), os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    if not (host and user and password):
        raise RuntimeError("Set SMTP_HOST, SMTP_USER and SMTP_PASSWORD in .env first")
    server = smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT", "465")),
                              context=ssl.create_default_context())
    server.login(user, password)
    return server


def notify_students(allocation_df, dry_run=True, updated_rolls=None, delay=1.0,
                    retries=2, log_path=LOG, smtp_factory=None,
                    redirect_to=None, limit=None):
    """Build and (unless dry_run) send one email per student. Returns (summary, plans).
    redirect_to: send every email to this address instead (safe testing).
    limit: only handle the first N students."""
    load_dotenv()
    plans = plan_emails(allocation_df, updated_rolls)
    if limit is not None:
        plans = plans[:limit]
    testing = redirect_to is not None

    if not dry_run and not testing:
        fake = [p["roll_no"] for p in plans
                if p["status"] == "ready" and p["to"].lower().endswith("@example.com")]
        if fake:
            raise ValueError(f"Refusing to send real email to {len(fake)} @example.com "
                             "addresses. Use redirect_to for testing.")

    done = set() if (dry_run or testing or updated_rolls is not None) else already_sent(log_path)
    ok = "test_sent" if testing else "sent"
    summary = {"sent": 0, "test_sent": 0, "failed": 0, "skipped": 0, "dry_run": 0}
    from_addr = f"{os.getenv('FROM_NAME', 'Exam Cell')} <{os.getenv('SMTP_USER', '')}>"

    server = None if dry_run else (smtp_factory or _connect)()
    try:
        for p in plans:
            key = str(p["roll_no"])
            if p["status"] == "skipped":
                log_result(key, p["to"], "skipped", p["reason"], log_path)
                summary["skipped"] += 1
            elif dry_run:
                log_result(key, p["to"], "dry_run", "", log_path)
                summary["dry_run"] += 1
            elif key in done:
                summary["skipped"] += 1             # already emailed in an earlier run
            else:
                if testing:
                    p = {**p, "to": redirect_to, "subject": "[TEST] " + p["subject"]}
                msg = build_message(p, from_addr)
                for attempt in range(retries + 1):
                    try:
                        server.send_message(msg)
                        log_result(key, p["to"], ok, "", log_path)
                        summary[ok] += 1
                        break
                    except Exception as exc:
                        if attempt == retries:
                            log_result(key, p["to"], "failed", str(exc)[:200], log_path)
                            summary["failed"] += 1
                        else:
                            time.sleep(delay * (attempt + 1))
                time.sleep(delay)
    finally:
        if server is not None:
            server.quit()
    return summary, plans


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="really send (default is a dry run)")
    ap.add_argument("--redirect-to", help="send every email to this address instead (testing)")
    ap.add_argument("--limit", type=int, help="only the first N students")
    args = ap.parse_args()

    allocation = pd.read_csv("data/processed/allocation.csv")
    summary, _ = notify_students(allocation, dry_run=not args.send,
                                 redirect_to=args.redirect_to, limit=args.limit)
    print(summary)