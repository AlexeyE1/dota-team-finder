from django.contrib.auth.models import AbstractUser
from django.db import models



class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(choices=[('male', 'Male'), ('female', 'Female')], null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    
    # Steam
    steam_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    steam_avatar = models.URLField(blank=True, null=True)
    steam_nickname = models.CharField(max_length=255, blank=True, null=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    url = models.URLField(blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    
    # Игровая статистика
    mmr = models.PositiveIntegerField(null=True, blank=True)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    win_rate = models.FloatField(default=0)
    rank = models.CharField(max_length=50, null=True, blank=True)
    
    # Настройки игрока
    role = models.IntegerField(
        choices=[
            (1, 'Carry'),
            (2, 'Mid'),
            (3, 'Offlane'),
            (4, 'Support'),
            (5, 'Hard Support'),
        ], 
        null=True, 
        blank=True
    )
    available_from = models.TimeField(null=True, blank=True)
    available_to = models.TimeField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.steam_nickname