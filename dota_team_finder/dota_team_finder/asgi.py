import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import direct_messages.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dota_team_finder.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            direct_messages.routing.websocket_urlpatterns
        )
    ),
})