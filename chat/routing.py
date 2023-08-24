from django.urls import path , include,re_path
from chat.consumers import ChatConsumer
from chat.interview import InterviewConsumer

# Here, "" is routing to the URL ChatConsumer which
# will handle the chat functionality.
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/interview/(?P<room_name>\w+)/$", InterviewConsumer.as_asgi()),
]

