# registrations/urls.py
from django.urls import path
from .views import RegistrationListCreateView, RegistrationCancelView


urlpatterns = [
    path("", RegistrationListCreateView.as_view(), name="registration-list-create"),
    path("<uuid:pk>/cancel/",RegistrationCancelView.as_view(),name="registration-cancel",)
]