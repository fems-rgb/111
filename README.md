# 111-1 Workspace

> 工作区根目录，承载一个主项目。

## 项目

| 目录 | 说明 |
|---|---|
| [`AI_Scientist_v2/`](./AI_Scientist_v2/) | **智研星枢 · AI Scientist v3.0** — 挑战杯「揭榜挂帅」XH-202619 参赛作品 · 基于国产 Qwen 的多智能体科研假设自动生成平台 |

## 快速起服务

```bash
# 最简方式（无需 Node，预构建 SPA）
cd AI_Scientist_v2/backend
pip install -r requirements.txt
copy .env.example .env        # 填入 QWEN_API_KEY
python run.py                 # → http://localhost:8000

# Docker 一键（单容器，开发 / 体验）
cd AI_Scientist_v2
docker compose up --build     # → http://localhost:8000

# 生产多副本（nginx → app×N → PostgreSQL + Redis）见 AI_Scientist_v2/deploy/，详见项目 README §22
```

## 文档索引

| 文档 | 说明 |
|---|---|
| [项目 README](./AI_Scientist_v2/README.md) | 完整技术方案（赛题映射 / 架构 / API / 部署） |
| [技术方案.md](./AI_Scientist_v2/docs/技术方案.md) | 评审精简版文档 |
| [技术方案.pdf](./AI_Scientist_v2/docs/技术方案.pdf) | 15 页 PDF 交付件 |
| [快速开始.md](./AI_Scientist_v2/docs/快速开始.md) | 部署指南 |
| [提交清单.md](./AI_Scientist_v2/docs/提交清单.md) | 赛题材料对照 |

## 技术栈速览

- **基座模型**：通义千问 Qwen（qwen-max · qwen-vl-max）· 阿里云百炼 DashScope
- **后端**：Python 3.12 · FastAPI · SQLAlchemy async · SQLite（默认）/ PostgreSQL（asyncpg）· Alembic
- **前端**：Vue 3.5 · TypeScript 5.7 · Vite 6 · Pinia · Element Plus · Tailwind
- **实验**：numpy/pandas/scipy/matplotlib · WeasyPrint（PDF 导出）
- **运维**：Docker（单容器 / 生产 nginx+PostgreSQL+Redis）· Redis（可选分布式）· GitHub Actions CI · pytest

## 冒烟测试

```bash
cd AI_Scientist_v2/backend
pip install -r requirements-dev.txt
pytest -q                     # 预期：12 passed
```

## 工作区结构

```
111-1/
├── README.md                       ← 你在这里
└── AI_Scientist_v2/
    ├── backend/                    FastAPI + SPA（单端口）· Dockerfile · requirements[-dev].txt · scripts/
    ├── frontend/                   Vue 3 源码
    ├── deploy/                     生产上云编排：nginx → app×N → PostgreSQL + Redis
    ├── docs/                       交付文档（技术方案 .md/.pdf · 快速开始 · 提交清单）
    ├── .github/workflows/ci.yml    GitHub Actions CI（后端 pytest + 前端 build）
    ├── docker-compose.yml          单容器一键部署（开发 / 体验）
    └── README.md                   项目主文档
```
