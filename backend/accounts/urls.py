from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    VerifyEmailView,
)

TaggedTokenRefreshView = extend_schema(
    tags=["Accounts"],
    summary="Refresh JWT access token",
)(TokenRefreshView)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TaggedTokenRefreshView.as_view(), name="token-refresh"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("me/", MeView.as_view(), name="me"),
]
