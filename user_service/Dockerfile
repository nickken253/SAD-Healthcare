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

# Mở port 8000
EXPOSE 8000

# Chạy ứng dụng khi container khởi động
CMD ["python", "-m", "uvicorn", "user_service.asgi:application", "--host", "0.0.0.0", "--port", "8000"]