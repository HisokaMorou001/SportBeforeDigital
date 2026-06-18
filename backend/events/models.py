from django.db import models


class SportEvent(models.Model):
    SPORT_TYPES = [
        ("jogging", "Jogging"),
        ("beach_volley", "Beach Volley"),
        ("bike", "Biciclettata"),
        ("gym", "Palestra"),
        ("tennis", "Tennis"),
        ("soccer", "Calcio"),
        ("basketball", "Basket"),
        ("padel", "Padel"),
        ("swimming", "Nuoto"),
        ("yoga", "Yoga"),
        ("hiking", "Escursione"),
        ("chess", "Scacchi"),
        ("videogames", "Videogiochi"),
    ]

    title = models.CharField(max_length=120)
    sport_type = models.CharField(max_length=20, choices=SPORT_TYPES)
    location = models.CharField(max_length=120)
    datetime = models.DateTimeField()

    creator_id = models.CharField(max_length=50)

    slack_channel = models.CharField(max_length=50, blank=True, default="")
    slack_ts = models.CharField(max_length=50, blank=True, default="")

    participants = models.ManyToManyField(
        "EventParticipant",
        related_name="events",
        blank=True
    )
    
    started = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.sport_type})"


class EventParticipant(models.Model):
    slack_user_id = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name or self.slack_user_id