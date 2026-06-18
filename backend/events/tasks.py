from datetime import timedelta
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.utils import timezone

from .models import SportEvent
from .slack_client import get_client


SLACK_CHANNEL = "C0BAPGC76N6"


def send_test_reminder_once():
    start = timezone.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ) + timedelta(days=1)

    end = start + timedelta(days=1)

    events = SportEvent.objects.filter(
        datetime__gte=start,
        datetime__lt=end
    ).order_by("datetime")

    client = get_client()

    text = "*TEST REMINDER (immediate)*\n\n"

    if not events.exists():
        text += "No events scheduled for tomorrow"
    else:
        for e in events:
            text += (
                f"*- {e.title} ({e.sport_type})* | "
                f"TIME: {e.datetime.strftime('%H:%M')} | "
                f"LOCATION: {e.location}\n"
            )

    client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=text
    )


# -----------------------------
# DAILY REMINDER (08:00)
# -----------------------------
@periodic_task(crontab(hour=8, minute=0), name="send_daily_reminders_task")
def send_daily_reminders():

    start = timezone.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ) + timedelta(days=1)

    end = start + timedelta(days=1)

    events = SportEvent.objects.filter(
        datetime__gte=start,
        datetime__lt=end,
        started=False
    ).order_by("datetime")

    if not events.exists():
        print("[Huey] No events scheduled for tomorrow")
        return

    client = get_client()

    text = "⏰ *Tomorrow's Events Reminder:*\n\n"

    for e in events:
        text += (
            f"*- {e.title} ({e.sport_type})* | "
            f"TIME: {e.datetime.strftime('%H:%M')} | "
            f"LOCATION: {e.location}\n"
        )

    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=text
        )

        print("[Huey] Daily reminder sent")

    except Exception as e:
        print("[Huey] Slack error:", e)


# -----------------------------
# EVENT START DETECTOR
# -----------------------------
@periodic_task(crontab(minute="*"), name="start_events_task")
def start_events():

    now = timezone.now()

    events = SportEvent.objects.filter(
        datetime__lte=now,
        started=False
    )

    client = get_client()

    for e in events:

        try:
            client.chat_postMessage(
                channel=e.slack_channel or SLACK_CHANNEL,
                text=f"🏁 Event *{e.title}* has started!"
            )

            e.started = True
            e.save()

        except Exception as err:
            print("[Huey] Event start error:", err)