# -*- coding: utf-8 -*-
import json
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import os
import re

# --- Biến toàn cục ---
intent_model = None
symptom_model = None # Sẽ là model_filtered
tokenizer = None
lbl_encoder = None # Intent encoder
symptom_encoder = None # Symptom encoder (EN - Filtered)
responses_dict = None
symptom_names = None # List symptom names (EN - Filtered/Relevant)
disease_names_vi = None # List disease names (VI - Filtered)
symptom_translation_vi = {} # Dictionary dịch triệu chứng
max_len = 20
INTENT_CONFIDENCE_THRESHOLD = 0.65
AFFIRMATIVE_WORDS = ['y', 'yes', 'có', 'vâng', 'đồng ý', 'ừ', 'được', 'đúng', 'chắc chắn', 'uh', 'co']
NEGATIVE_WORDS = ['n', 'no', 'không', 'ko', 'thôi', 'dừng', 'không đồng ý', 'sai', 'đừng', 'nope', 'hủy', 'khong']


# --- Bản đồ dịch triệu chứng Anh-Việt (Cần khớp với relevant_symptom_names_filtered.json) ---
# (Copy lại hoặc định nghĩa dictionary symptom_translation_vi_map đầy đủ ở đây)
symptom_translation_vi_map = {
    'itching': 'Ngứa', 'skin_rash': 'Phát ban da', 'nodal_skin_eruptions': 'Nốt sẩn trên da',
    'continuous_sneezing': 'Hắt hơi liên tục', 'shivering': 'Run rẩy', 'chills': 'Ớn lạnh',
    'joint_pain': 'Đau khớp', 'stomach_pain': 'Đau bụng/dạ dày', 'acidity': 'Ợ chua/Axít dạ dày',
    'ulcers_on_tongue': 'Loét lưỡi', 'muscle_wasting': 'Teo cơ', 'vomiting': 'Nôn/Ói',
    'burning_micturition': 'Tiểu buốt/rát', 'spotting_ urination': 'Tiểu rắt/lắt nhắt',
    'fatigue': 'Mệt mỏi', 'weight_gain': 'Tăng cân', 'anxiety': 'Lo lắng',
    'cold_hands_and_feets': 'Lạnh tay chân', 'mood_swings': 'Thay đổi tâm trạng',
    'weight_loss': 'Sụt cân', 'restlessness': 'Bồn chồn', 'lethargy': 'Hôn mê/Lờ đờ',
    'patches_in_throat': 'Mảng trong họng', 'irregular_sugar_level': 'Đường huyết không đều',
    'cough': 'Ho', 'high_fever': 'Sốt cao', 'sunken_eyes': 'Mắt trũng', 'breathlessness': 'Khó thở',
    'sweating': 'Đổ mồ hôi', 'dehydration': 'Mất nước', 'indigestion': 'Khó tiêu',
    'headache': 'Nhức đầu/Đau đầu', 'yellowish_skin': 'Vàng da', 'dark_urine': 'Nước tiểu sẫm màu',
    'nausea': 'Buồn nôn', 'loss_of_appetite': 'Chán ăn', 'pain_behind_the_eyes': 'Đau sau mắt',
    'back_pain': 'Đau lưng', 'constipation': 'Táo bón', 'abdominal_pain': 'Đau bụng',
    'diarrhoea': 'Tiêu chảy', 'mild_fever': 'Sốt nhẹ', 'yellow_urine': 'Nước tiểu vàng',
    'yellowing_of_eyes': 'Vàng mắt', 'acute_liver_failure': 'Suy gan cấp', 'fluid_overload': 'Quá tải dịch',
    'swelling_of_stomach': 'Sưng bụng', 'swelled_lymph_nodes': 'Sưng hạch bạch huyết',
    'malaise': 'Khó chịu/Uể oải', 'blurred_and_distorted_vision': 'Nhìn mờ và méo',
    'phlegm': 'Đờm', 'throat_irritation': 'Ngứa họng/Rát họng', 'redness_of_eyes': 'Đỏ mắt',
    'sinus_pressure': 'Viêm xoang/Nặng xoang', 'runny_nose': 'Sổ mũi/Chảy nước mũi',
    'congestion': 'Nghẹt mũi', 'chest_pain': 'Đau ngực', 'weakness_in_limbs': 'Yếu chi',
    'fast_heart_rate': 'Nhịp tim nhanh', 'pain_during_bowel_movements': 'Đau khi đi ngoài',
    'pain_in_anal_region': 'Đau vùng hậu môn', 'bloody_stool': 'Phân có máu', 'irritation_in_anus': 'Ngứa/rát hậu môn',
    'neck_pain': 'Đau cổ', 'dizziness': 'Chóng mặt', 'cramps': 'Chuột rút', 'bruising': 'Bầm tím', 'obesity': 'Béo phì',
    'swollen_legs': 'Sưng chân', 'swollen_blood_vessels': 'Sưng mạch máu', 'puffy_face_and_eyes': 'Mặt và mắt sưng húp',
    'enlarged_thyroid': 'Tuyến giáp phì đại', 'brittle_nails': 'Móng giòn dễ gãy', 'swollen_extremeties': 'Sưng đầu chi',
    'excessive_hunger': 'Đói nhiều', 'extra_marital_contacts': 'Quan hệ ngoài hôn nhân',
    'drying_and_tingling_lips': 'Khô và ngứa môi', 'slurred_speech': 'Nói lắp/Nói khó',
    'knee_pain': 'Đau đầu gối', 'hip_joint_pain': 'Đau khớp háng', 'muscle_weakness': 'Yếu cơ',
    'stiff_neck': 'Cứng cổ', 'swelling_joints': 'Sưng khớp', 'movement_stiffness': 'Cứng khớp khi cử động',
    'spinning_movements': 'Cảm giác quay cuồng', 'loss_of_balance': 'Mất thăng bằng', 'unsteadiness': 'Đi không vững',
    'weakness_of_one_body_side': 'Yếu một bên cơ thể', 'loss_of_smell': 'Mất khứu giác',
    'bladder_discomfort': 'Khó chịu bàng quang', 'foul_smell_of urine': 'Nước tiểu có mùi hôi',
    'continuous_feel_of_urine': 'Buồn tiểu liên tục', 'passage_of_gases': 'Xì hơi/Trung tiện',
    'internal_itching': 'Ngứa trong', 'toxic_look_(typhos)': 'Vẻ mặt nhiễm độc',
    'depression': 'Trầm cảm', 'irritability': 'Cáu gắt', 'muscle_pain': 'Đau cơ',
    'altered_sensorium': 'Rối loạn tri giác', 'red_spots_over_body': 'Đốm đỏ khắp người', 'belly_pain': 'Đau bụng (vùng bụng)',
    'abnormal_menstruation': 'Kinh nguyệt bất thường', 'dischromic _patches': 'Mảng đổi màu da',
    'watering_from_eyes': 'Chảy nước mắt', 'increased_appetite': 'Tăng cảm giác thèm ăn',
    'polyuria': 'Đa niệu (Tiểu nhiều)', 'family_history': 'Tiền sử gia đình', 'mucoid_sputum': 'Đờm nhầy',
    'rusty_sputum': 'Đờm gỉ sét', 'lack_of_concentration': 'Thiếu tập trung', 'visual_disturbances': 'Rối loạn thị giác',
    'receiving_blood_transfusion': 'Nhận truyền máu', 'receiving_unsterile_injections': 'Tiêm không vô trùng',
    'coma': 'Hôn mê', 'stomach_bleeding': 'Chảy máu dạ dày', 'distention_of_abdomen': 'Chướng bụng',
    'history_of_alcohol_consumption': 'Tiền sử nghiện rượu', 'fluid_overload.1': 'Quá tải dịch',
    'blood_in_sputum': 'Ho ra máu', 'prominent_veins_on_calf': 'Nổi rõ tĩnh mạch ở bắp chân',
    'palpitations': 'Hồi hộp/Đánh trống ngực', 'painful_walking': 'Đau khi đi lại', 'pus_filled_pimples': 'Mụn mủ',
    'blackheads': 'Mụn đầu đen', 'scurring': 'Sẹo', 'skin_peeling': 'Bong da', 'silver_like_dusting': 'Vảy bạc như bụi phấn',
    'small_dents_in_nails': 'Móng có vết lõm nhỏ', 'inflammatory_nails': 'Viêm móng', 'blister': 'Phồng rộp',
    'red_sore_around_nose': 'Vết loét đỏ quanh mũi', 'yellow_crust_ooze': 'Chảy dịch vàng đóng vảy'
}

