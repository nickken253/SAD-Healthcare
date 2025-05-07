# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Profile

# Tùy chỉnh cách hiển thị Model User trong trang Admin (kế thừa từ UserAdmin)
class UserAdmin(BaseUserAdmin):
    # Thêm các trường tùy chỉnh vào màn hình danh sách user
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles')
    # Thêm bộ lọc theo vai trò
    list_filter = BaseUserAdmin.list_filter + ('roles',)
    # Thêm trường roles vào fieldsets để chỉnh sửa trong trang chi tiết user
    # Lấy fieldsets từ BaseUserAdmin và thêm mục mới
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('phone_number', 'roles')}),
    )
    # Thêm trường roles vào add_fieldsets để hiển thị khi tạo user mới
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('phone_number', 'roles')}),
    )

    # Hàm để lấy danh sách roles hiển thị trong list_display
    @admin.display(description='Roles')
    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])

# Tùy chỉnh cách hiển thị Model Role
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',) # Cho phép tìm kiếm theo tên role

# Tùy chỉnh cách hiển thị Model Profile (sử dụng Inline)
# Inline cho phép chỉnh sửa Profile ngay trong trang chi tiết User
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False # Không cho phép xóa Profile từ trang User
    verbose_name_plural = 'Profile'
    fk_name = 'user' # Chỉ định foreign key

# Kế thừa UserAdmin đã tùy chỉnh ở trên và thêm ProfileInline
class CustomUserAdminWithProfile(UserAdmin):
    inlines = (ProfileInline,)

    # Ghi đè phương thức get_inline_instances để đảm bảo inline hoạt động đúng
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdminWithProfile, self).get_inline_instances(request, obj)


# Đăng ký các models với trang Admin
# Sử dụng CustomUserAdminWithProfile thay vì chỉ UserAdmin để có cả Profile inline
admin.site.register(User, CustomUserAdminWithProfile)
admin.site.register(Role, RoleAdmin)
# Không cần đăng ký Profile riêng lẻ vì nó đã được hiển thị inline trong User
# admin.site.register(Profile)