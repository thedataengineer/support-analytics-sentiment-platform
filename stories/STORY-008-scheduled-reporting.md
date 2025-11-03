# STORY-008 · Scheduled Reporting & Data-Driven PDFs

## Overview
Fulfill the reporting requirements by sourcing PDF exports from live analytics and delivering scheduled emails (daily/weekly) through Celery Beat.

## Acceptance Criteria
- `generate_pdf_report` pulls sentiment/entity data from PostgreSQL rather than mocks.
- Store user report preferences (`schedule_frequency`, `last_sent_at`, `email`) in `user_preferences` table.
- Celery Beat triggers `send_scheduled_reports` task on configured cadence, which generates PDF attachments and emails them via SMTP/SendGrid.
- API endpoint `/api/report/schedule` allows users to configure their schedule (role-restricted).
- Tests cover PDF generation with sample data and scheduler selecting correct recipients.

## Data Model Mockup
```sql
-- db/init.sql
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    schedule_frequency VARCHAR(10) NOT NULL CHECK (schedule_frequency IN ('daily', 'weekly')),
    delivery_time TIME NOT NULL DEFAULT '08:00',
    last_sent_at TIMESTAMPTZ,
    email VARCHAR(255) NOT NULL
);
```

## PDF Generation Mockup
```python
# backend/services/report_summarizer.py
def generate_pdf_report(start_date: date, end_date: date) -> str:
    with get_db_context() as db:
        distribution = (
            db.query(SentimentResult.sentiment, func.count(SentimentResult.id))
            .filter(SentimentResult.created_at.between(start_date, end_date + timedelta(days=1)))
            .group_by(SentimentResult.sentiment)
            .all()
        )
        entities = (
            db.query(Entity.label, Entity.text, func.count(Entity.id))
            .join(SentimentResult, SentimentResult.ticket_id == Entity.ticket_id)
            .filter(SentimentResult.created_at.between(start_date, end_date + timedelta(days=1)))
            .group_by(Entity.label, Entity.text)
            .order_by(func.count(Entity.id).desc())
            .limit(10)
            .all()
        )
    # feed data into existing ReportLab template (replace mock blocks)
```

## Scheduler Mockup
```python
# backend/jobs/report_scheduler.py
from jobs.celery_config import celery_app

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute=0, hour="8"), send_scheduled_reports.s("daily"))
    sender.add_periodic_task(crontab(minute=0, hour="8", day_of_week="mon"), send_scheduled_reports.s("weekly"))

@celery_app.task
def send_scheduled_reports(frequency: str):
    with get_db_context() as db:
        prefs = (
            db.query(UserPreferences)
            .filter(UserPreferences.schedule_frequency == frequency)
            .all()
        )
        for pref in prefs:
            start, end = compute_range(frequency)
            pdf_path = generate_pdf_report(start, end)
            email_service.send_email(
                to=pref.email,
                subject=f"Sentiment Report: {start} – {end}",
                body=render_email_body(pref.user, start, end),
                attachments=[("report.pdf", open(pdf_path, "rb").read())],
            )
            pref.last_sent_at = datetime.utcnow()
        db.commit()
```

## API Mockup
```python
# backend/api/report_api.py
@router.post("/report/schedule", dependencies=[Depends(require_role("analyst", "admin"))])
def update_schedule(payload: ScheduleRequest, user=Depends(current_user), db: Session = Depends(get_db)):
    pref = db.query(UserPreferences).filter(UserPreferences.user_id == user["id"]).one_or_none()
    if pref:
        pref.schedule_frequency = payload.schedule_frequency
        pref.delivery_time = payload.delivery_time
        pref.email = payload.email
    else:
        db.add(UserPreferences(user_id=user["id"], **payload.dict()))
    db.commit()
    return {"status": "ok"}
```

## Email Service Mockup
```python
# backend/services/email_service.py
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

sg = sendgrid.SendGridAPIClient(settings.sendgrid_api_key)

def send_email(to: str, subject: str, body: str, attachments: list[tuple[str, bytes]] | None = None):
    message = Mail(from_email=settings.reports_from_email, to_emails=to, subject=subject, html_content=body)
    for filename, content in attachments or []:
        message.add_attachment(
            Attachment(
                file_content=FileContent(base64.b64encode(content).decode()),
                file_type=FileType("application/pdf"),
                file_name=FileName(filename),
                disposition=Disposition("attachment"),
            )
        )
    sg.send(message)
```

## Testing Notes
- Mock SendGrid client in unit tests to avoid network calls.
- Use Celery’s `celery_app.conf.task_always_eager = True` in tests to synchronously run scheduled tasks.
- Ensure timezone-safe comparisons when computing `daily` vs `weekly` ranges.