# --- CÂY QUYẾT ĐỊNH HỎI TRIỆU CHỨNG (MỞ RỘNG HƠN - VẪN LÀ VÍ DỤ) ---
# !!! CẢNH BÁO: Logic chỉ để demo kỹ thuật, KHÔNG chính xác về y khoa !!!
SYMPTOM_QUESTIONING_TREE = {
    "START": {
        "question_vi": "Để giúp tôi hiểu rõ hơn, bạn có bị sốt không?",
        "symptom_key": "high_fever", # Key tiếng Anh khớp với symptom_names
        "yes_next": "fever_yes_ask_cough",
        "no_next": "fever_no_ask_respiratory"
    },
    # Nhánh có Sốt
    "fever_yes_ask_cough": {
        "question_vi": "Bạn có bị ho không?",
        "symptom_key": "cough",
        "yes_next": "fever_cough_yes_ask_breath",
        "no_next": "fever_cough_no_ask_headache"
    },
    "fever_cough_yes_ask_breath": {
        "question_vi": "Bạn có cảm thấy khó thở hoặc đau ngực không?",
        "symptom_key": "breathlessness", # Key chính
        "yes_next": "PREDICT", # Sốt, Ho, Khó thở -> Viêm phổi? -> Dự đoán
        "no_next": "fever_cough_yes_no_breath_ask_phlegm"
    },
    "fever_cough_yes_no_breath_ask_phlegm": {
         "question_vi": "Khi ho bạn có ra đờm không?",
         "symptom_key": "phlegm",
         "yes_next": "PREDICT", # Sốt, Ho, Đờm -> Viêm phế quản/phổi -> Dự đoán
         "no_next": "PREDICT" # Sốt, Ho khan -> Cúm/Covid/Cảm -> Dự đoán
     },
    "fever_cough_no_ask_headache": {
        "question_vi": "Bạn có bị nhức đầu không?",
        "symptom_key": "headache",
        "yes_next": "fever_no_cough_headache_yes_ask_chills",
        "no_next": "fever_no_cough_headache_no_ask_abdominal"
    },
    "fever_no_cough_headache_yes_ask_chills":{
         "question_vi": "Bạn có cảm thấy ớn lạnh hoặc run rẩy không?",
         "symptom_key": "chills",
         "yes_next": "PREDICT", # Sốt, Đau đầu, Lạnh -> Cúm/Sốt virus -> Dự đoán
         "no_next": "PREDICT"
     },
    "fever_no_cough_headache_no_ask_abdominal":{
          "question_vi": "Bạn có bị đau bụng không?",
          "symptom_key": "abdominal_pain",
          "yes_next": "fever_no_cough_no_headache_abdominal_yes_ask_vomit",
          "no_next": "PREDICT" # Chỉ sốt -> Dự đoán
      },
    "fever_no_cough_no_headache_abdominal_yes_ask_vomit":{
           "question_vi": "Bạn có bị nôn/buồn nôn không?",
           "symptom_key": "nausea",
           "yes_next": "PREDICT", # Sốt, Đau bụng, Nôn -> Viêm dạ dày ruột -> Dự đoán
           "no_next": "PREDICT" # Sốt, Đau bụng -> Dự đoán
       },
    # Nhánh KHÔNG Sốt
    "fever_no_ask_respiratory": {
        "question_vi": "Bạn có triệu chứng hô hấp như ho, hắt hơi, sổ mũi không?",
        "symptom_key": "cough", # Dùng ho làm đại diện
        "yes_next": "fever_no_resp_yes_ask_sneezing",
        "no_next": "fever_no_resp_no_ask_digestive"
    },
    "fever_no_resp_yes_ask_sneezing": {
         "question_vi": "Bạn có bị hắt hơi liên tục hoặc chảy nước mũi nhiều không?",
         "symptom_key": "continuous_sneezing",
         "yes_next": "fever_no_resp_sneezing_yes_ask_itching",
         "no_next": "fever_no_resp_sneezing_no_ask_breath"
     },
    "fever_no_resp_sneezing_yes_ask_itching": {
          "question_vi": "Bạn có cảm thấy ngứa (mắt, mũi, da) kèm theo không?",
          "symptom_key": "itching",
          "yes_next": "PREDICT", # Không sốt, Hắt hơi, Ngứa -> DỊ ỨNG -> Dự đoán
          "no_next": "PREDICT"   # Không sốt, Hắt hơi, Không ngứa -> CẢM LẠNH -> Dự đoán
      },
     "fever_no_resp_sneezing_no_ask_breath": {
           "question_vi": "Bạn có bị khó thở, khò khè không?",
           "symptom_key": "breathlessness",
           "yes_next": "PREDICT", # Không sốt, Ho, Khó thở -> HEN PHẾ QUẢN -> Dự đoán
           "no_next": "PREDICT"   # Không sốt, Ho đơn thuần -> Cảm lạnh? -> Dự đoán
       },
    "fever_no_resp_no_ask_digestive": {
        "question_vi": "Vậy bạn có gặp vấn đề về tiêu hóa như đau bụng, ợ chua, buồn nôn, nôn, tiêu chảy không?",
        "symptom_key": "abdominal_pain",
        "yes_next": "fever_no_resp_no_digestive_yes_ask_acidity",
        "no_next": "STOP" # Ngoài phạm vi
    },
    "fever_no_resp_no_digestive_yes_ask_acidity": {
         "question_vi": "Bạn có thường bị ợ chua hoặc đau vùng dạ dày không?",
         "symptom_key": "acidity", # Hoặc stomach_pain
         "yes_next": "PREDICT", # Thiên về GERD -> Dự đoán
         "no_next": "fever_no_resp_no_digestive_yes_no_acidity_ask_diarrhea"
     },
    "fever_no_resp_no_digestive_yes_no_acidity_ask_diarrhea": {
          "question_vi": "Bạn có bị tiêu chảy hoặc nôn/buồn nôn không?",
          "symptom_key": "diarrhoea", # Hoặc vomiting, nausea
          "yes_next": "PREDICT", # Thiên về VIÊM DẠ DÀY RUỘT -> Dự đoán
          "no_next": "PREDICT" # Chỉ đau bụng? -> Dự đoán
      }
}


