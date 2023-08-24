from django.urls import path,re_path,include
from chat import views as chat_views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path("", chat_views.chatPage, name="chat-page"),
    re_path(r"chat/(?P<room_name>\w+)/$", chat_views.chatZoom, name="chat-zoom"),
    re_path(r"interview/(?P<room_name>\w+)/$", chat_views.interviewZoom, name="interview-zoom"),

    # login-section
    path("auth/login/", LoginView.as_view
         (template_name="chat/LoginPage.html"), name="login-user"),
    path("auth/logout/", LogoutView.as_view(), name="logout-user"),
]

