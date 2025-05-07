# clinical/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Model Chẩn đoán
class Diagnosis(models.Model):
    # Lưu ID của Lịch hẹn từ AppointmentService
    # Nên là unique để mỗi lịch hẹn chỉ có 1 chẩn đoán chính, trừ khi logic khác
    appointment_id = models.IntegerField(
        _("appointment id"),
        unique=True,
        db_index=True,
        help_text=_("ID of the Appointment from the Appointment Service")
    )
    # Lưu ID của Bệnh nhân và Bác sĩ (dữ liệu có thể lấy từ Appointment hoặc User service)
    patient_id = models.IntegerField(
        _("patient id"),
        db_index=True,
        help_text=_("ID of the Patient")
    )
    doctor_id = models.IntegerField(
        _("doctor id"),
        db_index=True,
        help_text=_("ID of the Doctor")
    )

    # Mã chẩn đoán theo ICD (tùy chọn)
    diagnosis_code = models.CharField(
        _("diagnosis code"),
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("ICD code, e.g., J06.9")
    )
    description = models.TextField(
        _("description"),
        help_text=_("Detailed diagnosis description and clinical notes.")
    )
    diagnosis_time = models.DateTimeField(
        _("diagnosis time"),
        auto_now_add=True, # Tự động ghi thời gian lúc tạo record
        help_text=_("Timestamp when the diagnosis was recorded.")
    )

    class Meta:
        verbose_name = _('diagnosis')
        verbose_name_plural = _('diagnoses')
        ordering = ['-diagnosis_time']

    def __str__(self):
        return f"Diagnosis for Appt ID {self.appointment_id} (Patient ID: {self.patient_id})"

# Model Đơn thuốc
class Prescription(models.Model):
    # Liên kết với Chẩn đoán
    diagnosis = models.ForeignKey(
        Diagnosis,
        on_delete=models.CASCADE, # Nếu xóa chẩn đoán, đơn thuốc liên quan cũng bị xóa
        related_name='prescriptions', # Từ Diagnosis -> prescriptions
        verbose_name=_("diagnosis")
    )
    # Có thể thêm thông tin patient_id, doctor_id ở đây để tiện truy vấn nếu cần
    # patient_id = models.IntegerField(db_index=True)
    # doctor_id = models.IntegerField(db_index=True)

    prescription_date = models.DateField(
        _("prescription date"),
        auto_now_add=True,
        db_index=True
    )
    notes = models.TextField(
        _("notes"),
        blank=True,
        null=True,
        help_text=_("Additional notes for the prescription or pharmacist.")
    )
    # Có thể thêm trạng thái (ví dụ: Mới, Đã cấp phát) nếu PharmacyService không quản lý

    class Meta:
        verbose_name = _('prescription')
        verbose_name_plural = _('prescriptions')
        ordering = ['-prescription_date']

    def __str__(self):
        return f"Prescription ID: {self.id} for Diagnosis ID: {self.diagnosis.id}"

# Model Chi tiết thuốc trong đơn
class PrescribedMedication(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='medications', # Từ Prescription -> medications
        verbose_name=_("prescription")
    )
    # Tên thuốc - Lý tưởng nên link đến một Catalog thuốc riêng (có thể ở PharmacyService)
    # Tạm thời lưu dạng text
    medication_name = models.CharField(_("medication name"), max_length=255)
    dosage = models.CharField(_("dosage"), max_length=100, help_text=_("e.g., '500mg', '1 tablet'"))
    frequency = models.CharField(_("frequency"), max_length=100, help_text=_("e.g., 'Twice a day', 'Every 6 hours'"))
    duration = models.CharField(_("duration"), max_length=100, help_text=_("e.g., '7 days', 'Until finished'"))
    instructions = models.TextField(
        _("instructions"),
        blank=True,
        null=True,
        help_text=_("Specific instructions for the patient.")
    )
    # quantity = models.PositiveIntegerField(null=True, blank=True) # Số lượng cấp phát

    class Meta:
        verbose_name = _('prescribed medication')
        verbose_name_plural = _('prescribed medications')

    def __str__(self):
        return f"{self.medication_name} ({self.dosage})"

# Model Yêu cầu Xét nghiệm
class LabOrder(models.Model):
    STATUS_ORDERED = 'Ordered'
    STATUS_RECEIVED = 'Received' # Phòng lab đã nhận mẫu/yêu cầu
    STATUS_PROCESSING = 'Processing'
    STATUS_COMPLETED = 'Completed' # Có kết quả
    STATUS_CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_ORDERED, _('Ordered')),
        (STATUS_RECEIVED, _('Received')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    # Có thể liên kết với Diagnosis hoặc trực tiếp với Appointment/Patient/Doctor
    diagnosis = models.ForeignKey(
        Diagnosis,
        on_delete=models.SET_NULL, # Không xóa LabOrder nếu Diagnosis bị xóa
        related_name='lab_orders',
        null=True,
        blank=True,
        verbose_name=_("diagnosis")
    )
    # Nên lưu ID của appointment, patient, doctor để truy vấn độc lập
    appointment_id = models.IntegerField(
        _("appointment id"),
        db_index=True,
        null=True, blank=True # Có thể không gắn với appointment cụ thể
    )
    patient_id = models.IntegerField(
        _("patient id"),
        db_index=True
    )
    doctor_id = models.IntegerField(
        _("doctor id"),
        db_index=True
    )

    # Tên xét nghiệm - Lý tưởng nên link đến Catalog xét nghiệm riêng
    test_name = models.CharField(_("test name"), max_length=255)
    order_time = models.DateTimeField(_("order time"), auto_now_add=True, db_index=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ORDERED,
        db_index=True
    )
    # Trường lưu kết quả (có thể là text, link file, hoặc ID kết quả từ LabService)
    # result_text = models.TextField(blank=True, null=True)
    # result_file_url = models.URLField(blank=True, null=True)
    # lab_result_id = models.IntegerField(null=True, blank=True, db_index=True)

    notes = models.TextField(
        _("notes"),
        blank=True,
        null=True,
        help_text=_("Additional notes for the lab technician.")
    )


    class Meta:
        verbose_name = _('lab order')
        verbose_name_plural = _('lab orders')
        ordering = ['-order_time']

    def __str__(self):
        return f"Lab Order ID: {self.id} for Patient ID: {self.patient_id} - {self.test_name}"