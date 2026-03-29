# Sử dụng Python 3.12 Base Image (Bản Slim siêu nhẹ)
FROM python:3.12-slim

# Cài đặt một số thư viện lõi hệ thống phòng trường hợp Scipy/Pandas cần C++ Build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc trong Container
WORKDIR /app

# Copy Requirements và cài đặt siêu tốc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Toàn bộ Trái Tim AI (Source Code) vào Container
COPY . .

# Mở cổng API
EXPOSE 8000

# Lệnh sống còn để kích hoạt Server AI tự động khi Cloud khởi động
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
