from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from app.src.services.auth import auth_service
from app.src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Send confirmetion email to the user

    Args:
        email (EmailStr): Email address to send message.
        username (str): Username of the recipient.
        host (str): Hostname of the recipient.
    """    
    try:
        token_verification = await auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_email(email: EmailStr, password: str, username: str, host: str):
    """
    Send email for password reset

    Args:
        email (EmailStr): Email address to send message.
        password (str): New password.
        username (str): Username of the recipient.
        host (str): Hostname of the recipient.
    """    
    try:
        token_verification = await auth_service.create_email_token({"sub": email, "pass": password}, expires_delta=60)
        message = MessageSchema(
            subject="Reset password",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_password_reset_template.html")
    except ConnectionErrors as err:
        print(err)
