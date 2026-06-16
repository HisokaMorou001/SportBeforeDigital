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
    slack_channel = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.sport_type})"