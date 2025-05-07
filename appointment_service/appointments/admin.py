# appointments/admin.py
from django.contrib import admin
from .models import DoctorSchedule, Appointment

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'start_time', 'end_time', 'is_available')
    list_filter = ('doctor_id', 'is_available')
    search_fields = ('doctor_id',)
    date_hierarchy = 'start_time' # Thêm bộ lọc nhanh theo ngày

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_id', 'doctor_id', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'doctor_id', 'patient_id')
    search_fields = ('patient_id', 'doctor_id', 'reason')
    list_editable = ('status',) # Cho phép sửa status trực tiếp từ danh sách
    date_hierarchy = 'appointment_time'
    raw_id_fields = ('schedule_slot',) # Hữu ích nếu có nhiều schedule slot
    readonly_fields = ('created_at', 'updated_at') # Không cho sửa các trường này

# Hoặc cách đăng ký đơn giản hơn:
# admin.site.register(DoctorSchedule)
# admin.site.register(Appointment)