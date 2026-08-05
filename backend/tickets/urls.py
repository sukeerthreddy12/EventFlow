from django.urls import path

from .views import TicketCheckInView, MyTicketByRegistrationView

urlpatterns = [
    path("check-in/", TicketCheckInView.as_view(), name="ticket-check-in"),
    path(
        "by-registration/<uuid:registration_id>/",
        MyTicketByRegistrationView.as_view(),
        name="ticket-by-registration",
    ),
]