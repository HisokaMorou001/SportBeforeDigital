import os
from slack_sdk import WebClient

def get_client():
    return WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def send_event_message(event):
    client = get_client()

    client.chat_postMessage(
        channel=event.slack_channel or "#general",
        text=f"Nuovo evento: {event.title} - {event.sport_type} @ {event.location} ({event.datetime})"
    )

def open_create_event_modal(trigger_id):
    client = get_client()

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "create_event_modal",
            "title": {"type": "plain_text", "text": "Crea Evento"},
            "submit": {"type": "plain_text", "text": "Crea"},
            "close": {"type": "plain_text", "text": "Annulla"},
            "blocks": [
                # TITLE
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {"type": "plain_text", "text": "Titolo"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title"
                    }
                },

                # SPORT (dropdown)
                {
                    "type": "input",
                    "block_id": "sport_block",
                    "label": {"type": "plain_text", "text": "Sport"},
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
                            {"text": {"type": "plain_text", "text": "Videogiochi"}, "value": "videogames"},
                        ]
                    }
                },

                # LOCATION
                {
                    "type": "input",
                    "block_id": "location_block",
                    "label": {"type": "plain_text", "text": "Luogo"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "location"
                    }
                },

                # DATE
                {
                    "type": "input",
                    "block_id": "date_block",
                    "label": {"type": "plain_text", "text": "Data"},
                    "element": {
                        "type": "datepicker",
                        "action_id": "date"
                    }
                },

                # TIME
                {
                    "type": "input",
                    "block_id": "time_block",
                    "label": {"type": "plain_text", "text": "Ora"},
                    "element": {
                        "type": "timepicker",
                        "action_id": "time"
                    }
                },
            ]
        }
    )