# 第一阶段：构建Vue前端
FROM node:16 as frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 复制前端项目文件
COPY bell_admin/package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY bell_admin/ ./

# 构建前端
RUN npm run build:prod

# 第二阶段：Python后端
FROM python:3.13

# 设置工作目录
WORKDIR /app/backend

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建必要的目录
RUN mkdir -p /app/backend/media /app/backend/static

# 首先复制 requirements.txt
COPY Bell/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r requirements.txt

# 然后复制其他后端文件
COPY Bell/manage.py /app/backend/
COPY Bell/bell /app/backend/bell/
COPY Bell/device /app/backend/device/
COPY Bell/menu /app/backend/menu/
COPY Bell/user /app/backend/user/

# 从前端构建阶段复制构建文件
COPY --from=frontend-builder /app/frontend/dist /app/backend/static/dist

# 暴露端口
EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/sh\n\
python manage.py migrate --noinput\n\
python manage.py collectstatic --noinput\n\
gunicorn bell.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120' > /app/backend/start.sh \
    && chmod +x /app/backend/start.sh

# 启动命令
CMD ["/app/backend/start.sh"] 