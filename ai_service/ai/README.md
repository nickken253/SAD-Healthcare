# Chatbot Chăm sóc Sức khỏe (ChatbotForHealthcare)

Đây là dự án chatbot được thiết kế để hỗ trợ trong lĩnh vực chăm sóc sức khỏe. Chatbot có khả năng nhận dạng ý định người dùng và đưa ra các gợi ý hoặc thông tin liên quan đến triệu chứng bệnh dựa trên mô hình học máy.

## Mục lục

* [Tổng quan](#tổng-quan)
* [Các Tính năng Chính](#các-tính-năng-chính)
* [Cấu trúc Thư mục](#cấu-trúc-thư-mục)
* [Công nghệ Sử dụng](#công-nghệ-sử-dụng)
* [Cài đặt](#cài-đặt)
* [Cách Chạy](#cách-chạy)
* [Các File Quan trọng](#các-file-quan-trọng)
* [Đóng góp](#đóng-góp)
* [Giấy phép](#giấy-phép)

## Tổng quan

Dự án này là một phần của Hệ thống Quản lý Chăm sóc Sức khỏe lớn hơn, đóng vai trò là một Microservice AI (AIService). Mục tiêu chính là cung cấp một giao diện trò chuyện thông minh để hỗ trợ người dùng với các truy vấn liên quan đến sức khỏe cơ bản và sàng lọc triệu chứng ban đầu.


## Các Tính năng Chính

* **Nhận dạng ý định (Intent Recognition):** Hiểu được mục đích của người dùng thông qua tin nhắn của họ.
* **Kiểm tra Triệu chứng (Symptom Checker):** Dựa trên các triệu chứng người dùng cung cấp, chatbot đưa ra gợi ý về các bệnh có khả năng liên quan (lưu ý: đây không phải là chẩn đoán y tế).
* **Giao diện Web:** Cung cấp giao diện người dùng đơn giản qua trình duyệt để tương tác với chatbot.
* **(Có thể mở rộng)** Trả lời câu hỏi thường gặp (FAQ) về sức khỏe.
* **(Có thể mở rộng)** Kết nối với các service khác để cung cấp thông tin (ví dụ: đặt lịch hẹn).

## Cấu trúc Thư mục

Dưới đây là cấu trúc thư mục chính của dự án `ChatbotForHealthcare`:
```
ChatbotForHealthcare/
├── pycache/          # Thư mục cache của Python
├── static/                # Chứa các file CSS, JavaScript cho frontend
│   ├── script.js
│   └── style.css
├── templates/             # Chứa file HTML cho giao diện
│   └── index.html
├── app.py                 # File server backend (Flask)
├── chatbot_core.py        # File chứa logic chính của chatbot (NLU, model, response generation)
├── disease_names_filtered_vi.json # Tên bệnh (tiếng Việt)
├── disease_names_vi.json  # Tên bệnh (tiếng Việt - có thể là file gốc)
├── intent_chatbot_model.keras # Model đã huấn luyện cho nhận dạng ý định
├── intents.json            # Định nghĩa các ý định và mẫu câu
├── intents.txt             # Dữ liệu thô cho ý định (nếu có)
├── label_encoder.pickle   # Bộ mã hóa nhãn đã lưu (cho ý định hoặc bệnh)
├── relevant_symptom_names_filtered.json # Danh sách tên triệu chứng liên quan (đã lọc)
├── symptom_checker_model_filtered.keras # Model kiểm tra triệu chứng (đã lọc)
├── symptom_checker_model.keras    # Model kiểm tra triệu chứng (gốc)
├── symptom_confusion_matrix_vi.png # Ma trận nhầm lẫn (kết quả đánh giá model)
├── symptom_label_encoder_EN.pickle # Bộ mã hóa nhãn triệu chứng (tiếng Anh)
├── symptom_label_encoder_filtered_EN.pickle # Bộ mã hóa nhãn triệu chứng (tiếng Anh, đã lọc)
├── symptom_names.json     # Tên các triệu chứng
├── tokenizer.pickle       # Tokenizer đã lưu cho xử lý văn bản
└── requirements.txt       # (Nên có) Danh sách các thư viện Python cần thiết
```

## Công nghệ Sử dụng

* **Backend:** Python, Flask
* **Machine Learning:** TensorFlow/Keras
* **Xử lý Ngôn ngữ Tự nhiên (NLP):** Các kỹ thuật cơ bản (Tokenization, Padding)
* **Frontend:** HTML, CSS, JavaScript (cho giao diện demo)
* **Thư viện Python chính:**
    * Flask
    * TensorFlow / Keras
    * NumPy
    * Scikit-learn (cho `LabelEncoder`)
    * Pandas (nếu dùng để xử lý dữ liệu)

## Cài đặt

1.  **Clone repository (nếu đã push lên Git):**
    ```bash
    git clone https://github.com/nickken253/ChatbotHealthcare
    cd ChatbotForHealthcare
    ```
2.  **Tạo và kích hoạt môi trường ảo (khuyến nghị):**
    ```bash
    python -m venv venv_chatbot # Hoặc tên khác
    # Windows
    venv_chatbot\Scripts\activate
    # macOS/Linux
    source venv_chatbot/bin/activate
    ```
3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```
    Nếu chưa có `requirements.txt`, bạn cần cài đặt thủ công các thư viện chính:
    ```bash
    pip install Flask tensorflow numpy scikit-learn pandas # (và các thư viện khác nếu cần)
    ```

## Cách Chạy

1.  **Đảm bảo môi trường ảo đã được kích hoạt.**
2.  **Chạy server Flask:**
    Từ thư mục gốc `ChatbotForHealthcare` (nơi chứa file `app.py`), chạy lệnh:
    ```bash
    python app.py
    ```
3.  **Mở trình duyệt:**
    Truy cập vào địa chỉ `http://127.0.0.1:5000` (hoặc địa chỉ IP và cổng mà server Flask hiển thị).
4.  **Tương tác với chatbot** qua giao diện web.

## Các File Quan trọng

* `app.py`: Điểm bắt đầu của ứng dụng web, xử lý request/response.
* `chatbot_core.py`: Chứa toàn bộ logic xử lý của chatbot, bao gồm tải model, tiền xử lý input, dự đoán ý định, dự đoán bệnh, và tạo câu trả lời.
* `*.keras`: Các file model Keras đã được huấn luyện.
* `*.pickle`: Các file đối tượng Python đã được lưu (tokenizer, label encoder).
* `*.json`: Các file dữ liệu cấu hình hoặc danh sách (intents, diseases, symptoms).
* `templates/index.html`: Giao diện người dùng.
* `static/script.js`: Logic JavaScript phía client để gửi tin nhắn và hiển thị phản hồi.

## Đóng góp

Hiện tại, dự án đang trong giai đoạn phát triển ban đầu. Nếu bạn muốn đóng góp, vui lòng:
1.  Fork repository.
2.  Tạo một branch mới (`git checkout -b feature/ten-tinh-nang-moi`).
3.  Commit các thay đổi của bạn (`git commit -am 'Thêm tính năng mới xyz'`).
4.  Push lên branch (`git push origin feature/ten-tinh-nang-moi`).
5.  Tạo một Pull Request mới.

Vui lòng đảm bảo code của bạn tuân thủ coding style và có comment rõ ràng.
