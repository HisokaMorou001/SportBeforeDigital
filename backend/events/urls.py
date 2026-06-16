from django.urls import path
from .api import (
    create_event,
    list_events,
    slack_events,
    slack_create_event,
    slack_interaction
)

urlpatterns = [
    # REST API
    path("create/", create_event),
    path("", list_events),

    # SLACK
    path("slack/events/", slack_events),
    path("slack/create-event/", slack_create_event),
    path("slack/interactions/", slack_interaction),

]