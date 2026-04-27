import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings


logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "yuvrajaryal83@gmail.com"


def send_rsvp_email(recipient_email: str, recipient_name: str, event_name: str, event_details: str) -> None:
    if not settings.app_password:
        logger.warning("SMTP app password is not configured; skipping RSVP confirmation email")
        return

    message = EmailMessage()
    message["Subject"] = f"RSVP confirmed: {event_name}"
    message["From"] = SMTP_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"Hello {recipient_name},\n\n"
        f"Your RSVP for '{event_name}' has been confirmed.\n\n"
        f"Event details:\n{event_details}\n\n"
        f"Thanks for registering."
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, settings.app_password)
            server.send_message(message)
            print("RSVP confirmation email sent successfully!")
    except Exception:
        logger.exception("Failed to send RSVP confirmation email")