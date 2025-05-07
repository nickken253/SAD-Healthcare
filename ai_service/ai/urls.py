# ai_service/ai/urls.py
from django.urls import path
from .views import AIChatProxyView

app_name = 'ai'

urlpatterns = [
    path('chat/', AIChatProxyView.as_view(), name='chat-proxy'),
]