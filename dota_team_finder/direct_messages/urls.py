from django.urls import path
from .views import ChatView, get_or_create_chat, bot_chat_view

app_name = 'direct_messages'

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('chat/<slug:slug_profile>/', get_or_create_chat, name='start-chat'),
    path('chat/room/bot/', bot_chat_view, name='bot_chatroom'),
    path('chat/room/<chatroom_name>/', ChatView.as_view(), name='chatroom'),
] 