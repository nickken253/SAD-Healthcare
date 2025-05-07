# users/urls.py
from django.urls import path, include
from .views import UserRegistrationView, CurrentUserView
from .views import (
    UserRegistrationView,
    CurrentUserView,
    UserListView,
    UserDetailView,
    RoleViewSet,
)
# Import router nếu dùng cho RoleViewSet
from rest_framework.routers import DefaultRouter

# Đặt tên cho namespace của app (tùy chọn nhưng nên có)
app_name = 'users'
# --- (Tùy chọn) Sử dụng Router cho RoleViewSet ---
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role') # basename cần thiết nếu queryset ko định nghĩa rõ

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    # Thêm các URL patterns khác cho user ở đây (ví dụ: login, list, detail, update)
    
    # User Management (Admin only by default)
    path('', UserListView.as_view(), name='user-list'), # GET /api/v1/users/
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'), # GET, PUT, PATCH, DELETE /api/v1/users/{user_id}/

    # Role Management URLs - Include các URL được tạo tự động bởi router
    path('', include(router.urls)),
    # Router sẽ tự tạo các URL như:
    # GET, POST /api/v1/users/roles/
    # GET, PUT, PATCH, DELETE /api/v1/users/roles/{role_id}/
]