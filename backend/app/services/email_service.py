import smtplib
from email.message import EmailMessage

from app.core.config import settings

SUBJECTS = {
    "registration.confirmed": "Registration confirmed",
    "registration.waitlisted": "You joined the waitlist",
    "registration.promoted": "Your registration is now confirmed",
    "registration.cancelled": "Registration cancelled",
    "event.cancelled": "Event cancelled",
}


def send_notification(topic: str, payload: dict[str, object]) -> None:
    message = EmailMessage()
    message["Subject"] = f"{SUBJECTS.get(topic, 'Event update')}: {payload['event_title']}"
    message["From"] = str(settings.smtp_from_email)
    message["To"] = str(payload["email"])
    update = SUBJECTS.get(topic, "There is an event update")
    message.set_content(f"Hello {payload['name']},\n\n{update} for '{payload['event_title']}'.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        server.send_message(message)
