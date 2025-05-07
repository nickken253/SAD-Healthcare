import logging
import os
import traceback # Để in lỗi chi tiết
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import ChatMessageSerializer, ChatResponseSerializer

logger = logging.getLogger('ai')

# --- Biến global để lưu trữ chatbot core và trạng thái ---
chatbot_core_instance = None
chatbot_ready_flag = False
initialization_error = None

# --- CỐ GẮNG IMPORT VÀ TẢI TÀI NGUYÊN NGAY LẬP TỨC ---
logger.info("Attempting to import and initialize chatbot_core at module level...")
try:
    # Bước 1: Import module chatbot_core
    # Đảm bảo chatbot_core.py nằm trong thư mục 'ai' (ai_service/ai/chatbot_core.py)
    from . import chatbot_core
    chatbot_core_instance = chatbot_core # Gán vào biến global nếu import thành công
    logger.info("chatbot_core imported successfully.")

    # Bước 2: Tải tài nguyên ngay lập tức
    try:
        # Xác định đường dẫn artifacts (giống như trong AppConfig)
        # Giả sử artifacts nằm cùng cấp với views.py trong thư mục 'ai'
        artifact_dir = os.path.dirname(os.path.abspath(__file__))
        # Hoặc nếu bạn tạo thư mục con 'artifacts' trong 'ai':
        # artifact_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artifacts')

        logger.info(f"Loading chatbot resources from artifact_dir: {artifact_dir}")

        # Kiểm tra sự tồn tại của các file quan trọng (tùy chọn nhưng nên có)
        required_files = [
            'intent_chatbot_model.keras',
            'symptom_checker_model_filtered.keras',
            'tokenizer.pickle',
            'label_encoder.pickle',
            'relevant_symptom_names_filtered.json',
            'disease_names_filtered_vi.json',
            'intents.json'
        ]
        missing_files = []
        for fname in required_files:
            fpath = os.path.join(artifact_dir, fname)
            if not os.path.exists(fpath):
                missing_files.append(fname)

        if missing_files:
             error_msg = f"Cannot load chatbot resources. Missing required artifact files in {artifact_dir}: {', '.join(missing_files)}"
             logger.error(error_msg)
             initialization_error = error_msg # Lưu lỗi để trả về sau
             # Không đặt chatbot_ready_flag = True
        else:
            # Gọi hàm load_resources từ module đã import
            chatbot_core_instance.load_resources(artifact_dir=artifact_dir)
            chatbot_ready_flag = True # Đánh dấu sẵn sàng
            logger.info("Chatbot resources loaded successfully at module level.")

    except FileNotFoundError as e:
        error_msg = f"FileNotFoundError during resource loading: {e}. Check artifact paths inside chatbot_core.load_resources and ensure files are in {artifact_dir}."
        logger.critical(error_msg, exc_info=True)
        initialization_error = error_msg
    except Exception as e:
        error_msg = f"CRITICAL ERROR loading chatbot resources: {e}"
        logger.critical(error_msg, exc_info=True)
        initialization_error = error_msg # Lưu lỗi

except ImportError as e:
    error_msg = f"CRITICAL ImportError: Failed to import chatbot_core: {e}. Ensure chatbot_core.py is in the 'ai' directory and all required libraries (tensorflow, numpy, nltk, scikit-learn, pandas etc.) are installed in the correct environment."
    logger.critical(error_msg, exc_info=True)
    initialization_error = error_msg # Lưu lỗi
except Exception as e:
    error_msg = f"CRITICAL UNEXPECTED ERROR during chatbot_core import or initialization: {e}"
    logger.critical(error_msg, exc_info=True)
    initialization_error = error_msg # Lưu lỗi

# --- Kết thúc phần tải tài nguyên ---


class AIChatView(APIView):
    """
    API endpoint để tương tác với AI Chatbot (Logic tích hợp trực tiếp).
    Tài nguyên AI được tải khi module view được nạp.
    KHÔNG yêu cầu xác thực.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    # Quản lý lịch sử chat - VẪN LÀ VẤN ĐỀ cho production
    session_histories = {}

    def get_session_key(self, request):
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    def post(self, request, *args, **kwargs):
        logger.debug(f"AIChatView (Simple Load) POST request received.")
        logger.debug(f"Request Data: {request.data}")

        # Kiểm tra xem quá trình khởi tạo ban đầu có thành công không
        if not chatbot_ready_flag or not chatbot_core_instance:
            logger.error(f"Chatbot core is not ready. Initialization error: {initialization_error}")
            # Trả về lỗi chi tiết hơn nếu có
            error_detail = initialization_error or "Chatbot service failed to initialize."
            return Response({"error": f"Chatbot service is not ready. Detail: {error_detail}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']
        session_key = self.get_session_key(request)
        current_history = AIChatView.session_histories.get(session_key, [])

        # --- Gọi trực tiếp logic chatbot ---
        try:
            current_history.append({'role': 'user', 'content': user_message})
            history_limit = 20
            if len(current_history) > history_limit * 2:
                 current_history = current_history[-(history_limit * 2):]

            logger.debug(f"Calling chatbot_core_instance.generate_response for session {session_key} with history length: {len(current_history)}")
            # Sử dụng instance đã được import và khởi tạo ở cấp module
            bot_response = chatbot_core_instance.generate_response(user_message, current_history)

            current_history.append({'role': 'bot', 'content': bot_response})
            AIChatView.session_histories[session_key] = current_history # Lưu lại lịch sử

            logger.info(f"Chatbot core generated response for session {session_key}: {bot_response}")

            response_serializer = ChatResponseSerializer(data={"reply": bot_response})
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.critical(f"Error calling chatbot_core.generate_response for session {session_key}: {e}\n{traceback.format_exc()}", exc_info=True)
            return Response({"error": "An error occurred while processing the chat message."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

