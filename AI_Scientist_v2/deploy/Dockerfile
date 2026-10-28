# syntax=docker/dockerfile:1
# ══════════════════════════════════════════════════════════════════
# 智研星枢 生产镜像：前端构建 + 后端运行时 双阶段合一
# 构建上下文 = 仓库根（AI_Scientist_v2/），即 deploy/Dockerfile 的上级目录：
#   docker build -f deploy/Dockerfile .
# 国内网络可换镜像源加速：
#   --build-arg NPM_REGISTRY=https://registry.npmmirror.com `
#   --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
# ══════════════════════════════════════════════════════════════════

# ── 阶段 1：构建前端（Vite → dist 静态产物）──
# 基础镜像源可参数化：国内网络传 docker.1ms.run/library/... 镜像地址（compose 已预配），不用梯子也能拉
ARG NODE_IMAGE=docker.io/library/node:20-alpine
ARG PY_IMAGE=docker.io/library/python:3.12-slim
FROM ${NODE_IMAGE} AS web
ARG NPM_REGISTRY=https://registry.npmjs.org
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=${NPM_REGISTRY}
COPY frontend/ ./
RUN npm run build

# ── 阶段 2：后端运行时 ──
FROM ${PY_IMAGE}
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt
COPY backend/app ./app
COPY backend/run.py ./
# 前端产物放到 main.py FRONTEND_DIST 候选路径之一 → 单容器即全站（API+页面）
COPY --from=web /web/dist /app/frontend/dist

# 数据目录（compose 里挂 volume，容器重建不丢上传/生成文件）
RUN mkdir -p /app/backend/generated /app/backend/uploads /app/backend/logs

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