# --- Hàm tải tài nguyên ---
def load_resources(artifact_dir='.'):
    """Tải tất cả models và các file phụ trợ cần thiết (phiên bản filtered)."""
    global intent_model, symptom_model, tokenizer, lbl_encoder, symptom_encoder
    global responses_dict, symptom_names, disease_names_vi, max_len, symptom_translation_vi, SYMPTOM_QUESTIONING_TREE

    if intent_model is not None:
        print("Tài nguyên đã được tải trước đó.")
        return

    print(f"Bắt đầu tải tài nguyên từ: {artifact_dir}")
    symptom_translation_vi = symptom_translation_vi_map # Gán bản đồ dịch

    # Đường dẫn file
    intent_model_path = os.path.join(artifact_dir, "intent_chatbot_model.keras")
    symptom_model_path = os.path.join(artifact_dir, "symptom_checker_model_filtered.keras")
    tokenizer_path = os.path.join(artifact_dir, "tokenizer.pickle")
    intent_encoder_path = os.path.join(artifact_dir, "label_encoder.pickle")
    symptom_encoder_path = os.path.join(artifact_dir, "symptom_label_encoder_filtered_EN.pickle")
    intents_file_path = os.path.join(artifact_dir, "intents.json")
    symptom_names_path = os.path.join(artifact_dir, "relevant_symptom_names_filtered.json")
    disease_names_vi_path = os.path.join(artifact_dir, "disease_names_filtered_vi.json")

    # Kiểm tra file
    required_files = [
        intents_file_path, intent_model_path, symptom_model_path, tokenizer_path,
        intent_encoder_path, symptom_encoder_path, symptom_names_path, disease_names_vi_path
    ]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        for f in missing_files: print(f"- Thiếu file: {f}")
        raise FileNotFoundError("Thiếu các file cần thiết để khởi tạo chatbot core (filtered).")

    # Tải
    try:
        intent_model = load_model(intent_model_path, compile=False)
        symptom_model = load_model(symptom_model_path, compile=False)
        with open(tokenizer_path, 'rb') as handle: tokenizer = pickle.load(handle)
        with open(intent_encoder_path, 'rb') as ecn_file: lbl_encoder = pickle.load(ecn_file)
        with open(symptom_encoder_path, 'rb') as ecn_file_symptom: symptom_encoder = pickle.load(ecn_file_symptom)
        with open(intents_file_path, 'r', encoding='utf-8') as f: intents = json.load(f)
        with open(symptom_names_path, 'r', encoding='utf-8') as file: symptom_names = json.load(file) # Danh sách triệu chứng EN đã lọc
        with open(disease_names_vi_path, 'r', encoding='utf-8') as file: disease_names_vi = json.load(file) # Danh sách bệnh VI đã lọc

        responses_dict = {intent['tag']: intent['responses'] for intent in intents.get('intents', []) if 'tag' in intent and 'responses' in intent}
        if not responses_dict: raise ValueError("responses_dict trống.")

        # Lấy max_len
        if hasattr(intent_model, 'input_shape') and isinstance(intent_model.input_shape, tuple) and len(intent_model.input_shape) > 1:
             model_input_len = intent_model.input_shape[1]
             if model_input_len is not None:
                  max_len = model_input_len
             else: max_len = 20 # Fallback
        else: max_len = 20 # Fallback
        print(f"Intent model max_len: {max_len}")

        # Kiểm tra sự khớp giữa symptom_names và symptom_translation_vi_map
        for key in symptom_names:
            if key not in symptom_translation_vi:
                print(f"Cảnh báo: Triệu chứng '{key}' có trong symptom_names nhưng thiếu trong bản đồ dịch.")
        for key_tree in SYMPTOM_QUESTIONING_TREE:
             node = SYMPTOM_QUESTIONING_TREE[key_tree]
             s_key = node.get('symptom_key')
             if s_key and s_key not in symptom_names and s_key not in ["pain_general", "pain_location_detail", "logic_node"]: # Bỏ qua key ảo
                  print(f"Cảnh báo: symptom_key '{s_key}' trong cây không có trong symptom_names đã tải.")
             if s_key and s_key not in symptom_translation_vi_map and s_key not in ["pain_general", "pain_location_detail", "logic_node"]:
                  print(f"Cảnh báo: symptom_key '{s_key}' trong cây thiếu bản dịch tiếng Việt.")


        print("Tải thành công tất cả tài nguyên.")

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải tài nguyên: {e}")
        raise e

