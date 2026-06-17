from datetime import timedelta
from huey import crontab
from huey.contrib.djhuey import periodic_task
from django.utils import timezone

from .models import SportEvent
from .slack_client import get_client


SLACK_CHANNEL = "C0BAPGC76N6"


def send_test_reminder_once():
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = start + timedelta(days=1)

    events = SportEvent.objects.filter(
        datetime__gte=start,
        datetime__lt=end
    ).order_by("datetime")

    client = get_client()

    text = "*TEST REMINDER (immediato)*\n\n"

    if not events.exists():
        text += "Nessun evento per domani"
    else:
        for e in events:
            text += f"• {e.title} — {e.datetime.strftime('%H:%M')} ({e.location})\n"

    client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=text
    )


@periodic_task(crontab(hour=8, minute=0), name="send_daily_reminders_task")
def send_daily_reminders():

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = start + timedelta(days=1)

    events = SportEvent.objects.filter(
        datetime__gte=start,
        datetime__lt=end
    ).order_by("datetime")

    if not events.exists():
        print("[Huey] Nessun evento per domani")
        return

    client = get_client()

    text = "⏰ *Reminder eventi di domani:*\n\n"

    for e in events:
        text += f"• *{e.title}* — {e.datetime.strftime('%H:%M')} ({e.location})\n"

    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=text
        )
        print("[Huey] Reminder giornaliero inviato")

    except Exception as e:
        print("[Huey] Slack error:", e)