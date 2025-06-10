# user_service/Dockerfile
# Sử dụng một base image Python nhẹ
FROM python:3.9-slim

# Tắt việc Python tạo file .pyc và bật unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Tạo thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào trước để tận dụng Docker cache
COPY requirements.txt /app/

# Cài đặt các thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của service vào thư mục làm việc
COPY . /app/

# Mở cổng mà Django development server sẽ chạy bên trong container
# Cổng này sẽ được map ra bên ngoài bởi Docker Compose
EXPOSE 8000

# Lệnh để chạy ứng dụng khi container khởi động
# Chúng ta sẽ chạy migrate trong docker-compose hoặc thủ công sau khi container chạy
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]