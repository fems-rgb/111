# ============================================================
# 智研星枢 后端镜像
# 构建（在项目根 AI_Scientist_v2/ 下）：
#   docker build -f backend/Dockerfile -t zhixing-backend:3.0.0 backend
# 运行：
#   docker run --rm -p 8000:8000 --env-file backend/.env zhixing-backend:3.0.0
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

# 系统依赖：
#   libgl1 / libglib2.0-0 → matplotlib
#   fonts-noto-cjk        → PDF 中文渲染
#   libpango / libcairo / libgdk-pixbuf → WeasyPrint（PDF 导出核心）
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libgl1 \
        libglib2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        shared-mime-info \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY ./app ./app
COPY ./run.py ./alembic.ini ./
COPY ./migrations ./migrations/
COPY ./scripts ./scripts/

# 前端预构建产物（SPA 单端口部署）
COPY ./static ./static/

# 运行时目录（generated 为一切生成文件的固定根，启动时会自动建齐骨架）
RUN mkdir -p /app/data /app/uploads /app/logs /app/generated

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

# 生产：多 worker；容器内监听 0.0.0.0
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
