import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import SportEvent, EventParticipant
from .slack_client import (
    send_event_message,
    open_create_event_modal,
    update_event_message,
    get_client
)

from .tasks import send_test_reminder_once  # opzionale (test manuale)


# ---------------- CREATE EVENT ----------------
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
            slack_channel=data.get("slack_channel", "C0BAPGC76N6")
        )

        send_event_message(event)

        return JsonResponse({
            "id": event.id,
            "title": event.title,
            "status": "created"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ---------------- LIST EVENTS ----------------
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


# ---------------- SLACK CREATE EVENT ----------------
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
            return JsonResponse({"text": str(e)})

    user_text = request.POST.get("text", "")

    try:
        parts = [p.strip() for p in user_text.split("|")]

        event = SportEvent.objects.create(
            title=parts[0] if len(parts) > 0 else "Evento Slack",
            sport_type=parts[1] if len(parts) > 1 else "jogging",
            location=parts[2] if len(parts) > 2 else "Slack",
            datetime=datetime.now(),
            creator_id="slack",
            slack_channel="C0BAPGC76N6"
        )

        send_event_message(event)

        return JsonResponse({
            "response_type": "ephemeral",
            "text": f"Evento creato: {event.title}"
        })

    except Exception as e:
        return JsonResponse({"text": str(e)})


# ---------------- SLACK INTERACTIONS ----------------
@csrf_exempt
def slack_interaction(request):
    if request.method != "POST":
        return JsonResponse({}, status=200)

    try:
        payload_str = request.POST.get("payload") or request.body.decode("utf-8")

        if payload_str.startswith("payload="):
            payload_str = payload_str.replace("payload=", "", 1)

        payload = json.loads(payload_str)

        # ================= VIEW SUBMISSION =================
        if payload.get("type") == "view_submission":

            state = payload["view"]["state"]["values"]

            title = state["title_block"]["title"]["value"]
            sport = state["sport_block"]["sport_type"]["selected_option"]["value"]
            location = state["location_block"]["location"]["value"]

            date = state["date_block"]["date"]["selected_date"]
            time = state["time_block"]["time"]["selected_time"]

            event_datetime = datetime.strptime(
                f"{date} {time}",
                "%Y-%m-%d %H:%M"
            )

            event = SportEvent.objects.create(
                title=title,
                sport_type=sport,
                location=location,
                datetime=event_datetime,
                creator_id=payload["user"]["id"],
                slack_channel="C0BAPGC76N6"
            )

            send_event_message(event)

            return JsonResponse({"response_action": "clear"})


        # ================= BUTTON ACTIONS =================
        if payload.get("type") == "block_actions":

            action = payload["actions"][0]
            event_id = action["value"]
            user_id = payload["user"]["id"]

            event = SportEvent.objects.get(id=event_id)

            # -------- JOIN EVENT --------
            if action["action_id"] == "join_event":

                participant, _ = EventParticipant.objects.get_or_create(
                    slack_user_id=user_id
                )

                already_joined = event.participants.filter(
                    slack_user_id=user_id
                ).exists()

                if already_joined:
                    event.participants.remove(participant)
                    message = "Sei stato rimosso dall'evento"
                else:
                    event.participants.add(participant)
                    message = "Sei stato aggiunto all'evento"

                event.save()
                update_event_message(event)

                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": message
                })


            # -------- LIST PARTICIPANTS --------
            if action["action_id"] == "list_participants":

                participants = event.participants.all()
                client = get_client()

                names = []

                for p in participants:
                    try:
                        res = client.users_info(user=p.slack_user_id)
                        user = res.get("user", {})
                        profile = user.get("profile", {})

                        name = (
                            profile.get("display_name")
                            or profile.get("real_name")
                            or user.get("name")
                            or p.slack_user_id
                        )
                    except Exception:
                        name = p.slack_user_id

                    names.append(f"- {name}")

                text = "\n".join(names) if names else "Nessun partecipante"

                client.chat_postEphemeral(
                    channel=event.slack_channel,
                    user=user_id,
                    text=f"Partecipanti ({event.title}) ({participants.count()}):\n{text}"
                )

                return JsonResponse({}, status=200)

        return JsonResponse({})

    except Exception as e:
        return JsonResponse({
            "response_action": "errors",
            "errors": {"general": str(e)}
        })


# ---------------- SLACK EVENTS COMMAND ----------------
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
        text += (
            f"- {e.title} ({e.sport_type}) | "
            f"{e.location} | "
            f"{e.datetime.strftime('%d-%m-%Y %H:%M')}\n"
        )

    return JsonResponse({
        "response_type": "in_channel",
        "text": text
    })


# ---------------- TEST REMINDER MANUALE ----------------
@csrf_exempt
def test_reminder(request):
    """
    Endpoint per test immediato Huey reminder.
    """
    try:
        send_test_reminder_once()
        return JsonResponse({"status": "sent"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)