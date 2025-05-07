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

from datetime import date, time, timedelta, datetime
from django.utils import timezone # Dùng timezone hiện tại
from rest_framework.exceptions import ParseError, NotFound

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
    
# --- View Lấy các khung giờ trống của bác sĩ trong một ngày cụ thể ---
class AvailableSlotsView(views.APIView):
    """
    API lấy danh sách các khung giờ còn trống để đặt lịch hẹn.
    Yêu cầu: doctor_id và date (YYYY-MM-DD) trong query params.
    Ví dụ: /api/v1/appointments/available-slots/?doctor_id=1&date=2025-05-10
    Giả định mỗi slot là 30 phút.
    """
    permission_classes = [IsAuthenticated] # Ai đăng nhập cũng có thể xem slot

    def get(self, request, *args, **kwargs):
        # 1. Lấy và Validate query parameters
        doctor_id_str = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')

        if not doctor_id_str or not date_str:
            raise ParseError("Cần cung cấp 'doctor_id' và 'date' (YYYY-MM-DD).")

        try:
            doctor_id = int(doctor_id_str)
        except ValueError:
            raise ParseError("'doctor_id' phải là số nguyên.")

        try:
            requested_date = date.fromisoformat(date_str)
        except ValueError:
            raise ParseError("'date' phải có định dạng YYYY-MM-DD.")

        # Không cho xem slot quá khứ
        current_date = timezone.now().date()
        if requested_date < current_date:
             raise ParseError("Không thể xem slot cho ngày trong quá khứ.")

        # 2. Lấy các lịch hẹn đã được đặt của bác sĩ trong ngày đó
        start_of_day_dt = timezone.make_aware(datetime.combine(requested_date, time.min))
        end_of_day_dt = timezone.make_aware(datetime.combine(requested_date, time.max))

        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_time__gte=start_of_day_dt,
            appointment_time__lte=end_of_day_dt, # Chỉ lấy trong ngày yêu cầu
            status__in=[Appointment.STATUS_SCHEDULED, Appointment.STATUS_CONFIRMED]
        )
        booked_start_times = {appt.appointment_time for appt in booked_appointments}
        print(f"--- Debugging AvailableSlots ---")
        print(f"Requested Doctor ID: {doctor_id}, Date: {requested_date}")
        print(f"Booked start times on {requested_date}: {booked_start_times}")


        # 3. Lấy các schedule của bác sĩ *chồng lấn* với ngày yêu cầu
        schedules_overlapping = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            start_time__date__lte=requested_date, # Bắt đầu trước hoặc trong ngày yêu cầu
            end_time__date__gte=requested_date,   # Kết thúc trong hoặc sau ngày yêu cầu
            is_available=True
        ).order_by('start_time')
        print(f"Found overlapping schedules count: {schedules_overlapping.count()}")


        # 4. Tạo danh sách các slot trống
        available_slots = set() # Dùng set để tự loại bỏ trùng lặp
        appointment_duration = timedelta(minutes=30)
        now = timezone.now()
        print(f"Current time (now): {now}")

        for schedule in schedules_overlapping:
            print(f"Processing schedule: ID={schedule.id}, Start={schedule.start_time}, End={schedule.end_time}")

            # Xác định khoảng thời gian hiệu lực của schedule TRONG ngày yêu cầu
            effective_start_dt = max(schedule.start_time, start_of_day_dt)
            effective_end_dt = min(schedule.end_time, end_of_day_dt)
            print(f"  Effective range for {requested_date}: {effective_start_dt} to {effective_end_dt}")

            # Xác định thời điểm bắt đầu vòng lặp slot
            # Phải lớn hơn hoặc bằng thời điểm hiện tại nếu là ngày hôm nay
            current_potential_start = effective_start_dt
            if requested_date == current_date:
                # Làm tròn thời gian hiện tại lên mốc 30 phút tiếp theo
                minutes_to_add = 30 - (now.minute % 30) if now.minute % 30 != 0 else 0
                rounded_now = (now + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)
                current_potential_start = max(effective_start_dt, rounded_now)

            print(f"  Starting slot check from: {current_potential_start}")

            # Bắt đầu tạo và kiểm tra slot
            slot_start_time = current_potential_start
            loop_count = 0
            while slot_start_time < effective_end_dt and loop_count < 100: # Lặp trong khoảng hiệu lực của ngày
                slot_end_time = slot_start_time + appointment_duration

                # Chỉ xét slot nếu nó KẾT THÚC TRƯỚC hoặc BẰNG thời gian kết thúc hiệu lực
                if slot_end_time > effective_end_dt:
                    print(f"    Slot {slot_start_time.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')} ends after effective end ({effective_end_dt.strftime('%H:%M')}). Stopping for this schedule.")
                    break

                # Kiểm tra xem slot đã bị đặt chưa
                is_booked = slot_start_time in booked_start_times
                print(f"    Checking slot: {slot_start_time.strftime('%H:%M')} - {slot_end_time.strftime('%H:%M')}. Booked? {is_booked}")

                if not is_booked:
                    # Kiểm tra lại lần nữa xem có đúng là > now không (đề phòng edge case)
                    if slot_start_time > now:
                        print(f"    >>> Adding slot: {slot_start_time}")
                        available_slots.add(slot_start_time)
                    else:
                         print(f"    Slot {slot_start_time.strftime('%H:%M')} is not in the future (Now: {now.strftime('%H:%M')}). Skipping.")

                slot_start_time += appointment_duration
                loop_count+=1
            if loop_count >=100:
                print(f"    WARNING: Loop limit reached for schedule {schedule.id}")


        # Sắp xếp và format output
        sorted_slots = sorted(list(available_slots))
        formatted_slots = [slot.strftime("%Y-%m-%dT%H:%M:%S%z") for slot in sorted_slots]
        print(f"Final available slots (formatted): {formatted_slots}")

        return Response(formatted_slots, status=status.HTTP_200_OK)