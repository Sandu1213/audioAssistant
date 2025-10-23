FROM python:3.9-slim

# 安装 ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p uploads outputs

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]