import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import SportEvent
from .slack_client import send_event_message, open_create_event_modal

@csrf_exempt
def create_event(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)

        event = SportEvent.objects.create(
            title=data["title"],
            sport_type=data["sport_type"],
            location=data["location"],
            datetime=datetime.fromisoformat(data["datetime"]),
            creator_id=data.get("creator_id", "anonymous"),
            slack_channel=data.get("slack_channel", "")
        )

        send_event_message(event)

        return JsonResponse({
            "id": event.id,
            "title": event.title,
            "status": "created"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def list_events(request):
    events = SportEvent.objects.all().order_by("-datetime")

    return JsonResponse([
        {
            "id": e.id,
            "title": e.title,
            "sport_type": e.sport_type,
            "location": e.location,
            "datetime": e.datetime.isoformat(),
            "creator_id": e.creator_id,
        }
        for e in events
    ], safe=False)

@csrf_exempt
def slack_create_event(request):
    if request.method != "POST":
        return JsonResponse({"text": "POST only"}, status=200)

    trigger_id = request.POST.get("trigger_id")

    if trigger_id:
        try:
            open_create_event_modal(trigger_id)
            return JsonResponse({})
        except Exception as e:
            return JsonResponse({
                "response_type": "ephemeral",
                "text": f"Errore modal: {str(e)}"
            })

    user_text = request.POST.get("text", "")

    try:
        parts = [p.strip() for p in user_text.split("|")]

        event = SportEvent.objects.create(
            title=parts[0] if len(parts) > 0 else "Evento Slack",
            sport_type=parts[1] if len(parts) > 1 else "jogging",
            location=parts[2] if len(parts) > 2 else "Slack",
            datetime=datetime.now(),
            creator_id="slack",
            slack_channel=""
        )

        send_event_message(event)

        return JsonResponse({
            "response_type": "ephemeral",
            "text": f"Evento creato: {event.title}"
        })

    except Exception as e:
        return JsonResponse({
            "response_type": "ephemeral",
            "text": f"Errore: {str(e)}"
        })


@csrf_exempt
def slack_interaction(request):
    if request.method != "POST":
        return JsonResponse({}, status=200)

    try:
        payload_str = request.POST.get("payload")

        if not payload_str:
            payload_str = request.body.decode("utf-8")

        payload = json.loads(payload_str)

        if payload.get("type") == "view_submission":

            state = payload["view"]["state"]["values"]

            title = state["title_block"]["title"]["value"]

            sport = state["sport_block"]["sport_type"]["selected_option"]["value"]

            location = state["location_block"]["location"]["value"]

            date = state["date_block"]["date"]["selected_date"]
            time = state["time_block"]["time"]["selected_time"]

            from datetime import datetime
            event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            SportEvent.objects.create(
                title=title,
                sport_type=sport,
                location=location,
                datetime=event_datetime,
                creator_id=payload["user"]["id"],
                slack_channel=""
            )

            return JsonResponse({"response_action": "clear"})

        return JsonResponse({})

    except Exception as e:
        return JsonResponse({
            "response_action": "errors",
            "errors": {"general": str(e)}
        })


@csrf_exempt
def slack_events(request):
    if request.method != "POST":
        return JsonResponse({"text": "POST only"}, status=200)

    events = SportEvent.objects.all().order_by("-datetime")[:10]

    if not events:
        return JsonResponse({
            "response_type": "in_channel",
            "text": "Nessun evento disponibile"
        })

    text = "Eventi attivi:\n\n"

    for e in events:
        text += f"- {e.title} ({e.sport_type}) | {e.location} | {e.datetime.strftime('%d-%m-%Y %H:%M')}\n"

    return JsonResponse({
        "response_type": "in_channel",
        "text": text
    })