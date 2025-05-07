# users/models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _ # Thường dùng cho messages, fields

# Model Role để định nghĩa các vai trò trong hệ thống
class Role(models.Model):
    name = models.CharField(
        _("role name"), # Sử dụng gettext_lazy cho đa ngôn ngữ (tùy chọn)
        max_length=50,
        unique=True,
        help_text=_("Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages={
            'unique': _("A role with that name already exists."),
        },
    )
    description = models.TextField(
        _("description"),
        blank=True,
        null=True,
        help_text=_("A short description of the role.")
    )

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self):
        return self.name

# Model User tùy chỉnh, kế thừa từ AbstractUser của Django
class User(AbstractUser):
    # Kế thừa username, password, email, first_name, last_name, is_staff, is_active, date_joined từ AbstractUser

    # Thêm các trường tùy chỉnh
    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True, # Cho phép trống
        null=True,  # Cho phép giá trị NULL trong DB
        help_text=_("Optional. User's phone number.")
    )
    # Quan hệ ManyToMany với Role, một User có thể có nhiều Role
    roles = models.ManyToManyField(
        Role,
        verbose_name=_('roles'),
        blank=True, # Cho phép user không có role nào (tùy yêu cầu)
        related_name='users', # Tên để truy cập ngược từ Role -> User (role.users.all())
        help_text=_('The roles this user belongs to. A user will get all permissions granted to each of their roles.'),
    )

    # --- QUAN TRỌNG: Xử lý xung đột related_name với auth.User mặc định ---
    # Django User mặc định đã có quan hệ ManyToMany với Group và Permission.
    # Khi kế thừa AbstractUser, chúng ta cần đổi `related_name` cho các trường này
    # để tránh lỗi "Reverse accessor for 'User.groups' clashes with reverse accessor for 'Auth.User.groups'".
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="hms_user_set", # Đặt tên related_name khác đi
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="hms_user_permission_set", # Đặt tên related_name khác đi
        related_query_name="user",
    )
    # ---------------------------------------------------------------------

    # Có thể thêm các trường khác nếu cần, ví dụ: avatar, address,...
    # Tuy nhiên, thông tin profile chi tiết hơn nên để ở model Profile

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['username'] # Sắp xếp user theo username (tùy chọn)

    def __str__(self):
        return self.username

# Model Profile để lưu trữ thông tin bổ sung, không liên quan trực tiếp đến xác thực
class Profile(models.Model):
    # Quan hệ OneToOne với User tùy chỉnh của chúng ta
    # primary_key=True nghĩa là trường user này cũng là khóa chính của bảng Profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE, # Khi User bị xóa, Profile cũng bị xóa
        primary_key=True,
        related_name='profile' # Tên để truy cập từ User -> Profile (user.profile)
    )
    # Các trường thông tin profile khác
    date_of_birth = models.DateField(_("date of birth"), null=True, blank=True)
    address = models.TextField(_("address"), blank=True, null=True)
    # Ví dụ: thông tin chuyên khoa cho bác sĩ, mã bệnh nhân cho patient,...
    # Có thể tạo các model Profile con kế thừa từ Profile này nếu cần:
    # class DoctorProfile(Profile):
    #     specialty = models.CharField(...)
    # class PatientProfile(Profile):
    #     patient_code = models.CharField(...)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return f"{self.user.username}'s Profile"