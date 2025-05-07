# clinical/views.py
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Diagnosis, Prescription, LabOrder, PrescribedMedication
from .serializers import (
    DiagnosisSerializer,
    DiagnosisCreateSerializer,
    PrescriptionSerializer,
    PrescriptionCreateSerializer,
    LabOrderSerializer,
    LabOrderCreateSerializer,
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser # Import permissions
from .permissions import IsAdminClaim, IsDoctorClaim, IsPatientClaim
from rest_framework.permissions import IsAuthenticated

# --- View Tạo Chẩn đoán mới ---
class DiagnosisCreateView(generics.CreateAPIView):
    """
    API tạo một Chẩn đoán mới.
    Yêu cầu quyền Bác sĩ (hoặc Admin).
    """
    serializer_class = DiagnosisCreateSerializer
    # permission_classes = [IsAuthenticated, IsDoctorPermission] # Cần Custom Permission
    permission_classes = [IsAuthenticated, IsDoctorClaim] # Tạm thời chỉ cho Admin

    def perform_create(self, serializer):
        # Giả định doctor_id lấy từ user đang request
        # Cần cơ chế xác định user là Doctor và lấy ID của họ
        # patient_id có thể lấy từ appointment_id (cần gọi service khác hoặc giả định)
        serializer.save(doctor_id=self.request.user.id) # Tạm gán ID user hiện tại là doctor

# --- View Tạo Đơn thuốc mới ---
class PrescriptionCreateView(generics.CreateAPIView):
    """
    API tạo một Đơn thuốc mới (kèm chi tiết thuốc).
    Yêu cầu quyền Bác sĩ (hoặc Admin).
    """
    serializer_class = PrescriptionCreateSerializer
    # permission_classes = [IsAuthenticated, IsDoctorPermission]
    permission_classes = [IsAuthenticated, IsDoctorClaim]

    def perform_create(self, serializer):
        # --- Placeholder for Inter-service Communication ---
        prescription = serializer.save()
        print(f"--- Gửi sự kiện 'prescription_created' vào Message Queue ---")
        print(f"--- Dữ liệu: prescription_id={prescription.id}, diagnosis_id={prescription.diagnosis.id} ---")
        # Ví dụ: publish_event('prescription_created', {'prescription_id': prescription.id, ...})

# --- View Tạo Yêu cầu Xét nghiệm mới ---
class LabOrderCreateView(generics.CreateAPIView):
    """
    API tạo một Yêu cầu Xét nghiệm mới.
    Yêu cầu quyền Bác sĩ (hoặc Admin).
    """
    serializer_class = LabOrderCreateSerializer
    # permission_classes = [IsAuthenticated, IsDoctorPermission]
    permission_classes = [IsAuthenticated, IsDoctorClaim]

    def perform_create(self, serializer):
        # Giả định doctor_id và patient_id lấy từ context hoặc payload đã validate
        lab_order = serializer.save(doctor_id=self.request.user.id) # Tạm gán ID user hiện tại là doctor
        # --- Placeholder for Inter-service Communication ---
        print(f"--- Gửi sự kiện 'lab_order_created' vào Message Queue ---")
        print(f"--- Dữ liệu: lab_order_id={lab_order.id}, patient_id={lab_order.patient_id}, test_name={lab_order.test_name} ---")
        # Ví dụ: publish_event('lab_order_created', {'lab_order_id': lab_order.id, ...})

# --- View Lấy Tóm tắt EHR của Bệnh nhân ---
class PatientEHRView(views.APIView):
    """
    API lấy tóm tắt Hồ sơ sức khỏe điện tử (EHR) của một bệnh nhân.
    Yêu cầu quyền Admin hoặc Bác sĩ liên quan hoặc chính Bệnh nhân đó.
    """
    # Permission này cần phức tạp hơn: IsOwner (Patient) OR IsAssociatedDoctor OR IsAdminClaim
    # Tạm thời:
    permission_classes = [IsAuthenticated] # Sẽ cần kiểm tra patient_id với user.id hoặc user là doctor/admin
    # Ví dụ kiểm tra trong hàm get:
    # def get(self, request, patient_id, format=None):
    #     user = request.user
    #     is_owner = (str(user.get('user_id')) == str(patient_id) and 'Patient' in user.get('roles', []))
    #     is_doctor_associated = # (logic kiểm tra bác sĩ có liên quan đến patient_id này không)
    #     is_admin = user.get('is_staff', False)
    #     if not (is_owner or is_doctor_associated or is_admin):
    #         return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    def get(self, request, patient_id, format=None):
        # Kiểm tra quyền truy cập ở đây nếu dùng permission phức tạp hơn

        # Lấy tất cả các chẩn đoán của bệnh nhân
        diagnoses = Diagnosis.objects.filter(patient_id=patient_id).prefetch_related(
            'prescriptions__medications', # Prefetch sâu để lấy cả thuốc
            'lab_orders'
        ).order_by('-diagnosis_time')

        if not diagnoses.exists():
            return Response({"detail": "No clinical records found for this patient."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize dữ liệu chẩn đoán (đã bao gồm đơn thuốc và xét nghiệm lồng nhau)
        serializer = DiagnosisSerializer(diagnoses, many=True)

        # Trong thực tế, có thể cần tổng hợp thêm thông tin từ các service khác
        # Ví dụ: gọi LabService để lấy kết quả chi tiết cho lab_orders

        return Response(serializer.data)

# --- (Tùy chọn) Thêm các ViewSet/Generic Views cho CRUD Diagnosis, Prescription, LabOrder ---
# class DiagnosisViewSet(viewsets.ReadOnlyModelViewSet): # Ví dụ chỉ cho đọc
#     queryset = Diagnosis.objects.all()
#     serializer_class = DiagnosisSerializer
#     permission_classes = [IsAdminUser] # Hoặc quyền phù hợp hơn