# --- Hàm xử lý chính ---

def predict_intent(text):
    """Dự đoán ý định từ text và trả về tag, confidence"""
    global tokenizer, intent_model, lbl_encoder, max_len, INTENT_CONFIDENCE_THRESHOLD
    if not all([tokenizer, intent_model, lbl_encoder]):
        raise ValueError("Chatbot core chưa được khởi tạo đầy đủ.")
    try:
        # Tiền xử lý cơ bản
        processed_text = text.lower().strip()
        if not processed_text: # Trả về unknown nếu input rỗng
            return "unknown", 0.0

        sequence = tokenizer.texts_to_sequences([processed_text])
        padded_sequence = pad_sequences(sequence, truncating='post', maxlen=max_len)
        result = intent_model.predict(padded_sequence, verbose=0)
        confidence = np.max(result)
        tag_index = np.argmax(result)

        # Kiểm tra ngưỡng tin cậy
        if confidence < INTENT_CONFIDENCE_THRESHOLD:
            print(f"DEBUG: Confidence ({confidence:.2f}) < Threshold ({INTENT_CONFIDENCE_THRESHOLD}). Treating as 'unknown'.")
            tag = "unknown"
        elif tag_index < 0 or tag_index >= len(lbl_encoder.classes_):
             print(f"Warning: Predicted index {tag_index} out of bounds.")
             tag = "unknown"
        else:
             tag = lbl_encoder.inverse_transform([tag_index])[0]
        return tag, confidence
    except Exception as e:
        print(f"Lỗi khi dự đoán intent cho '{text}': {e}")
        return "error", 0.0
    pass

def get_symptom_prediction(symptom_vector):
    """Dự đoán bệnh từ vector triệu chứng"""
    global symptom_model, disease_names_vi, symptom_names
    if not all([symptom_model, disease_names_vi, symptom_names]):
        raise ValueError("Symptom checker chưa được khởi tạo đầy đủ.")
    try:
        input_array = np.array([symptom_vector], dtype=np.float32)
        # Kiểm tra kích thước input
        expected_input_size = len(symptom_names)
        if symptom_model.input_shape[1] is not None: # Kiểm tra nếu model có input_shape cố định
             expected_input_size = symptom_model.input_shape[1]

        if input_array.shape[1] != expected_input_size:
             raise ValueError(f"Input shape không khớp: {input_array.shape[1]} vs {expected_input_size}")

        predictions = symptom_model.predict(input_array, verbose=0)
        sorted_indices = np.argsort(predictions[0])[::-1]

        results = []
        for i in range(min(5, len(disease_names_vi))): # Top 5
            idx = sorted_indices[i]
            results.append({"disease": disease_names_vi[idx], "probability": float(predictions[0][idx])})
        most_likely = disease_names_vi[sorted_indices[0]]
        return most_likely, results

    except Exception as e:
        print(f"Lỗi khi dự đoán triệu chứng: {e}")
        return "Lỗi dự đoán", []
    pass


# --- Quản lý trạng thái hỏi triệu chứng (Sửa đổi để dùng cây) ---
current_symptom_session = {
    "active": False,
    "symptom_vector": [], # Vector đầy đủ cho các triệu chứng trong symptom_names (đã lọc)
    "current_node_key": None # Key của nút/câu hỏi hiện tại trong cây
}

# --- Hàm Keyword Spotting Đơn Giản ---
def spot_keywords(text, keywords):
    """Tìm keywords trong text (phân tách từ đơn giản)"""
    found_keywords = set()
    # Tách từ bằng khoảng trắng và dấu câu cơ bản (có thể cải thiện bằng tokenizer tốt hơn)
    words = set(re.findall(r'\b\w+\b', text.lower()))
    for keyword in keywords:
        # Xử lý keyword (ví dụ: bỏ dấu gạch dưới)
        processed_keyword = keyword.replace('_', ' ').lower()
        # Kiểm tra xem keyword có trong tập các từ của text không
        # (Cách này đơn giản, có thể không chính xác với cụm từ)
        # Hoặc kiểm tra trực tiếp sự tồn tại của chuỗi con
        if processed_keyword in text.lower(): # Kiểm tra chuỗi con trực tiếp
             found_keywords.add(keyword)
        # Nâng cao hơn: tách processed_keyword thành các từ và kiểm tra sự tồn tại của tất cả các từ đó trong words
        # keyword_parts = set(processed_keyword.split())
        # if keyword_parts.issubset(words):
        #      found_keywords.add(keyword)

    return list(found_keywords)

