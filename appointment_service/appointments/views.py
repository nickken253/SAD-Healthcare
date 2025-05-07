# appointments/views.py
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta, datetime
from .models import DoctorSchedule, Appointment
from .serializers import (
    DoctorScheduleSerializer,
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser # Import permissions cơ bản
from .permissions import IsAdminClaim, IsDoctorClaim, IsPatientClaim, IsAppointmentOwnerOrAdminOrAssociatedDoctor
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminClaim, IsDoctorClaim, IsPatientClaim, CanModifyOrViewAppointment

# --- View lấy danh sách lịch làm việc của bác sĩ ---
class DoctorScheduleListView(generics.ListAPIView):
    """
    API xem lịch làm việc của các bác sĩ.
    Có thể lọc theo doctor_id, ngày bắt đầu, ngày kết thúc.
    Ví dụ: /api/v1/appointments/schedules/?doctor_id=1&start_date=2025-05-10&end_date=2025-05-15
    """
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated] # Bất kỳ ai đăng nhập cũng có thể xem lịch

    def get_queryset(self):
        queryset = DoctorSchedule.objects.filter(is_available=True, end_time__gte=timezone.now()) # Chỉ lấy lịch còn hiệu lực và còn trống
        doctor_id = self.request.query_params.get('doctor_id')
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        if start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
                queryset = queryset.filter(start_time__date__gte=start_date)
            except ValueError:
                pass # Bỏ qua nếu format ngày sai

        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
                # Lấy đến cuối ngày end_date
                queryset = queryset.filter(start_time__date__lte=end_date)
            except ValueError:
                pass # Bỏ qua nếu format ngày sai

        return queryset.order_by('start_time')

# --- View Tạo Lịch hẹn mới ---
class AppointmentCreateView(generics.CreateAPIView):
    """
    API để bệnh nhân đặt lịch hẹn mới.
    """
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsAuthenticated, IsPatientClaim] # Yêu cầu đăng nhập để đặt lịch

    def perform_create(self, serializer):
        # Tự động gán patient_id từ user đang thực hiện request
        # Quan trọng: Giả định ID user trong hệ thống user_service chính là patient_id
        # Cần đảm bảo cơ chế lấy ID này là đúng (ví dụ: từ JWT payload)
        serializer.save(patient_id=self.request.user.id, status=Appointment.STATUS_SCHEDULED)
        # Có thể gửi sự kiện vào Message Queue ở đây để NotificationService gửi thông báo

    def get_serializer_context(self):
        """
        Truyền patient_id vào context để serializer có thể sử dụng trong validate.
        """
        context = super(AppointmentCreateView, self).get_serializer_context()
        context.update({"patient_id": self.request.user.id})
        return context

