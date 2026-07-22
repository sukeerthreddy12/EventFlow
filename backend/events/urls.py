from django.urls import path

from .views import EventDetailView, EventListCreateView, EventPublishView, EventUnpublishView, EventCancelView, EventAdminOverrideView

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path("<uuid:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("<uuid:pk>/publish/", EventPublishView.as_view(), name="event-publish"),
    path("<uuid:pk>/unpublish/", EventUnpublishView.as_view(), name="event-unpublish"),
    path("<uuid:pk>/cancel/", EventCancelView.as_view(), name="event-cancel"),
    path("<uuid:pk>/admin-override/", EventAdminOverrideView.as_view(), name="event-admin-override"),
]