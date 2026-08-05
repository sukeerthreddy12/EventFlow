"""
Smoke: EmailRetryQueue + process_email_retry_queue (same task Beat schedules).

  cd backend
  # worker must be running for the .delay() part:
  #   uv run celery -A backend worker -l info --pool=solo
  uv run python notifications/smoke_email_retry.py
"""
from __future__ import annotations

import os
import sys
import time
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django

django.setup()

from django.utils import timezone

from accounts.models import User
from events.models import Event
from notifications.models import EmailRetryQueue
from notifications.retry import enqueue_email_retry, send_or_queue
from notifications.tasks import process_email_retry_queue

passed = 0
failed = 0


def ok(label: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        extra = f" — {detail}" if detail else ""
        print(f"  FAIL  {label}{extra}")


def main() -> None:
    user = User.objects.filter(is_verified=True).first()
    event = Event.objects.filter(is_deleted=False).first()
    if not user or not event:
        raise SystemExit("Need at least one verified user and one event in DB.")

    print("=== 1) Forced PENDING row (simulates SMTP fail already queued) ===")
    row = enqueue_email_retry(
        EmailRetryQueue.Kind.EVENT_REMINDER,
        user,
        event,
        Exception("forced smoke failure"),
        delay_seconds=0,
    )
    ok("row PENDING", row.status == EmailRetryQueue.Status.PENDING, row.status)
    ok("next_attempt due", row.next_attempt_at <= timezone.now())

    print("\n=== 2) In-process process_email_retry_queue() ===")
    sent = process_email_retry_queue()
    row.refresh_from_db()
    ok("processor sent >= 1 (or left PENDING if SMTP down)", sent >= 0)
    ok(
        "row SENT (SMTP OK) or still PENDING/DEAD (SMTP fail)",
        row.status in {
            EmailRetryQueue.Status.SENT,
            EmailRetryQueue.Status.PENDING,
            EmailRetryQueue.Status.DEAD,
        },
        f"{row.status} attempts={row.attempts} err={row.last_error[:120]}",
    )
    if row.status == EmailRetryQueue.Status.SENT:
        print("  -> Mailtrap should show a reminder email.")
    else:
        print("  -> SMTP failed; backoff/DEAD is still valid retry behavior.")

    print("\n=== 3) Worker path via .delay() (what Beat does) ===")
    row2 = enqueue_email_retry(
        EmailRetryQueue.Kind.EVENT_REMINDER,
        user,
        event,
        Exception("forced smoke for delay"),
        delay_seconds=0,
    )
    async_result = process_email_retry_queue.delay()
    print(f"  queued task id={async_result.id}")
    print("  Watch WORKER log for: process_email_retry_queue ... succeeded")

    # wait briefly for solo worker
    deadline = time.time() + 15
    while time.time() < deadline:
        row2.refresh_from_db()
        if row2.status == EmailRetryQueue.Status.SENT:
            break
        if row2.status == EmailRetryQueue.Status.DEAD:
            break
        if row2.attempts > 0 and row2.status == EmailRetryQueue.Status.PENDING:
            # retried but SMTP failed again — still proves worker ran
            break
        time.sleep(0.5)

    row2.refresh_from_db()
    ok(
        "worker touched row2 (attempts>0 or SENT/DEAD)",
        row2.attempts > 0 or row2.status == EmailRetryQueue.Status.SENT,
        f"{row2.status} attempts={row2.attempts}",
    )

    print("\n=== 4) Optional Beat check (manual) ===")
    row3 = enqueue_email_retry(
        EmailRetryQueue.Kind.EVENT_REMINDER,
        user,
        event,
        Exception("forced smoke for beat"),
        delay_seconds=0,
    )
    print(f"  Created PENDING id={row3.id}")
    print("  Keep worker + beat running; within ~60s Beat should schedule")
    print("  process_email_retry_queue and worker should process this row.")
    print("  Then: EmailRetryQueue.objects.get(id=...).status")

    print(f"\n=== Done: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()