# --- View Lấy danh sách lịch hẹn của Bệnh nhân hiện tại ---
class PatientAppointmentListView(generics.ListAPIView):
    """
    API xem danh sách lịch hẹn của bệnh nhân đang đăng nhập.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatientClaim]

    def get_queryset(self):
        # Lấy user hiện tại (patient_id)
        user_id = self.request.user.id
        # Lọc các lịch hẹn của user đó, sắp xếp theo thời gian gần nhất
        return Appointment.objects.filter(patient_id=user_id).order_by('-appointment_time')

# --- View Lấy danh sách lịch hẹn của Bác sĩ (Yêu cầu quyền Admin hoặc Doctor) ---
class DoctorAppointmentListView(generics.ListAPIView):
    """
    API xem danh sách lịch hẹn của một bác sĩ cụ thể.
    Cần doctor_id làm query parameter.
    Yêu cầu quyền Admin hoặc chính bác sĩ đó.
    Ví dụ: /api/v1/appointments/doctor-appointments/?doctor_id=5
    """
    serializer_class = AppointmentSerializer
    # permission_classes = [IsAuthenticated, IsAdminOrAssociatedDoctor] # Cần permission tùy chỉnh
    permission_classes = [IsAuthenticated, IsDoctorClaim] # Tạm thời chỉ cho Admin

    def get_queryset(self):
        user = self.request.user
        if 'Doctor' in user.get('roles', []) and not user.get('is_staff', False):
            # Nếu là Doctor, chỉ lấy lịch của chính doctor đó (user.id là doctor_id)
            return Appointment.objects.filter(
                doctor_id=user.get('user_id'), # Giả định user_id của doctor là doctor_id
                appointment_time__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).order_by('appointment_time')
        elif user.get('is_staff', False):
            # Nếu là Admin, cho phép lọc theo doctor_id từ query params
            doctor_id_param = self.request.query_params.get('doctor_id')
            if doctor_id_param:
                try:
                    return Appointment.objects.filter(
                        doctor_id=int(doctor_id_param),
                        appointment_time__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    ).order_by('appointment_time')
                except (ValueError, TypeError):
                    return Appointment.objects.none()
            return Appointment.objects.filter( # Admin xem tất cả nếu không có doctor_id
                appointment_time__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).order_by('appointment_time')
        return Appointment.objects.none() # Không có quyền


# --- View Xem chi tiết, Cập nhật (trạng thái), Hủy lịch hẹn ---
class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API xem chi tiết, cập nhật trạng thái (hủy), hoặc xóa lịch hẹn.
    """
    queryset = Appointment.objects.all()
    # permission_classes = [IsAuthenticated, IsOwnerOrAdminOrDoctor] # Cần permission tùy chỉnh
    permission_classes = [IsAuthenticated, IsAppointmentOwnerOrAdminOrAssociatedDoctor, CanModifyOrViewAppointment]

    def get_serializer_class(self):
        # Dùng serializer khác nhau cho việc đọc và cập nhật status
        if self.request.method in ['PUT', 'PATCH']:
            return AppointmentStatusUpdateSerializer
        return AppointmentSerializer

    def get_permissions(self):
        # Quyền hạn khác nhau tùy theo action
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Ví dụ: Chỉ chủ sở hữu (bệnh nhân) hoặc Admin mới được hủy/sửa status
            # Cần kiểm tra logic phức tạp hơn (ví dụ: chỉ hủy trước 24h)
            # return [IsAuthenticated(), IsOwnerOrAdmin()] # Custom permission
            return [IsAdminUser()] # Tạm thời chỉ cho Admin sửa/xóa
        # Cho phép xem chi tiết nếu là chủ sở hữu hoặc admin hoặc bác sĩ liên quan
        # return [IsAuthenticated(), IsOwnerOrAdminOrDoctor()]
        if self.request.method in ['GET']: # GET
            return [IsAuthenticated()] # Tạm thời cho ai cũng xem nếu biết ID, sẽ được lọc bởi has_object_permission
        return [IsAuthenticated(), CanModifyOrViewAppointment()] # Tạm thời cho ai đăng nhập cũng xem được detail nếu biết ID


    # Ghi đè phương thức update/partial_update để chỉ cho phép cập nhật status
    def update(self, request, *args, **kwargs):
        # Chỉ cho phép cập nhật nếu dùng AppointmentStatusUpdateSerializer
        if self.get_serializer_class() != AppointmentStatusUpdateSerializer:
             return Response({"detail": "Method not allowed for this serializer."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)

        # --- Thêm logic kiểm tra quyền hạn cập nhật status ---
        # Ví dụ: Bệnh nhân chỉ được cập nhật status thành 'Cancelled'
        new_status = serializer.validated_data.get('status')
        user = request.user

        # if not user.is_staff and instance.patient_id == user.id: # Nếu là bệnh nhân sở hữu
        #     if new_status != Appointment.STATUS_CANCELLED:
        #         return Response({"detail": "You can only cancel your appointment."}, status=status.HTTP_403_FORBIDDEN)
             # Thêm kiểm tra thời gian hủy hợp lệ
             # if instance.appointment_time < timezone.now() + timedelta(hours=24):
             #    return Response({"detail": "Cannot cancel appointment less than 24 hours in advance."}, status=status.HTTP_403_FORBIDDEN)

        # Nếu là Admin hoặc các role khác có quyền, cho phép cập nhật các status khác (Confirmed, Completed)
        # elif user.is_staff:
        #     pass # Admin có thể cập nhật thành các trạng thái khác

        # else: # Không phải chủ sở hữu hoặc admin
        #     return Response({"detail": "You do not have permission to update this appointment status."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_update(serializer)
        return Response(serializer.data)

    # Ghi đè destroy để kiểm tra quyền xóa (thường chỉ Admin)
    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     # Thêm logic kiểm tra quyền xóa
    #     self.perform_destroy(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)