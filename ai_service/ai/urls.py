from django.urls import path
from .views import AIChatView # Đổi tên view cho rõ ràng hơn

app_name = 'ai'

urlpatterns = [
    path('chat/', AIChatView.as_view(), name='ai-chat'),
]