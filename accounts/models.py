from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    """
    A custom user model that extends Django's built-in AbstractUser.
    """

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from markets.models import Instrument, Position
        all_instruments = Instrument.objects.all()
        for i in all_instruments:
            if (i.name == 'Cash'):
                pos_size = i.market.starting_funds
            else:
                pos_size = 0
            pos, _ = Position.objects.get_or_create(user=self, instrument = i, defaults = {'size' : pos_size})

    def __str__(self):
        return f'''{self.username} ({self.email})'''
