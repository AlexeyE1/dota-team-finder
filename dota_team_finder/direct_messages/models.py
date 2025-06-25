from django.db import models
from accounts.models import CustomUser
import shortuuid


class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid())
    users_online = models.ManyToManyField(CustomUser, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(CustomUser, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.group_name


class ChatMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='chat_messages')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.steam_nickname} : {self.body}"
    
    class Meta:
        ordering = ['-created_at']
