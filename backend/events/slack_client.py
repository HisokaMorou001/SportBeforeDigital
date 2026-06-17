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
                    "text": f"*Luogo:*\n{event.location}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Data:*\n{event.datetime.strftime('%d/%m/%Y')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Ora:*\n{event.datetime.strftime('%H:%M')}"
                },
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"👥 Partecipanti: *{count}*"
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
                        "text": "Partecipa"
                    },
                    "action_id": "join_event",
                    "value": str(event.id)
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"Partecipanti ({count})"
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
            text=f"Nuovo evento: {event.title}",
            blocks=build_blocks(event)
        )

        event.slack_channel = response["channel"]
        event.slack_ts = response["ts"]
        event.save(update_fields=["slack_channel", "slack_ts"])

        client.chat_postMessage(
            channel=SLACK_DEFAULT_CHANNEL,
            text="<!channel> Nuovo evento creato! Clicca per partecipare"
        )

    except Exception as e:
        print("Errore Slack chat_postMessage:", e)

def update_event_message(event: SportEvent):
    if not event.slack_ts:
        return

    client = get_client()

    try:
        client.chat_update(
            channel=event.slack_channel,
            ts=event.slack_ts,
            text=f"Nuovo evento: {event.title}",
            blocks=build_blocks(event)
        )

        print("Messaggio Slack aggiornato.")

    except Exception as e:
        print("Errore aggiornamento Slack:", e)


def open_create_event_modal(trigger_id):
    client = get_client()

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "create_event_modal",
            "title": {
                "type": "plain_text",
                "text": "Crea Evento"
            },
            "submit": {
                "type": "plain_text",
                "text": "Crea"
            },
            "close": {
                "type": "plain_text",
                "text": "Annulla"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Titolo"
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
                            {"text": {"type": "plain_text", "text": "Calcio"}, "value": "soccer"},
                            {"text": {"type": "plain_text", "text": "Basket"}, "value": "basketball"},
                            {"text": {"type": "plain_text", "text": "Tennis"}, "value": "tennis"},
                            {"text": {"type": "plain_text", "text": "Yoga"}, "value": "yoga"},
                            {"text": {"type": "plain_text", "text": "Palestra"}, "value": "gym"},
                            {"text": {"type": "plain_text", "text": "Biciclettata"}, "value": "bike"},
                            {"text": {"type": "plain_text", "text": "Beach Volley"}, "value": "beach_volley"},
                            {"text": {"type": "plain_text", "text": "Escursione"}, "value": "hiking"},
                            {"text": {"type": "plain_text", "text": "Nuoto"}, "value": "swimming"},
                            {"text": {"type": "plain_text", "text": "Scacchi"}, "value": "chess"},
                            {"text": {"type": "plain_text", "text": "Videogiochi"}, "value": "videogames"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "location_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Luogo"
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
                        "text": "Data"
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
                        "text": "Ora"
                    },
                    "element": {
                        "type": "timepicker",
                        "action_id": "time"
                    }
                }
            ]
        }
    )