from email.message import EmailMessage
import smtplib

from config import settings


def send_password_reset_email(email: str, token: str) -> None:
    """Envia o email quando SMTP está configurado; nunca retorna o token na API."""
    if not all((settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.PASSWORD_RESET_FROM_EMAIL)):
        return

    message = EmailMessage()
    message["Subject"] = "Redefina sua senha do Cine Random"
    message["From"] = settings.PASSWORD_RESET_FROM_EMAIL
    message["To"] = email
    reset_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={token}"
    message.set_content(
        "Recebemos uma solicitação para redefinir sua senha.\n\n"
        f"Use este link em até 30 minutos: {reset_url}\n\n"
        "Se você não solicitou isso, ignore este email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