import random
import json
import numpy as np
import re # Cần import re nếu chưa có

# --- Hàm chính: Generate Response (LOGIC CÂY QUYẾT ĐỊNH MỚI - Đã sửa Y/N check) ---
def generate_response(user_message, history):
    """Tạo phản hồi dựa trên tin nhắn mới, lịch sử và cây quyết định triệu chứng"""
    global responses_dict, symptom_names, current_symptom_session, disease_names_vi
    global SYMPTOM_QUESTIONING_TREE, symptom_translation_vi_map, INTENT_CONFIDENCE_THRESHOLD
    global AFFIRMATIVE_WORDS, NEGATIVE_WORDS

    # Tạo set từ list để kiểm tra nhanh hơn (nên làm một lần ngoài hàm nếu list không đổi)
    AFFIRMATIVE_SET = set(AFFIRMATIVE_WORDS)
    NEGATIVE_SET = set(NEGATIVE_WORDS)


    if not all([responses_dict, symptom_names, disease_names_vi, symptom_translation_vi_map]):
        return "Lỗi: Chatbot core chưa được khởi tạo đầy đủ."

    processed_user_message = user_message.lower().strip()
    # Mặc định là câu trả lời không rõ
    bot_response = random.choice(responses_dict.get("unknown", ["Xin lỗi, tôi chưa hiểu rõ ý bạn lắm."]))

    # --- ƯU TIÊN XỬ LÝ NẾU ĐANG TRONG LUỒNG HỎI TRIỆU CHỨNG ---
    if current_symptom_session.get("active"):
        current_node_key = current_symptom_session.get("current_node_key")

        # --- Sửa lỗi 1: Kiểm tra Y/N bằng cách tách từ và so sánh set ---
        processed_words = set(processed_user_message.split()) # Tách thành các từ
        is_affirmative = not processed_words.isdisjoint(AFFIRMATIVE_SET) # Kiểm tra xem có từ nào chung với set khẳng định không
        is_negative = not processed_words.isdisjoint(NEGATIVE_SET)   # Kiểm tra xem có từ nào chung với set phủ định không

        # Ưu tiên affirmative nếu cả hai đều khớp (ví dụ: "tôi không chắc có")
        if is_affirmative and is_negative:
            # Quy tắc đơn giản: nếu có từ khẳng định thì ưu tiên là khẳng định
            is_negative = False
            print("DEBUG: Detected both affirmative and negative keywords, prioritizing affirmative.")
        elif not is_affirmative and not is_negative:
             # Nếu không phải Y/N rõ ràng, thử kiểm tra intent xem có phải là 'stop', 'cancel'... không
             # (Giả sử bạn có các intent như 'goodbye', 'stop_symptoms', 'cancel' đã được huấn luyện)
             fallback_intent, fallback_confidence = predict_intent(user_message)
             # Thêm các intent hoặc từ khóa dừng khác nếu cần
             stop_keywords = {'dừng', 'thôi', 'hủy', 'stop', 'cancel'}
             is_stop_command = fallback_intent in ['goodbye', 'stop_symptoms', 'cancel'] or \
                               not processed_words.isdisjoint(stop_keywords)

             if is_stop_command:
                 print("DEBUG: User wants to stop symptom check.")
                 # Lấy câu trả lời từ intent 'cancel_symptoms' hoặc một câu mặc định
                 cancel_responses = responses_dict.get("cancel_symptoms", ["Được rồi, chúng ta sẽ dừng việc hỏi triệu chứng tại đây."])
                 bot_response = random.choice(cancel_responses)
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None} # Reset
                 return bot_response
             else:
                 # Nếu không phải Y/N và cũng không phải lệnh dừng -> Thoát luồng
                 print(f"DEBUG: User message '{processed_user_message}' not recognized as Y/N or stop command, exiting symptom flow.")
                 # Quan trọng: Reset trạng thái hỏi triệu chứng
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None}
                 # Lưu lại intent đã dự đoán để dùng bên dưới
                 intent_tag = fallback_intent
                 confidence = fallback_confidence
                 print(f"DEBUG: Fallback Intent='{intent_tag}', Confidence={confidence:.4f}")
                 # Fall through to intent handling below
                 pass # Sẽ nhảy xuống phần xử lý intent thông thường
        # --- Kết thúc Sửa lỗi 1 ---

        # Chỉ xử lý nếu đang chờ Y/N VÀ user trả lời Y/N rõ ràng
        # (is_affirmative hoặc is_negative là True)
        # Kiểm tra lại active vì có thể đã bị reset ở trên (trong trường hợp non-Y/N)
        if current_symptom_session.get("active") and (is_affirmative or is_negative):
             # --- Sửa lỗi 2: Đảm bảo current_node_key hợp lệ ---
             if not current_node_key or current_node_key not in SYMPTOM_QUESTIONING_TREE:
                 print(f"DEBUG: Lỗi logic - current_node_key không hợp lệ hoặc không có trong cây: '{current_node_key}'")
                 bot_response = "Đã có lỗi logic trong quá trình hỏi triệu chứng. Vui lòng bắt đầu lại."
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None}
                 return bot_response
             # --- Kết thúc Sửa lỗi 2 ---

             current_node_info = SYMPTOM_QUESTIONING_TREE.get(current_node_key)

             # Kiểm tra lại node info (dù đã check key ở trên)
             if not current_node_info: # Trường hợp hiếm gặp
                 print(f"DEBUG: Lỗi cây quyết định - không tìm thấy thông tin node '{current_node_key}' dù key tồn tại.")
                 bot_response = "Đã có lỗi logic trong cây hỏi triệu chứng. Vui lòng bắt đầu lại."
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None}
                 return bot_response

             symptom_key_just_asked = current_node_info.get('symptom_key')

             # Cập nhật symptom_vector nếu symptom_key hợp lệ
             if symptom_key_just_asked and symptom_key_just_asked in symptom_names:
                 try:
                     symptom_index = symptom_names.index(symptom_key_just_asked)
                     # Đảm bảo vector có đúng kích thước trước khi gán
                     if len(current_symptom_session.get("symptom_vector", [])) == len(symptom_names):
                         current_symptom_session["symptom_vector"][symptom_index] = 1.0 if is_affirmative else 0.0
                         print(f"DEBUG: Updated vector for {symptom_key_just_asked} = {current_symptom_session['symptom_vector'][symptom_index]}")
                     else:
                         print(f"DEBUG: Lỗi kích thước symptom_vector khi cập nhật {symptom_key_just_asked}. Vector size: {len(current_symptom_session.get('symptom_vector', []))}, Expected: {len(symptom_names)}")
                         # Khởi tạo lại vector nếu có lỗi? Hoặc báo lỗi và dừng.
                         # current_symptom_session["symptom_vector"] = [0.0] * len(symptom_names) # Tùy chọn: reset vector
                         # current_symptom_session["symptom_vector"][symptom_index] = 1.0 if is_affirmative else 0.0

                 except ValueError:
                      print(f"DEBUG: Lỗi - symptom_key '{symptom_key_just_asked}' có trong node nhưng không tìm thấy trong symptom_names list?")
             elif symptom_key_just_asked and "general" not in symptom_key_just_asked and "detail" not in symptom_key_just_asked: # Bỏ qua key ảo
                 print(f"DEBUG: Cảnh báo - symptom_key '{symptom_key_just_asked}' từ cây không có trong symptom_names (filtered).")

             # Xác định node tiếp theo
             next_node_key = current_node_info.get('yes_next' if is_affirmative else 'no_next')

             # --- Xử lý node tiếp theo ---
             if next_node_key == 'PREDICT':
                 print(f"DEBUG: Reached end state ({current_node_key} -> {('Yes' if is_affirmative else 'No')} -> PREDICT), predicting...")
                 # Đảm bảo vector hợp lệ trước khi dự đoán
                 if len(current_symptom_session.get("symptom_vector", [])) == len(symptom_names):
                     most_likely, results_list = get_symptom_prediction(current_symptom_session["symptom_vector"])

                     # --- BẮT ĐẦU THAY ĐỔI ĐỊNH DẠNG OUTPUT ---

                     response_lines = [] # Bắt đầu list mới cho các dòng output

                     # 1. Tiêu đề
                     response_lines.append("**Kết quả gợi ý (Chỉ mang tính tham khảo)**")
                     response_lines.append("---") # Dòng kẻ ngang phân cách

                     # 2. (Tùy chọn) Tóm tắt triệu chứng đã xác nhận
                     confirmed_symptoms_vi = []
                     symptom_vector = current_symptom_session.get("symptom_vector", [])
                     # Lặp qua vector triệu chứng để tìm các triệu chứng được xác nhận (giá trị = 1.0)
                     for index, value in enumerate(symptom_vector):
                         if value == 1.0 and index < len(symptom_names):
                             symptom_key_en = symptom_names[index]
                             # Lấy tên tiếng Việt từ bản đồ dịch, nếu không có thì dùng key tiếng Anh
                             symptom_name_vi = symptom_translation_vi_map.get(symptom_key_en, symptom_key_en.replace('_', ' '))
                             confirmed_symptoms_vi.append(symptom_name_vi)

                     # Thêm câu dẫn và danh sách triệu chứng nếu có
                     if confirmed_symptoms_vi:
                         # Giới hạn số lượng triệu chứng hiển thị nếu quá dài (ví dụ: 5 triệu chứng đầu)
                         max_symptoms_to_show = 5
                         symptoms_text = ", ".join(confirmed_symptoms_vi[:max_symptoms_to_show])
                         if len(confirmed_symptoms_vi) > max_symptoms_to_show:
                              symptoms_text += ",..." # Thêm dấu ... nếu danh sách dài hơn
                         response_lines.append(f"Dựa trên các triệu chứng bạn cung cấp:{symptoms_text}, bạn có khả năng đang mắc phải:")
                     else:
                         # Câu dẫn chung nếu không tóm tắt được triệu chứng
                         response_lines.append("Dựa trên các triệu chứng bạn đã cung cấp, bạn có khả năng đang mắc phải:")

                     # 3. Hiển thị bệnh có khả năng cao nhất (in đậm)
                     if most_likely and most_likely != "Lỗi dự đoán":
                         response_lines.append(f"-> **{most_likely}**")
                     else:
                         # Xử lý trường hợp không có dự đoán hoặc có lỗi
                         response_lines.append("-> *Không thể đưa ra gợi ý cụ thể dựa trên thông tin hiện có.*")


                     # 4. Lưu ý quan trọng (định dạng lại)
                     # 4. Lưu ý quan trọng (định dạng lại - SỬA LẠI DÙNG MARKDOWN LIST)
                     response_lines.append("\n\n---") # Thêm dòng trống trước HR
                     response_lines.append("\n**Lưu ý quan trọng:**\n") # Thêm dòng trống sau tiêu đề

                    # Sử dụng '*' hoặc '-' và dấu cách để tạo danh sách Markdown chuẩn
                     response_lines.append("* Kết quả này **KHÔNG** phải là chẩn đoán y tế.")
                     response_lines.append("* Vui lòng **luôn tham khảo ý kiến bác sĩ** để được chẩn đoán chính xác và tư vấn điều trị phù hợp.")

                    # Nối các dòng lại. Các \n giữa các mục append sẽ được marked.js xử lý đúng cách
                    # để tạo ra cấu trúc HTML (ví dụ: <hr>, <p><strong>...</strong></p>, <ul><li>...</li></ul>)
                     bot_response = "\n".join(response_lines)

                     # --- KẾT THÚC THAY ĐỔI ĐỊNH DẠNG OUTPUT ---

                 else:
                     # Giữ nguyên thông báo lỗi nếu vector không hợp lệ
                     bot_response = "**Lỗi**: Không đủ thông tin triệu chứng để đưa ra gợi ý."

                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None} # Reset session sau khi dự đoán

             elif next_node_key == 'STOP' or not next_node_key:
                 print(f"DEBUG: Reached end state ({current_node_key} -> {('Yes' if is_affirmative else 'No')} -> {next_node_key}), stopping.")
                 bot_response = "Cảm ơn bạn đã cung cấp thông tin. Dựa trên những triệu chứng này, tôi chưa thể đưa ra gợi ý cụ thể hơn hoặc nằm ngoài phạm vi các bệnh phổ biến tôi được huấn luyện. Bạn nên tham khảo ý kiến bác sĩ nhé."
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None} # Reset

             elif next_node_key in SYMPTOM_QUESTIONING_TREE: # Chuyển sang hỏi triệu chứng tiếp theo
                 next_node_info = SYMPTOM_QUESTIONING_TREE[next_node_key]
                 current_symptom_session["current_node_key"] = next_node_key # <<< Cập nhật node hiện tại LÀ node MỚI
                 # Lấy câu hỏi tiếng Việt
                 symptom_key_for_question = next_node_info.get('symptom_key', next_node_key) # Lấy key triệu chứng của node mới
                 symptom_vi_name = symptom_translation_vi_map.get(symptom_key_for_question, symptom_key_for_question.replace('_',' ').capitalize())
                 # Lấy câu hỏi từ node mới, có fallback và thêm gợi ý (Y/N)
                 question_vi = next_node_info.get('question_vi', f"Bạn có bị '{symptom_vi_name}' không?")
                 if "(y/n)" not in question_vi.lower() and "(yes/no)" not in question_vi.lower():
                      question_vi += " (**Y**: có/ **N**: không)" # Thêm gợi ý nếu chưa có
                 bot_response = question_vi
                 print(f"DEBUG: Moved to node '{next_node_key}', asking about '{symptom_key_for_question}'")

             else: # Lỗi: next_node_key không hợp lệ
                 print(f"DEBUG: Lỗi cây quyết định - không tìm thấy node kế tiếp '{next_node_key}' được định nghĩa từ node '{current_node_key}'.")
                 bot_response = "Đã có lỗi logic trong cây hỏi triệu chứng (không tìm thấy bước tiếp theo). Vui lòng bắt đầu lại."
                 current_symptom_session = {"active": False, "symptom_vector": [], "current_node_key": None} # Reset

             return bot_response # Trả về ngay sau khi xử lý Y/N

    # --- Xử lý Intent thông thường (Chỉ chạy nếu không ở trong luồng hỏi và trả lời Y/N) ---
    # Kiểm tra lại vì session có thể đã reset ở phần xử lý non-Y/N
    if not current_symptom_session.get("active"):
        # Nếu intent chưa được dự đoán lại ở phần xử lý non-Y/N thì dự đoán ở đây
        if 'intent_tag' not in locals():
             intent_tag, confidence = predict_intent(user_message)
             print(f"DEBUG: Intent='{intent_tag}', Confidence={confidence:.4f}")

        if intent_tag == "error":
            bot_response = "Đã có lỗi xảy ra khi xử lý yêu cầu của bạn."

        elif intent_tag == "report_symptoms" and confidence >= INTENT_CONFIDENCE_THRESHOLD:
            # --- Bắt đầu luồng hỏi triệu chứng MỚI theo cây ---
            print("DEBUG: Bắt đầu luồng hỏi triệu chứng theo cây.")
            response_options = responses_dict.get(intent_tag, [])
            # Chọn câu giới thiệu từ intent.json hoặc câu mặc định
            bot_response_intro = random.choice(response_options) if response_options \
                else "Ok, tôi sẽ hỏi bạn một số triệu chứng."

            # Thêm lưu ý quan trọng vào phần giới thiệu nếu chưa có
            disclaimer = "**Lưu ý quan trọng:** Thông tin này **KHÔNG** phải là chẩn đoán y tế và không thể thay thế việc thăm khám trực tiếp với bác sĩ."
            if disclaimer.lower() not in bot_response_intro.lower():
                 bot_response_intro += "\n" + disclaimer

            # Khởi tạo session mới
            current_symptom_session["active"] = True
            current_symptom_session["symptom_vector"] = [0.0] * len(symptom_names) # Vector ban đầu toàn số 0
            current_symptom_session["current_node_key"] = "START" # <<< Quan trọng: Giữ là "START"

            # Keyword Spotting (có thể cần cải thiện)
            spotted = spot_keywords(user_message, symptom_names)
            print(f"DEBUG: Spotted relevant symptoms: {spotted}")
            for symptom_key in spotted:
                if symptom_key in symptom_names:
                    try:
                       symptom_index = symptom_names.index(symptom_key)
                       # Đảm bảo vector có đúng kích thước
                       if len(current_symptom_session["symptom_vector"]) == len(symptom_names):
                            current_symptom_session["symptom_vector"][symptom_index] = 1.0
                       else:
                            print(f"DEBUG: Lỗi kích thước vector khi spotting symptom '{symptom_key}'.")
                    except ValueError:
                        print(f"DEBUG: Lỗi - spotted symptom '{symptom_key}' không có index trong symptom_names?")

            # Lấy câu hỏi đầu tiên từ cây
            start_node_info = SYMPTOM_QUESTIONING_TREE.get("START")
            if start_node_info:
                start_symptom_key = start_node_info.get('symptom_key') # Key của triệu chứng hỏi đầu tiên ('high_fever')
                # Lấy tên tiếng Việt
                start_symptom_vi = symptom_translation_vi_map.get(start_symptom_key, start_symptom_key.replace('_',' ') if start_symptom_key else "triệu chứng chung")
                # Lấy câu hỏi từ node START, có fallback và thêm (Y/N) nếu chưa có
                first_question = start_node_info.get('question_vi', f"Để bắt đầu, bạn có bị '{start_symptom_vi}' không?")
                if "(y/n)" not in first_question.lower() and "(yes/no)" not in first_question.lower():
                      first_question += " (**Y**: có/ **N**: không)"

                # Kiểm tra xem triệu chứng ĐẦU TIÊN đã được spot chưa
                start_symptom_index = -1
                if start_symptom_key and start_symptom_key in symptom_names:
                     try:
                         start_symptom_index = symptom_names.index(start_symptom_key)
                     except ValueError: pass # Bỏ qua nếu key không có index

                # Nếu triệu chứng đầu tiên đã được spot -> Đi theo nhánh YES của START node ngay
                if start_symptom_index != -1 and \
                   len(current_symptom_session["symptom_vector"]) == len(symptom_names) and \
                   current_symptom_session["symptom_vector"][start_symptom_index] == 1.0:

                    print(f"DEBUG: Triệu chứng bắt đầu '{start_symptom_key}' đã được spot, đi theo nhánh YES từ START.")
                    next_node_key = start_node_info.get('yes_next')
                    current_symptom_session["current_node_key"] = next_node_key # Cập nhật node hiện tại là node kế tiếp

                    # Lấy câu hỏi tiếp theo (nếu có và hợp lệ)
                    if next_node_key and next_node_key in SYMPTOM_QUESTIONING_TREE:
                         next_node_info = SYMPTOM_QUESTIONING_TREE.get(next_node_key)
                         next_symptom_key = next_node_info.get('symptom_key', next_node_key)
                         next_symptom_vi = symptom_translation_vi_map.get(next_symptom_key, next_symptom_key.replace('_',' ').capitalize())
                         # Lấy câu hỏi từ node tiếp theo, thêm (Y/N) nếu chưa có
                         next_question = next_node_info.get('question_vi', f"Bạn có bị '{next_symptom_vi}' không?")
                         if "(y/n)" not in next_question.lower() and "(yes/no)" not in next_question.lower():
                             next_question += " (**Y**: có/ **N**: không)"
                         bot_response = bot_response_intro + "\n" + next_question
                         print(f"DEBUG: Skipped first question, moved directly to node '{next_node_key}'")
                    # Nếu nhánh YES dẫn đến PREDICT/STOP hoặc node không hợp lệ
                    elif next_node_key == 'PREDICT' or next_node_key == 'STOP':
                         # Trường hợp này nên được xử lý ở lần gọi generate_response tiếp theo
                         # khi current_node_key là 'PREDICT' hoặc 'STOP' (nếu bạn định nghĩa node PREDICT/STOP)
                         # Hoặc gọi hàm dự đoán/dừng ngay tại đây. Hiện tại chỉ thông báo.
                         print(f"DEBUG: Branch from START immediately leads to '{next_node_key}'. Will be handled in next turn or needs direct handling.")
                         # Có thể trả về câu hỏi trước đó hoặc một thông báo chung
                         bot_response = bot_response_intro + f"\n(Đã ghi nhận triệu chứng '{start_symptom_vi}', tôi sẽ xử lý bước tiếp theo...)"
                         # Quan trọng: Giữ session active và current_node_key là next_node_key
                    else: # Lỗi không tìm thấy node kế tiếp
                         print(f"DEBUG: Lỗi - Node kế tiếp '{next_node_key}' từ START (nhánh Yes) không hợp lệ.")
                         bot_response = bot_response_intro + "\n(Đã ghi nhận thông tin ban đầu, nhưng có lỗi logic cây ở bước tiếp theo.)"
                         current_symptom_session["active"] = False # Hủy luồng

                else: # Triệu chứng bắt đầu chưa được spot -> hỏi câu đầu tiên
                    bot_response = bot_response_intro + "\n" + first_question
                    # Node key vẫn là "START"
                    print(f"DEBUG: Asking first question for node 'START' (symptom '{start_symptom_key}')")


            else: # Lỗi không có nút START trong cây
                bot_response = bot_response_intro + "\n(Lỗi: Không thể bắt đầu cây hỏi triệu chứng - Thiếu nút START.)"
                current_symptom_session["active"] = False

        # Xử lý các intent khác hoặc unknown
        elif intent_tag != "error": # Bao gồm cả 'unknown'
            response_options = responses_dict.get(intent_tag)
            if response_options:
                bot_response = random.choice(response_options)
            # else: giữ nguyên default response nếu intent là unknown và không có response định nghĩa

    return bot_response

