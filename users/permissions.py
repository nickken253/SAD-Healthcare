# user_service/users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminUser(BasePermission):
    """
    Cho phép truy cập chỉ khi user đã xác thực và có is_staff=True từ token.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )

class IsDoctor(BasePermission):
    """
    Cho phép truy cập chỉ khi user đã xác thực và có role 'Doctor' trong token.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # request.user ở đây là đối tượng từ token (sau khi simplejwt xử lý)
        # Nó là một dict-like object hoặc SimpleLazyObject chứa claims
        # user_roles = request.user.get('roles', [])
        # return 'Doctor' in user_roles # Kiểm tra role 'Doctor'
        return request.user.roles.filter(name='Doctor').exists()

class IsPatient(BasePermission):
    """
    Cho phép truy cập chỉ khi user đã xác thực và có role 'Patient' trong token.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # user_roles = request.user.get('roles', [])
        # return 'Patient' in user_roles # Kiểm tra role 'Patient'
        return request.user.roles.filter(name='Patient').exists()

class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to edit/view it.
    Assumes the model instance has a `patient_id` or `user_id` or `user` attribute.
    Hoặc kiểm tra `is_staff` từ token.
    """
    def has_object_permission(self, request, view, obj):
        # Admin có mọi quyền
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True

        # Chủ sở hữu (ví dụ: Profile của user)
        if hasattr(obj, 'user'): # Nếu object có trường 'user' (ví dụ Profile)
            return obj.user == request.user
        # Hoặc nếu object có trường patient_id (ví dụ Appointment, nhưng class này đang ở user_service)
        # if hasattr(obj, 'patient_id'):
        #     return obj.patient_id == request.user.id

        return False