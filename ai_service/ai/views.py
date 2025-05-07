# ai_service/ai/views.py
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
# from django.conf import settings # Không cần thiết nếu URL không đổi

# URL của Flask Chatbot server bạn đang chạy (trên cổng 5000)
EXISTING_CHATBOT_API_URL = "http://127.0.0.1:5000/chat" # Đảm bảo đây là địa chỉ đúng

class AIChatProxyView(APIView):
    """
    API Proxy để gửi tin nhắn đến chatbot Flask hiện có và nhận phản hồi.
    """
    # permission_classes = [permissions.IsAuthenticated] # Yêu cầu user đăng nhập
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Missing 'message' field."}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy user_id từ token JWT (có thể dùng hoặc không tùy chatbot Flask)
        user_id = request.user.get('user_id')

        # Payload gửi đến Flask chatbot - Khớp với những gì app.py mong đợi
        payload = {
            "message": user_message
            # Chatbot Flask hiện tại không dùng 'sender', nên không cần gửi
        }

        print(f"[AI Service Proxy] Sending to Flask Chatbot ({EXISTING_CHATBOT_API_URL}): {payload}")

        try:
            # Gọi đến API /chat của Flask app
            response = requests.post(EXISTING_CHATBOT_API_URL, json=payload, timeout=10)
            response.raise_for_status() # Check for 4xx/5xx errors

            # Lấy JSON response từ Flask app
            chatbot_response_data = response.json()
            # Lấy giá trị của key 'response' mà Flask app trả về
            bot_message = chatbot_response_data.get("response", "Error: Could not parse chatbot response.")

            print(f"[AI Service Proxy] Received from Flask Chatbot: {bot_message}")

            # Trả về phản hồi cho client đã gọi API proxy này
            # Đặt tên key là 'reply' hoặc 'response' tùy bạn muốn API này trả về gì
            return Response({"reply": bot_message})

        except requests.exceptions.Timeout:
            print(f"[AI Service Proxy] ERROR: Timeout connecting to Flask Chatbot")
            return Response({"error": "Chatbot service timed out."}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.RequestException as e:
            print(f"[AI Service Proxy] ERROR: Could not connect to Flask Chatbot: {e}")
            return Response({"error": f"Could not connect to chatbot service."}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            # In lỗi cụ thể ra console để debug
            import traceback
            print(f"[AI Service Proxy] ERROR: Unexpected error: {e}")
            print(traceback.format_exc()) # In traceback chi tiết
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)