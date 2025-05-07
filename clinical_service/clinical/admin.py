# clinical/admin.py
from django.contrib import admin
from .models import Diagnosis, Prescription, PrescribedMedication, LabOrder

# Inline admin cho PrescribedMedication để hiển thị trong Prescription
class PrescribedMedicationInline(admin.TabularInline): # TabularInline hiển thị dạng bảng
    model = PrescribedMedication
    extra = 1 # Số lượng dòng trống để thêm mới
    fields = ('medication_name', 'dosage', 'frequency', 'duration', 'instructions')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'diagnosis_id', 'prescription_date', 'get_patient_id', 'get_doctor_id') # Thêm hàm lấy ID BN, BS
    list_filter = ('prescription_date',)
    search_fields = ('diagnosis__appointment_id', 'diagnosis__patient_id', 'diagnosis__doctor_id') # Tìm theo ID liên quan từ Diagnosis
    inlines = [PrescribedMedicationInline] # Hiển thị chi tiết thuốc inline

    @admin.display(description='Patient ID')
    def get_patient_id(self, obj):
        return obj.diagnosis.patient_id

    @admin.display(description='Doctor ID')
    def get_doctor_id(self, obj):
        return obj.diagnosis.doctor_id

# Inline admin cho Prescription và LabOrder để hiển thị trong Diagnosis
class PrescriptionInline(admin.StackedInline): # StackedInline hiển thị dạng khối
    model = Prescription
    extra = 0 # Không hiển thị dòng trống vì thường tạo đơn riêng
    readonly_fields = ('prescription_date', 'notes') # Chỉ đọc ở đây
    can_delete = False
    show_change_link = True # Cho phép click để đến trang chỉnh sửa Prescription

class LabOrderInline(admin.TabularInline):
    model = LabOrder
    extra = 0
    fields = ('test_name', 'status', 'order_time')
    readonly_fields = ('order_time',)
    can_delete = False
    show_change_link = True

@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'patient_id', 'doctor_id', 'diagnosis_code', 'diagnosis_time')
    list_filter = ('diagnosis_time', 'doctor_id')
    search_fields = ('appointment_id', 'patient_id', 'doctor_id', 'diagnosis_code', 'description')
    inlines = [PrescriptionInline, LabOrderInline] # Hiển thị Đơn thuốc và Yêu cầu XN inline
    readonly_fields = ('diagnosis_time',)

@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment_id', 'patient_id', 'doctor_id', 'test_name', 'status', 'order_time')
    list_filter = ('status', 'test_name', 'doctor_id')
    search_fields = ('appointment_id', 'patient_id', 'doctor_id', 'test_name')
    list_editable = ('status',) # Cho phép sửa status từ danh sách
    readonly_fields = ('order_time',)

# Không cần đăng ký PrescribedMedication riêng vì đã inline