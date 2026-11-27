# Email notification design

## Goal
Every seated student receives one email listing the room, building, floor,
row, bench and seat for each of their exams.

## Decisions
- One consolidated email per student (5 exams in one message), not 5 emails.
  A student with a blank, malformed or shared email still gets a seat.
  They are skipped by the email step, and the reason is logged.
- Content: name, roll number, then for each exam the date, slot, reporting
  time, subject, room, building, floor, row, bench and seat, plus a reminder
  to bring the ID card.
- Privacy: one email per student, no group emails, no visible CC list, and
  only that student's own data.
- Dry run is the default. Real sending needs --send.
- Fake addresses (@example.com) are never sent to. The sender refuses.
- Testing uses a redirect address, so the emails go to our own inbox.
- After a room change, only affected students get an UPDATED email.
- A log (logs/email_log.csv) records sent, failed, skipped, dry_run and
  test_sent for each student. A rerun never emails a student twice.
- Credentials live in .env only (SMTP_HOST, SMTP_PORT, SMTP_USER,
  SMTP_PASSWORD, FROM_NAME). Never in code, never in Git.

## Limits
- A free Gmail account has a daily sending limit. For a whole college we
  would use the college mail server or a transactional email service.
- The public demo runs without sending (preview and dry run only).

## Flow
allocation -> plan emails -> dry run (review) -> send test to ourselves
-> send -> log -> resend failures only
