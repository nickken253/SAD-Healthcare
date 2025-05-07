# clinical/serializers.py
from rest_framework import serializers
from .models import Diagnosis, Prescription, PrescribedMedication, LabOrder

# --- Serializer cho Chi tiết Thuốc trong Đơn (để lồng) ---
class PrescribedMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescribedMedication
        # Không cần 'prescription' vì nó sẽ được lồng vào PrescriptionSerializer
        fields = ['id', 'medication_name', 'dosage', 'frequency', 'duration', 'instructions']
        read_only_fields = ('id',)

# --- Serializer cho Đơn thuốc (để đọc, có thể lồng chi tiết thuốc) ---
class PrescriptionSerializer(serializers.ModelSerializer):
    # Lồng danh sách các thuốc đã kê
    medications = PrescribedMedicationSerializer(many=True, read_only=True)
    # Có thể thêm các trường ID để tham chiếu nếu cần
    # diagnosis_id = serializers.IntegerField(source='diagnosis.id', read_only=True)
    # patient_id = serializers.IntegerField(source='diagnosis.patient_id', read_only=True)
    # doctor_id = serializers.IntegerField(source='diagnosis.doctor_id', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'diagnosis', # Hiển thị ID của diagnosis liên quan
            'prescription_date',
            'notes',
            'medications', # Danh sách thuốc lồng vào
            # 'diagnosis_id',
            # 'patient_id',
            # 'doctor_id',
        ]
        read_only_fields = ('id', 'prescription_date', 'medications')

# --- Serializer cho Yêu cầu Xét nghiệm (để đọc) ---
class LabOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrder
        fields = [
            'id',
            'diagnosis', # ID của diagnosis liên quan (nếu có)
            'appointment_id',
            'patient_id',
            'doctor_id',
            'test_name',
            'order_time',
            'status',
            'notes',
            # Thêm các trường kết quả nếu có trong model
            # 'result_text',
            # 'result_file_url',
        ]
        read_only_fields = ('id', 'order_time')

# --- Serializer cho Chẩn đoán (để đọc, có thể lồng đơn thuốc, xét nghiệm) ---
class DiagnosisSerializer(serializers.ModelSerializer):
    # Lồng các đơn thuốc và yêu cầu xét nghiệm liên quan
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    lab_orders = LabOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Diagnosis
        fields = [
            'id',
            'appointment_id',
            'patient_id',
            'doctor_id',
            'diagnosis_code',
            'description',
            'diagnosis_time',
            'prescriptions', # Danh sách đơn thuốc lồng vào
            'lab_orders',    # Danh sách yêu cầu xét nghiệm lồng vào
        ]
        read_only_fields = ('id', 'diagnosis_time', 'prescriptions', 'lab_orders')

# --- Serializer riêng cho việc TẠO Chẩn đoán ---
class DiagnosisCreateSerializer(serializers.ModelSerializer):
    # Giả định appointment_id, patient_id, doctor_id được cung cấp hoặc lấy từ context/appointment
    class Meta:
        model = Diagnosis
        fields = [
            'appointment_id',
            'patient_id',    # Có thể lấy từ context nếu liên kết với request user là bác sĩ
            'doctor_id',     # Có thể lấy từ context nếu request user là bác sĩ
            'diagnosis_code',
            'description',
        ]
        # diagnosis_time tự động được tạo

    def validate_appointment_id(self, value):
        """Kiểm tra xem appointment_id đã có chẩn đoán chưa."""
        if Diagnosis.objects.filter(appointment_id=value).exists():
            raise serializers.ValidationError(f"Diagnosis for appointment ID {value} already exists.")
        # TODO: Có thể cần gọi AppointmentService để kiểm tra appointment_id tồn tại và lấy patient_id, doctor_id?
        # Hoặc giả định dữ liệu này được truyền vào đáng tin cậy.
        return value

    # Không cần ghi đè create() nếu logic đơn giản

# --- Serializer riêng cho việc TẠO Đơn thuốc (nhận cả danh sách thuốc) ---
class PrescriptionCreateSerializer(serializers.ModelSerializer):
    # Nhận một danh sách các object thuốc để tạo PrescribedMedication
    medications = PrescribedMedicationSerializer(many=True)
    # Client cần gửi diagnosis (ID của Diagnosis đã tạo)
    diagnosis = serializers.PrimaryKeyRelatedField(queryset=Diagnosis.objects.all())

    class Meta:
        model = Prescription
        fields = [
            'diagnosis',
            'notes',
            'medications', # Danh sách các thuốc cần tạo
        ]
        # prescription_date tự động tạo

    def create(self, validated_data):
        # Tách dữ liệu medications ra khỏi validated_data
        medications_data = validated_data.pop('medications')
        # Tạo đối tượng Prescription trước
        prescription = Prescription.objects.create(**validated_data)
        # Tạo các đối tượng PrescribedMedication liên quan
        for medication_data in medications_data:
            PrescribedMedication.objects.create(prescription=prescription, **medication_data)
        return prescription

# --- Serializer riêng cho việc TẠO Yêu cầu Xét nghiệm ---
class LabOrderCreateSerializer(serializers.ModelSerializer):
    # Có thể liên kết với diagnosis hoặc không
    diagnosis = serializers.PrimaryKeyRelatedField(queryset=Diagnosis.objects.all(), required=False, allow_null=True)

    class Meta:
        model = LabOrder
        fields = [
            'diagnosis',      # ID chẩn đoán (tùy chọn)
            'appointment_id', # ID lịch hẹn (tùy chọn)
            'patient_id',     # ID bệnh nhân (bắt buộc) - Lấy từ context/diagnosis/appointment
            'doctor_id',      # ID bác sĩ (bắt buộc) - Lấy từ context
            'test_name',      # Tên xét nghiệm (bắt buộc)
            'notes',          # Ghi chú (tùy chọn)
        ]
        # order_time, status tự động/mặc định

    # Không cần ghi đè create() nếu logic đơn giản