# users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserSerializer, RoleSerializer
from .models import User, Role, Profile
from rest_framework import viewsets
from users.permissions import IsAdminUser as CustomIsAdminUser # Đổi tên để tránh nhầm lẫn
from rest_framework.permissions import IsAuthenticated, AllowAny


# Import các lớp permission cần thiết
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from .permissions import IsAdminUser as CustomUserIsAdmin, IsDoctor as CustomUserIsDoctor, IsPatient as CustomUserIsPatient


# View sử dụng generics.CreateAPIView để xử lý việc tạo mới User (Đăng ký)
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all() # Cần thiết cho CreateAPIView nhưng không dùng nhiều ở đây
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] # Cho phép bất kỳ ai cũng có thể đăng ký

    # Có thể ghi đè perform_create nếu cần thêm logic sau khi tạo user thành công
    # def perform_create(self, serializer):
    #     user = serializer.save()
        # Gửi email chào mừng chẳng hạn

# View để lấy thông tin user đang đăng nhập (ví dụ)
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Chỉ user đã đăng nhập mới truy cập được

    def get_object(self):
        # Trả về chính đối tượng user đang gửi request
        return self.request.user
    
# --- View Liệt kê tất cả Users ---
class UserListView(generics.ListAPIView):
    queryset = User.objects.select_related('profile').prefetch_related('roles').all() # Tối ưu query
    serializer_class = UserSerializer
    permission_classes = [CustomUserIsAdmin] # Chỉ Admin mới được xem danh sách tất cả user

# --- View Xem chi tiết, Cập nhật, Xóa User ---
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.select_related('profile').prefetch_related('roles').all()
    serializer_class = UserSerializer
    # permission_classes = [IsAdminUser] # Đơn giản nhất: Chỉ Admin mới được xem/sửa/xóa

    # Hoặc có thể dùng permission tùy chỉnh phức tạp hơn:
    # Ví dụ: Admin được làm mọi thứ, user thường chỉ được xem/sửa chính mình
    # permission_classes = [IsAuthenticated, IsAdminOrSelf] # Cần tạo permission IsAdminOrSelf

    # Tạm thời dùng IsAdminUser để đảm bảo an toàn
    permission_classes = [CustomUserIsAdmin]

    # Ghi đè perform_destroy để xử lý logic trước khi xóa (nếu cần)
    # def perform_destroy(self, instance):
    #     # Ví dụ: không cho xóa superuser cuối cùng
    #     super().perform_destroy(instance)

# --- (Optional) Có thể cần Serializer riêng cho Update User nếu logic phức tạp ---
# Ví dụ: không cho phép thay đổi username, xử lý đổi mật khẩu,...
# class UserUpdateSerializer(serializers.ModelSerializer):
#     # ... định nghĩa các trường cho phép cập nhật
#     class Meta:
#         model = User
#         fields = ['email', 'first_name', 'last_name', 'phone_number', 'roles', ...] # Bỏ username, password

# --- ViewSet cho quản lý Roles (CRUD) ---
class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép xem, tạo, sửa, xóa Roles.
    Chỉ dành cho Admin.
    """
    queryset = Role.objects.all().order_by('name') # Lấy tất cả Role, sắp xếp theo tên
    serializer_class = RoleSerializer
    permission_classes = [CustomUserIsAdmin] # Chỉ Admin mới được quản lý Roles

    # Có thể thêm các tùy chỉnh khác cho ViewSet nếu cần
    # Ví dụ: override các phương thức create, update, destroy,...