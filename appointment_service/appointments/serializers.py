# appointments/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import DoctorSchedule, Appointment

# --- Serializer cho Lịch làm việc của Bác sĩ ---
class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor_id', 'start_time', 'end_time', 'is_available']
        read_only_fields = ('id',) # ID chỉ đọc

# --- Serializer cho Lịch hẹn (dùng để đọc) ---
class AppointmentSerializer(serializers.ModelSerializer):
    # Có thể thêm các trường read-only để hiển thị tên BS, BN nếu đã lưu trong model
    # patient_name = serializers.CharField(read_only=True)
    # doctor_name = serializers.CharField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_id',
            'doctor_id',
            'appointment_time',
            'reason',
            'status',
            'schedule_slot', # Hiển thị ID của schedule slot nếu có liên kết
            'created_at',
            'updated_at',
            # 'patient_name', # Thêm nếu có lưu
            # 'doctor_name', # Thêm nếu có lưu
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'patient_id') # patient_id thường không đổi sau khi tạo

# --- Serializer riêng cho việc TẠO Lịch hẹn ---
class AppointmentCreateSerializer(serializers.ModelSerializer):
    # Client chỉ cần gửi doctor_id, appointment_time, reason.
    # patient_id sẽ được lấy từ thông tin user đang request (trong view).

    class Meta:
        model = Appointment
        fields = [
            'doctor_id',
            'appointment_time',
            'reason',
            'schedule_slot', # Tùy chọn: client có thể gửi ID slot nếu thiết kế theo slot
        ]
        # Không bao gồm patient_id, status (sẽ set mặc định), created_at, updated_at

    def validate_appointment_time(self, value):
        """
        Kiểm tra xem thời gian hẹn có phải là trong tương lai không.
        """
        if value <= timezone.now():
            raise serializers.ValidationError(_("Appointment time must be in the future."))
        # Có thể thêm kiểm tra giờ làm việc (ví dụ: không đặt lịch lúc 12h đêm)
        # if not (8 <= value.hour < 18): # Ví dụ: chỉ cho đặt từ 8h đến 17h
        #     raise serializers.ValidationError(_("Appointments can only be scheduled between 8 AM and 5 PM."))
        return value

    def validate(self, attrs):
        """
        Kiểm tra logic nghiệp vụ phức tạp hơn:
        1. Bác sĩ có lịch làm việc vào thời điểm đó không?
        2. Thời điểm đó đã có người khác đặt chưa (cả bác sĩ và bệnh nhân)?
        """
        appointment_time = attrs.get('appointment_time')
        doctor_id = attrs.get('doctor_id')
        # Giả định patient_id được truyền vào context từ view
        patient_id = self.context.get('patient_id')

        if not patient_id:
             raise serializers.ValidationError(_("Patient information is missing."))

        # 1. Kiểm tra lịch làm việc của bác sĩ (logic này cần chính xác hóa)
        # Ví dụ đơn giản: Bác sĩ có schedule bao phủ thời gian appointment_time không?
        # Lưu ý: Cần xử lý cẩn thận nếu thời gian khám > 1 slot
        schedule_exists = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            start_time__lte=appointment_time,
            end_time__gt=appointment_time, # Giả sử lịch hẹn bắt đầu trong khoảng thời gian làm việc
            is_available=True
        ).exists()

        if not schedule_exists:
            raise serializers.ValidationError(_("The doctor is not available at the selected time."))

        # 2. Kiểm tra trùng lịch của Bác sĩ
        doctor_conflict = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_time=appointment_time,
            status__in=[Appointment.STATUS_SCHEDULED, Appointment.STATUS_CONFIRMED] # Chỉ kiểm tra các lịch đang active
        ).exists()

        if doctor_conflict:
            raise serializers.ValidationError(_("The doctor already has an appointment at this time."))

        # 3. Kiểm tra trùng lịch của Bệnh nhân
        patient_conflict = Appointment.objects.filter(
            patient_id=patient_id,
            appointment_time=appointment_time,
            status__in=[Appointment.STATUS_SCHEDULED, Appointment.STATUS_CONFIRMED]
        ).exists()

        if patient_conflict:
            raise serializers.ValidationError(_("You already have an appointment at this time."))

        return attrs

# --- Serializer riêng cho việc CẬP NHẬT trạng thái Lịch hẹn ---
class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    # Chỉ cho phép cập nhật trường status
    class Meta:
        model = Appointment
        fields = ['status'] # Chỉ chứa trường status

    def validate_status(self, value):
        """
        Có thể thêm logic validate việc chuyển trạng thái ở đây.
        Ví dụ: không cho chuyển từ Completed về Scheduled.
        """
        # Lấy trạng thái hiện tại (nếu là update)
        # current_status = self.instance.status if self.instance else None
        # if current_status == Appointment.STATUS_COMPLETED and value == Appointment.STATUS_SCHEDULED:
        #    raise serializers.ValidationError("Cannot change status from Completed back to Scheduled.")
        if value not in dict(Appointment.STATUS_CHOICES):
             raise serializers.ValidationError(f"Invalid status value: {value}")
        return value