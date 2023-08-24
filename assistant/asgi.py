"""
ASGI config for assistant project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assistant.settings')

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter ,ChannelNameRouter, URLRouter
from chat import routing
from chat.docqa_consumer import DocQAConsumer,PrintConsumer
 
application = ProtocolTypeRouter(
    {
        "http" : get_asgi_application() ,
        "websocket" : AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )   
        ),
        "channel":ChannelNameRouter({
            "doc-qa":DocQAConsumer.as_asgi(),
        })
    }
)
#application = get_asgi_application()
