import json
from datetime import datetime as dt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import SportEvent, EventParticipant
from .slack_client import (
    send_event_message,
    open_create_event_modal,
    update_event_message,
    get_client
)

from .tasks import send_test_reminder_once


# ---------------- CREATE EVENT ----------------
@csrf_exempt
def create_event(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)

        naive_dt = dt.fromisoformat(data["datetime"])
        event_datetime = timezone.make_aware(
            naive_dt,
            timezone.get_current_timezone()
        )

        event = SportEvent.objects.create(
            title=data["title"],
            sport_type=data["sport_type"],
            location=data["location"],
            datetime=event_datetime,
            creator_id=data.get("creator_id", "anonymous"),
            slack_channel=data.get("slack_channel", "C0BAPGC76N6"),
            started=False
        )

        send_event_message(event)

        return JsonResponse({
            "id": event.id,
            "title": event.title,
            "status": "created"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ---------------- LIST EVENTS (NOT STARTED) ----------------
def list_events(request):
    now = timezone.now()

    events = SportEvent.objects.filter(
        started=False,
        datetime__gte=now
    ).order_by("datetime")[:10]

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
            title=parts[0] if len(parts) > 0 else "Slack Event",
            sport_type=parts[1] if len(parts) > 1 else "jogging",
            location=parts[2] if len(parts) > 2 else "Slack",
            datetime=timezone.now(),
            creator_id="slack",
            slack_channel="C0BAPGC76N6",
            started=False
        )

        send_event_message(event)

        return JsonResponse({
            "response_type": "ephemeral",
            "text": f"Event created: {event.title}"
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

            naive_dt = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

            event_datetime = timezone.make_aware(
                naive_dt,
                timezone.get_current_timezone()
            )

            event = SportEvent.objects.create(
                title=title,
                sport_type=sport,
                location=location,
                datetime=event_datetime,
                creator_id=payload["user"]["id"],
                slack_channel="C0BAPGC76N6",
                started=False
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
                    message = "You have been removed from the event"
                else:
                    event.participants.add(participant)
                    message = "You have been added to the event"

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

                text = "\n".join(names) if names else "*No participants*"

                client.chat_postEphemeral(
                    channel=event.slack_channel,
                    user=user_id,
                    text=(
                        f"*:busts_in_silhouette: PARTICIPANTS "
                        f"({event.title}) | TOTAL: ({participants.count()}):*\n{text}"
                    )
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

    now = timezone.now()

    events = SportEvent.objects.filter(
        started=False,
        datetime__gte=now
    ).order_by("datetime")[:10]

    if not events:
        return JsonResponse({
            "response_type": "in_channel",
            "text": "*No events available*"
        })

    text = "*:calendar: Active events:*\n\n"

    for e in events:
        text += (
            f"- {e.title} ({e.sport_type}) | "
            f"{e.location} | "
            f"{timezone.localtime(e.datetime).strftime('%d-%m-%Y %H:%M')}\n"
        )

    return JsonResponse({
        "response_type": "in_channel",
        "text": text
    })


# ---------------- MANUAL TEST REMINDER ----------------
@csrf_exempt
def test_reminder(request):
    try:
        send_test_reminder_once()
        return JsonResponse({"status": "sent"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)