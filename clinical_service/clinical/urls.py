# clinical/urls.py
from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from .views import (
    DiagnosisCreateView,
    PrescriptionCreateView,
    LabOrderCreateView,
    PatientEHRView,
    # DiagnosisViewSet, # Nếu dùng ViewSet
)

app_name = 'clinical'

# --- (Tùy chọn) Router cho ViewSets ---
# router = DefaultRouter()
# router.register(r'diagnoses', DiagnosisViewSet, basename='diagnosis')

urlpatterns = [
    path('diagnoses/create/', DiagnosisCreateView.as_view(), name='diagnosis-create'),
    path('prescriptions/create/', PrescriptionCreateView.as_view(), name='prescription-create'),
    path('lab-orders/create/', LabOrderCreateView.as_view(), name='laborder-create'),
    # URL để lấy EHR theo ID bệnh nhân
    path('ehr/patient/<int:patient_id>/', PatientEHRView.as_view(), name='patient-ehr'),

    # Include router URLs nếu dùng ViewSet
    # path('', include(router.urls)),
]