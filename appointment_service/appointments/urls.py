# appointments/urls.py
from django.urls import path
from .views import (
    DoctorScheduleListView,
    AppointmentCreateView,
    PatientAppointmentListView,
    DoctorAppointmentListView,
    AppointmentDetailView,
    # AvailableSlotsView, # Sẽ thêm view này nếu cần logic phức tạp hơn
)

app_name = 'appointments'

urlpatterns = [
    # Lịch làm việc của bác sĩ
    path('schedules/', DoctorScheduleListView.as_view(), name='doctor-schedule-list'),
    # path('available-slots/', AvailableSlotsView.as_view(), name='available-slots'), # URL cho xem slot trống

    # Quản lý lịch hẹn
    path('book/', AppointmentCreateView.as_view(), name='appointment-create'),
    path('my-appointments/', PatientAppointmentListView.as_view(), name='patient-appointment-list'),
    path('doctor-appointments/', DoctorAppointmentListView.as_view(), name='doctor-appointment-list'), # Cần ?doctor_id=...
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'), # Xem chi tiết, cập nhật status, hủy
]