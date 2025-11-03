from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Iterable, Tuple

from celery import shared_task
from celery.schedules import crontab

from config import settings
from database import SessionLocal
from models import User, UserReportPreference
from services.report_summarizer import generate_pdf_report
from services.email_service import email_service
from jobs.celery_config import celery_app

logger = logging.getLogger(__name__)


def _should_send(preference: UserReportPreference, now: datetime) -> bool:
    """
    Determine if a report should be delivered for this preference at the given moment.
    """
    if preference.delivery_time and preference.delivery_time.hour != now.hour:
        return False

    if not preference.last_sent_at:
        return True

    last_sent = preference.last_sent_at
    if preference.schedule_frequency == "daily":
        return last_sent.date() < now.date()
    if preference.schedule_frequency == "weekly":
        last_iso = last_sent.isocalendar()
        current_iso = now.isocalendar()
        return (last_iso[0], last_iso[1]) < (current_iso[0], current_iso[1])

    return True


def _compute_range(frequency: str, now: datetime) -> Tuple[str, str]:
    """
    Return start/end date strings (YYYY-MM-DD) for the given frequency.
    """
    if frequency == "weekly":
        end = (now - timedelta(days=1)).date()
        start = (now - timedelta(days=7)).date()
    else:  # daily
        end = (now - timedelta(days=1)).date()
        start = end

    return start.isoformat(), end.isoformat()


def _render_email_body(user: User, start_date: str, end_date: str) -> str:
    return (
        f"<p>Hello {user.email},</p>"
        f"<p>Your scheduled sentiment analysis report for <strong>{start_date}</strong> to "
        f"<strong>{end_date}</strong> is attached.</p>"
        "<p>Regards,<br>Sentiment Platform</p>"
    )


@shared_task(name="backend.jobs.reporting_tasks.send_scheduled_reports")
def send_scheduled_reports(frequency: str) -> int:
    """
    Celery task that generates and emails scheduled reports.
    Returns the number of successfully dispatched emails.
    """
    session = SessionLocal()
    now = datetime.now(timezone.utc)
    delivered = 0

    try:
        preferences = (
            session.query(UserReportPreference)
            .filter(UserReportPreference.schedule_frequency == frequency)
            .all()
        )

        for preference in preferences:
            if not _should_send(preference, now):
                continue

            user = session.query(User).filter(User.id == preference.user_id).one_or_none()
            if not user:
                logger.warning("Skipping report for missing user_id=%s", preference.user_id)
                continue

            start_date, end_date = _compute_range(frequency, now)
            try:
                pdf_path = generate_pdf_report(start_date, end_date)
                with open(pdf_path, "rb") as pdf_file:
                    attachments = [(f"sentiment_report_{start_date}_to_{end_date}.pdf", pdf_file.read())]

                subject = f"Sentiment Report: {start_date} – {end_date}"
                body = _render_email_body(user, start_date, end_date)
                if email_service.send_email(preference.email, subject, body, attachments):
                    preference.last_sent_at = now
                    delivered += 1
                else:
                    logger.warning("Email not sent for user_id=%s", preference.user_id)
            except Exception as exc:
                logger.error("Failed to generate or send report for user_id=%s: %s", preference.user_id, exc, exc_info=True)
            finally:
                try:
                    if pdf_path and os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except Exception:
                    logger.debug("Failed to remove temporary PDF %s", pdf_path)

        session.commit()
        return delivered
    except Exception as exc:
        session.rollback()
        logger.error("Scheduled report task failed: %s", exc, exc_info=True)
        return delivered
    finally:
        session.close()


# Register beat schedules
celery_app.conf.beat_schedule = celery_app.conf.get("beat_schedule", {}) or {}
celery_app.conf.beat_schedule.update(
    {
        "send-daily-reports": {
            "task": "backend.jobs.reporting_tasks.send_scheduled_reports",
            "schedule": crontab(
                minute=settings.reports_daily_minute,
                hour=settings.reports_daily_hour,
            ),
            "args": ("daily",),
        },
        "send-weekly-reports": {
            "task": "backend.jobs.reporting_tasks.send_scheduled_reports",
            "schedule": crontab(
                minute=settings.reports_weekly_minute,
                hour=settings.reports_weekly_hour,
                day_of_week=settings.reports_weekly_day_of_week,
            ),
            "args": ("weekly",),
        },
    }
)
