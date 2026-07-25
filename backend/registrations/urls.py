# registrations/urls.py
from django.urls import path
from .views import RegistrationListCreateView, RegistrationCancelView, TeamRegistrationCreateView


urlpatterns = [
    path("", RegistrationListCreateView.as_view(), name="registration-list-create"),
    path("<uuid:pk>/cancel/",RegistrationCancelView.as_view(),name="registration-cancel",),
    path("team/", TeamRegistrationCreateView.as_view(), name="team-registration-create"),
]