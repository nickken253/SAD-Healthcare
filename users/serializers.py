# users/serializers.py
from rest_framework import serializers
from .models import User, Role, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

# Serializer cho Role model
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description'] # Các trường muốn hiển thị trong API

# Serializer cho Profile model
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'address'] # Không cần trường 'user' vì nó sẽ được lồng vào UserSerializer

# Serializer cho User model (dùng để đọc thông tin user)
class UserSerializer(serializers.ModelSerializer):
    # Hiển thị thông tin Profile lồng vào User
    profile = ProfileSerializer(read_only=True)
    # Hiển thị tên các Role thay vì chỉ ID (dùng StringRelatedField)
    roles = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        # Các trường muốn hiển thị trong API khi đọc thông tin User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'profile', # Trường lồng từ ProfileSerializer
            'roles',   # Trường lồng từ Role (hiển thị tên)
            'is_active',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ('is_active', 'is_staff', 'date_joined') # Các trường chỉ đọc

# Serializer riêng cho việc đăng ký User mới
class UserRegistrationSerializer(serializers.ModelSerializer):
    # Thêm trường password confirmation
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Password confirmation")
    # Ghi đè trường roles để cho phép nhận danh sách ID hoặc tên Role khi đăng ký
    roles = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        required=False # Cho phép không cần gán role khi đăng ký (tùy yêu cầu)
    )

    class Meta:
        model = User
        # Các trường cần cung cấp khi đăng ký
        fields = [
            'username',
            'email',
            'password',
            'password2', # Trường xác nhận mật khẩu
            'first_name',
            'last_name',
            'phone_number',
            'roles',   # Cho phép gán vai trò khi đăng ký
        ]
        # Thiết lập các thuộc tính bổ sung cho fields
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}, # Không hiển thị password khi đọc, ẩn khi nhập
            'first_name': {'required': True}, # Bắt buộc nhập first_name
            'last_name': {'required': True},  # Bắt buộc nhập last_name
        }

    # Validate dữ liệu (ví dụ: kiểm tra password và password2 khớp nhau)
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Có thể thêm validate email tồn tại ở đây nếu muốn
        # email = attrs.get('email')
        # if User.objects.filter(email=email).exists():
        #     raise serializers.ValidationError({"email": "Email already exists."})

        return attrs

    # Ghi đè phương thức create để xử lý việc tạo User và hash password
    def create(self, validated_data):
        # Lấy ra các roles đã được validate (nếu có)
        roles_data = validated_data.pop('roles', None)
        # Loại bỏ password2 vì không lưu vào model User
        validated_data.pop('password2')

        # Tạo user và hash password
        user = User.objects.create_user(**validated_data) # create_user sẽ tự hash password

        # Gán roles cho user nếu có
        if roles_data:
            user.roles.set(roles_data)

        # Tạo Profile mặc định cho user mới
        Profile.objects.create(user=user)

        return user
    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user) # Gọi phương thức gốc để lấy token

        # Thêm các custom claims vào token payload
        token['username'] = user.username # Thêm username
        token['is_staff'] = user.is_staff # Thêm cờ is_staff
        # Lấy danh sách tên các role của user
        roles = [role.name for role in user.roles.all()]
        token['roles'] = roles

        return token

    # (Tùy chọn) Có thể ghi đè phương thức validate để thêm dữ liệu vào response khi login thành công
    # def validate(self, attrs):
    #     data = super().validate(attrs) # data chứa access và refresh token
    #     # Thêm thông tin user vào response (ngoài token)
    #     data['user'] = {
    #         'id': self.user.id,
    #         'username': self.user.username,
    #         'email': self.user.email,
    #         'is_staff': self.user.is_staff,
    #         'roles': [role.name for role in self.user.roles.all()]
    #     }
    #     return data