# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template
import chatbot_core # Import module logic chatbot của bạn

app = Flask(__name__)

# --- Quản lý Lịch sử Chat Đơn giản (In-memory) ---
# Lưu ý: Cách này sẽ mất lịch sử khi server restart.
# Chỉ phù hợp cho demo local 1 người dùng.
# Trong ứng dụng thực tế cần dùng session, database hoặc cache.
conversation_history = []

print("Đang tải model và các thành phần chatbot...")
try:
    chatbot_core.load_resources() # Gọi hàm tải tài nguyên từ chatbot_core
    print("Chatbot core đã sẵn sàng.")
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG KHI KHỞI TẠO CHATBOT CORE: {e}")
    # Có thể quyết định thoát ứng dụng ở đây nếu muốn
    # exit()

@app.route('/')
def home():
    """Phục vụ trang web chat"""
    global conversation_history
    conversation_history = [] # Reset lịch sử mỗi khi tải lại trang chính
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Nhận tin nhắn từ user, xử lý và trả về phản hồi của bot"""
    global conversation_history
    try:
        data = request.get_json()
        user_message = data.get('message')
        # Lịch sử client gửi lên có thể dùng để đồng bộ, nhưng ở đây
        # chúng ta sẽ dùng lịch sử lưu trên server để đảm bảo tính liên tục
        # client_history = data.get('history', []) # Có thể dùng để debug hoặc đồng bộ

        if not user_message:
            return jsonify({'response': 'Vui lòng nhập tin nhắn.'}), 400

        # Thêm tin nhắn user vào lịch sử server
        conversation_history.append({'role': 'user', 'content': user_message})

        # Gọi logic chatbot để lấy phản hồi, truyền vào tin nhắn mới và lịch sử
        # Hàm generate_response cần được thiết kế để nhận và sử dụng history
        bot_response = chatbot_core.generate_response(user_message, conversation_history)

        # Thêm phản hồi của bot vào lịch sử server
        conversation_history.append({'role': 'bot', 'content': bot_response})

        # Giới hạn độ dài lịch sử để tránh tốn bộ nhớ (ví dụ: giữ 20 lượt thoại gần nhất)
        history_limit = 20
        if len(conversation_history) > history_limit * 2:
             conversation_history = conversation_history[-(history_limit * 2):]


        return jsonify({'response': bot_response})

    except Exception as e:
        print(f"Lỗi xử lý /chat: {e}")
        # Gửi lỗi về client một cách an toàn
        error_message = "Xin lỗi, đã có lỗi xảy ra phía server. Vui lòng thử lại sau."
        # Thêm lỗi vào lịch sử để client biết
        conversation_history.append({'role': 'bot', 'content': error_message})
        return jsonify({'response': error_message}), 500

if __name__ == '__main__':
    # Chạy Flask server ở chế độ debug (chỉ dùng cho phát triển)
    # Host '0.0.0.0' cho phép truy cập từ máy khác trong cùng mạng LAN
    app.run(host='0.0.0.0', port=5000, debug=True)