# appointment_service/appointments/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.utils import timezone # Cần cho ví dụ nâng cao
from datetime import timedelta  # Cần cho ví dụ nâng cao

class IsAdminClaim(BasePermission): # Kiểm tra is_staff từ claim
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

class IsPatientClaim(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return 'Patient' in request.user.get('roles', [])

class IsAppointmentOwnerOrAdminOrAssociatedDoctor(BasePermission):
    def has_object_permission(self, request, view, obj): # obj là instance của Appointment
        # Admin có mọi quyền
        if request.user.get('is_staff', False):
            return True

        # Bệnh nhân sở hữu lịch hẹn
        if obj.patient_id == request.user.get('user_id'):
            # Bệnh nhân có thể xem (GET, HEAD, OPTIONS)
            if request.method in SAFE_METHODS:
                return True
            # Bệnh nhân có thể hủy (ví dụ nếu action là 'cancel' hoặc method là PATCH/PUT với status 'Cancelled')
            # Logic này cần cụ thể hơn, ví dụ cho phép PATCH status thành 'Cancelled'
            if request.method in ['PUT', 'PATCH'] and request.data.get('status') == obj.STATUS_CANCELLED:
                # Thêm kiểm tra thời gian hủy hợp lệ ở đây
                # if obj.appointment_time < timezone.now() + timedelta(hours=24): return False
                return True
            return False # Các hành động khác không cho phép

        # Bác sĩ liên quan đến lịch hẹn có thể xem
        if request.method in SAFE_METHODS and obj.doctor_id == request.user.get('user_id'):
             # Giả định user_id của bác sĩ cũng là doctor_id trong appointment
             # Điều này cần đảm bảo khi bác sĩ đăng nhập, user_id của họ được dùng làm doctor_id
             return True # Bác sĩ có thể xem

        return False
    
class CanModifyOrViewAppointment(BasePermission):
    def has_object_permission(self, request, view, obj): # obj là instance của Appointment
        user = request.user
        if not (user and user.is_authenticated):
            return False

        # Admin có mọi quyền
        if user.get('is_staff', False):
            return True

        # Bệnh nhân sở hữu lịch hẹn
        if obj.patient_id == user.get('user_id'): # Giả định user_id từ token là patient_id
            if request.method in SAFE_METHODS: # GET, HEAD, OPTIONS
                return True
            # Bệnh nhân có thể hủy (PATCH/PUT với status là Cancelled)
            if request.method in ['PUT', 'PATCH'] and request.data.get('status') == obj.STATUS_CANCELLED:
                # (Tùy chọn) Thêm logic kiểm tra thời gian hủy, ví dụ:
                # if obj.appointment_time < timezone.now() + timedelta(hours=24):
                #     self.message = "Cannot cancel appointment less than 24 hours in advance."
                #     return False
                return True
            return False # Các hành động ghi khác của bệnh nhân không được phép

        # Bác sĩ liên quan đến lịch hẹn có thể xem
        if request.method in SAFE_METHODS and obj.doctor_id == user.get('user_id'): # Giả định user_id của doctor là doctor_id
            return True
        
        # Bác sĩ liên quan có thể cập nhật status thành Confirmed hoặc Completed
        if obj.doctor_id == user.get('user_id') and request.method in ['PUT', 'PATCH']:
            allowed_doctor_statuses = [obj.STATUS_CONFIRMED, obj.STATUS_COMPLETED]
            if request.data.get('status') in allowed_doctor_statuses:
                return True

        return False