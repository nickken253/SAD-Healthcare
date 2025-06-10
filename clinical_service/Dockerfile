# Sử dụng image python chính thức
FROM python:3.9-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Chép file requirements.txt vào container
COPY requirements.txt .

# Cài đặt các gói cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Chép toàn bộ code của service vào container
COPY . .

# Mở port 8002
EXPOSE 8002

# Chạy ứng dụng khi container khởi động (thay tên 'main:app' nếu cần)
CMD ["uvicorn", "clinical_service.asgi:application", "--host", "0.0.0.0", "--port", "8002"]