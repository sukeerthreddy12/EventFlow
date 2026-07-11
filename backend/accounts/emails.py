#connected with tokens.py for email verification and reset passowrd  
from django.conf import settings
from django.core.mail import send_mail

from .models import User
from .tokens import create_verification_token, create_password_reset_token


def send_verification_email(user: User) -> None:
    token = create_verification_token(user.pk)
    verify_url = f"{settings.FRONTEND_VERIFY_URL}?token={token}"

    send_mail(
        subject="Verify your email address",
        message=(
            f"Hi {user.username},\n\n"
            f"Please verify your email by visiting:\n{verify_url}\n\n"
            f"Your verification token (copy this):\n{token}\n\n"
            f"This link expires in {settings.EMAIL_VERIFICATION_TTL // 60} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
def send_password_reset_email(user: User) -> None:
    token = create_password_reset_token(user.pk)
    reset_url = f"{settings.FRONTEND_PASSWORD_RESET_URL}?token={token}"
    send_mail(
        subject="Reset your password",
        message=(
            f"Hi {user.username},\n\n"
            f"Your password reset token (copy this):\n{token}\n\n"
            f"Or visit:\n{reset_url}\n\n"
            f"Your verification token (copy this):\n{token}\n\n"
            f"This link expires in {settings.PASSWORD_RESET_TTL // 60} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )