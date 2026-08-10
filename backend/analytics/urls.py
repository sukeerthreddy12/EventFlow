from django.urls import path
from .views import OrganiserAnalyticsSummaryView, EventAnalyticsDetailView

urlpatterns = [
    path("organiser/summary/", OrganiserAnalyticsSummaryView.as_view()),
    path("events/<uuid:pk>/", EventAnalyticsDetailView.as_view()),
]