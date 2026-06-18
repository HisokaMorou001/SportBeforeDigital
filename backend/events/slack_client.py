import os
from slack_sdk import WebClient

from .models import SportEvent


def get_client():
    return WebClient(token=os.getenv("SLACK_BOT_TOKEN"))


def build_blocks(event):
    count = event.participants.count()

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{event.title}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Sport:*\n{event.get_sport_type_display()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Location:*\n{event.location}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{event.datetime.strftime('%d/%m/%Y')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{event.datetime.strftime('%H:%M')}"
                },
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"👥 Participants: *{count}*"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {
                        "type": "plain_text",
                        "text": "Join"
                    },
                    "action_id": "join_event",
                    "value": str(event.id)
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"Participants ({count})"
                    },
                    "action_id": "list_participants",
                    "value": str(event.id)
                }
            ]
        }
    ]


def send_event_message(event: SportEvent):
    client = get_client()

    SLACK_DEFAULT_CHANNEL = "C0BAPGC76N6"

    try:
        response = client.chat_postMessage(
            channel=SLACK_DEFAULT_CHANNEL,
            text=f"New event: {event.title}",
            blocks=build_blocks(event)
        )

        event.slack_channel = response["channel"]
        event.slack_ts = response["ts"]
        event.save(update_fields=["slack_channel", "slack_ts"])

        client.chat_postMessage(
            channel=SLACK_DEFAULT_CHANNEL,
            text="*<!channel> A new event has been created! Click to join.*"
        )

    except Exception as e:
        print("Slack chat_postMessage error:", e)


def update_event_message(event: SportEvent):
    if not event.slack_ts:
        return

    client = get_client()

    try:
        client.chat_update(
            channel=event.slack_channel,
            ts=event.slack_ts,
            text=f"New event: {event.title}",
            blocks=build_blocks(event)
        )

        print("Slack message updated.")

    except Exception as e:
        print("Slack update error:", e)


def open_create_event_modal(trigger_id):
    client = get_client()

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "create_event_modal",
            "title": {
                "type": "plain_text",
                "text": "Create Event"
            },
            "submit": {
                "type": "plain_text",
                "text": "Create"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Title"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title"
                    }
                },
                {
                    "type": "input",
                    "block_id": "sport_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Sport"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "sport_type",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Jogging"}, "value": "jogging"},
                            {"text": {"type": "plain_text", "text": "Soccer"}, "value": "soccer"},
                            {"text": {"type": "plain_text", "text": "Basketball"}, "value": "basketball"},
                            {"text": {"type": "plain_text", "text": "Tennis"}, "value": "tennis"},
                            {"text": {"type": "plain_text", "text": "Yoga"}, "value": "yoga"},
                            {"text": {"type": "plain_text", "text": "Gym"}, "value": "gym"},
                            {"text": {"type": "plain_text", "text": "Cycling"}, "value": "bike"},
                            {"text": {"type": "plain_text", "text": "Beach Volleyball"}, "value": "beach_volley"},
                            {"text": {"type": "plain_text", "text": "Hiking"}, "value": "hiking"},
                            {"text": {"type": "plain_text", "text": "Swimming"}, "value": "swimming"},
                            {"text": {"type": "plain_text", "text": "Chess"}, "value": "chess"},
                            {"text": {"type": "plain_text", "text": "Video Games"}, "value": "videogames"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "location_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Location"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "location"
                    }
                },
                {
                    "type": "input",
                    "block_id": "date_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Date"
                    },
                    "element": {
                        "type": "datepicker",
                        "action_id": "date"
                    }
                },
                {
                    "type": "input",
                    "block_id": "time_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Time"
                    },
                    "element": {
                        "type": "timepicker",
                        "action_id": "time"
                    }
                }
            ]
        }
    )