# clinical_service/clinical/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminClaim(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.get('is_staff', False)
        )

class IsDoctorClaim(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return 'Doctor' in request.user.get('roles', [])

class IsPatientClaim(BasePermission): # Thêm nếu Patient được xem EHR
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return 'Patient' in request.user.get('roles', [])