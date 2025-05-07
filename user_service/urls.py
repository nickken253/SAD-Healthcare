"""
URL configuration for user_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# # Import custom serializer và view mặc định
from users.serializers import MyTokenObtainPairSerializer # Đường dẫn đến custom serializer
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView, # Tùy chọn: để client kiểm tra token hợp lệ
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView


# Tạo một view mới sử dụng custom serializer
class MyTokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# urlpatterns = [
#     # ... (admin, users.urls)
#     path('api/v1/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), # Dùng view tùy chỉnh
#     path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
# ]
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Thêm dòng này để include tất cả URLs từ app 'users'
    # với tiền tố 'api/v1/users/'
    path('api/v1/users/', include('users.urls', namespace='users')),
    # Bạn có thể thêm các app/service khác ở đây sau này
    # path('api/v1/appointments/', include('appointments.urls', namespace='appointments')),
    
    
    # URLs cho JWT Token Authentication
    # Client sẽ gửi POST request với username/password đến đây để lấy token
    # path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # # Client sẽ gửi POST request với refresh token để lấy access token mới
    # path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # # (Tùy chọn) Client có thể gửi POST request với token để kiểm tra tính hợp lệ
    # path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('api/v1/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), # Dùng view tùy chỉnh
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

