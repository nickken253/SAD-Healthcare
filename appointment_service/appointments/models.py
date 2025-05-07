# appointments/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Có thể cần nếu dùng AUTH_USER_MODEL, nhưng ở đây ta dùng ID

# Model Lịch làm việc của Bác sĩ
class DoctorSchedule(models.Model):
    # Lưu ID của bác sĩ từ UserService
    # Chúng ta không dùng ForeignKey trực tiếp đến User của user_service
    # vì đây là 2 service/database riêng biệt.
    doctor_id = models.IntegerField(
        _("doctor id"),
        db_index=True, # Tạo index để query nhanh hơn theo doctor_id
        help_text=_("ID of the Doctor from the User Service")
    )
    # Có thể lưu tên bác sĩ ở đây (dữ liệu sao chép) để tiện hiển thị,
    # nhưng cần cơ chế đồng bộ nếu tên thay đổi ở user_service.
    # doctor_name = models.CharField(max_length=255, blank=True, null=True)

    start_time = models.DateTimeField(_("start time"))
    end_time = models.DateTimeField(_("end time"))
    # Cân nhắc: Thay vì start/end time, có thể chia thành các slot nhỏ hơn (ví dụ 15 phút/slot)
    # và đánh dấu slot nào còn trống (is_available). Hoặc giữ start/end và kiểm tra logic khi book.

    is_available = models.BooleanField(
        _("is available"),
        default=True,
        help_text=_("Is this time slot generally available (before considering appointments)?")
    )

    class Meta:
        verbose_name = _('doctor schedule')
        verbose_name_plural = _('doctor schedules')
        # Đảm bảo không có lịch trình trùng lặp cho cùng một bác sĩ
        # unique_together = ('doctor_id', 'start_time', 'end_time') # Có thể gây khó khăn nếu lịch linh hoạt
        ordering = ['doctor_id', 'start_time']

    def __str__(self):
        return f"Dr. ID {self.doctor_id}: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"

# Model Lịch hẹn khám bệnh
class Appointment(models.Model):
    STATUS_SCHEDULED = 'Scheduled'
    STATUS_CONFIRMED = 'Confirmed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_COMPLETED = 'Completed'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, _('Scheduled')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    # Lưu ID của bệnh nhân từ UserService/PatientService
    patient_id = models.IntegerField(
        _("patient id"),
        db_index=True,
        help_text=_("ID of the Patient from the User Service")
    )
    # Lưu ID của bác sĩ từ UserService
    doctor_id = models.IntegerField(
        _("doctor id"),
        db_index=True,
        help_text=_("ID of the Doctor from the User Service")
    )

    # Có thể liên kết với một slot cụ thể trong DoctorSchedule nếu thiết kế theo slot
    schedule_slot = models.ForeignKey(
        DoctorSchedule,
        on_delete=models.SET_NULL, # Nếu lịch bác sĩ bị xóa, không xóa lịch hẹn mà chỉ set null
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name=_("schedule slot")
    )

    # Thời gian hẹn chính xác (quan trọng)
    appointment_time = models.DateTimeField(
        _("appointment time"),
        db_index=True
    )
    # Thời gian kết thúc dự kiến (tùy chọn, có thể tính dựa trên thời gian khám trung bình)
    # end_time = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(
        _("reason for appointment"),
        blank=True,
        null=True
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SCHEDULED,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Lưu dữ liệu sao chép để tiện hiển thị (cần cơ chế đồng bộ)
    # patient_name = models.CharField(max_length=255, blank=True, null=True)
    # doctor_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('appointment')
        verbose_name_plural = _('appointments')
        # Đảm bảo một bệnh nhân không đặt 2 lịch cùng lúc
        # Hoặc một bác sĩ không có 2 lịch cùng lúc
        unique_together = (('patient_id', 'appointment_time'), ('doctor_id', 'appointment_time'))
        ordering = ['appointment_time']

    def __str__(self):
        return f"Appt ID: {self.id} - Patient: {self.patient_id} with Dr: {self.doctor_id} at {self.appointment_time.strftime('%Y-%m-%d %H:%M')}"