# --- (Tùy chọn) Hàm chạy thử local ---
if __name__ == '__main__':
    try:
        load_resources(artifact_dir='.')
        print("\n--- Chạy thử Chatbot Core (Local - Logic Cây Quyết định) ---")
        local_history = [{'role': 'bot', 'content': 'Xin chào! Tôi là trợ lý ảo HMS...'}]
        print(f"Bot: {local_history[0]['content']}")

        while True:
            user_msg = input("You: ")
            if not user_msg: continue
            if user_msg.lower() in ["tạm biệt", "bye", "goodbye", "thoát"]:
                print("Bot:", random.choice(responses_dict.get("goodbye", ["Tạm biệt!"])))
                break

            local_history.append({'role': 'user', 'content': user_msg})
            # Quan trọng: Luôn dùng history đầy đủ khi gọi generate_response
            # Biến current_symptom_session là global nên sẽ được cập nhật bên trong hàm
            bot_msg = generate_response(user_msg, local_history)
            print(f"Bot: {bot_msg}")
            local_history.append({'role': 'bot', 'content': bot_msg})
            # Giới hạn lịch sử local (ví dụ 20 lượt cuối)
            if len(local_history) > 20: local_history = local_history[-20:]

    except FileNotFoundError as e:
        print(f"\nLỗi: Không tìm thấy file cần thiết. {e}")
    except Exception as e:
        print(f"\nLỗi khi chạy thử chatbot core: {e}")