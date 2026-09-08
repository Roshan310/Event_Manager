import smtplib
from email.message import EmailMessage

from app.core.config import settings

SUBJECTS = {
    "registration.confirmed": "Registration confirmed",
    "registration.waitlisted": "You joined the waitlist",
    "registration.promoted": "Your registration is now confirmed",
    "registration.cancelled": "Registration cancelled",
    "event.cancelled": "Event cancelled",
    "event.updated": "Event schedule or location updated",
    "event.reminder": "Your event starts tomorrow",
}


def send_notification(topic: str, payload: dict[str, object]) -> None:
    message = EmailMessage()
    title = str(payload.get("event_title", "Your account")).replace("\r", " ").replace("\n", " ")
    message["Subject"] = f"{SUBJECTS.get(topic, 'Account action')}: {title}"
    message["From"] = str(settings.smtp_from_email)
    message["To"] = str(payload["email"])
    update = SUBJECTS.get(topic, "There is an event update")
    if topic.startswith("account."):
        action = "reset your password" if topic == "account.reset" else "verify your email"
        body = (
            f"Use this single-use token to {action}:\n\n{payload['token']}\n\n"
            "If you did not request this, ignore this email."
        )
    else:
        body = (
            f"{update} for '{title}'.\nStart: {payload.get('starts_at', '')}\n"
            f"End: {payload.get('ends_at', '')}\nLocation: {payload.get('location', '')}\n"
            f"Timezone: {payload.get('timezone', '')}"
        )
    message.set_content(f"Hello {payload['name']},\n\n{body}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        server.send_message(message)
