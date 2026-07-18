from django.urls import path

from .views import TicketCheckInView

urlpatterns = [
    path("check-in/", TicketCheckInView.as_view(), name="ticket-check-in"),
]