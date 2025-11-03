from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable, Tuple

from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Simple SMTP-backed email sender for scheduled reports.
    Falls back to logging when SMTP is not configured.
    """

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.from_email = settings.reports_from_email

        self.enabled = bool(self.host and self.port and self.from_email)
        if not self.enabled:
            logger.warning("EmailService disabled: SMTP host/port or from-email not configured")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachments: Iterable[Tuple[str, bytes]] | None = None,
    ) -> bool:
        """
        Send an email. Returns True if the message was dispatched.
        """
        if not self.enabled:
            logger.info(
                "Skipping email to %s because EmailService is disabled. Subject: %s",
                to_email,
                subject,
            )
            return False

        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content("This email contains an HTML version of the report.")
        message.add_alternative(html_body, subtype="html")

        for filename, content in attachments or []:
            message.add_attachment(content, maintype="application", subtype="pdf", filename=filename)

        try:
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.host, self.port) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(message)

            logger.info("Sent scheduled report email to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc, exc_info=True)
            return False


email_service = EmailService()
