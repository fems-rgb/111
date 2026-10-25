# 111-1 Workspace

> 工作区根目录。当前仅承载一个主项目。

## 项目

| 目录 | 说明 |
|---|---|
| [`AI_Scientist_v2/`](./AI_Scientist_v2/) | **智研星枢 · AI Scientist v3.0** — 挑战杯「揭榜挂帅」XH-202619 参赛作品 · 基于国产 Qwen 的多智能体科研假设自动生成平台 |

进入项目：

```bash
cd AI_Scientist_v2
```

**主文档**：[AI_Scientist_v2/README.md](./AI_Scientist_v2/README.md) · 1184 行完整技术方案  
**评审精简版**：[AI_Scientist_v2/docs/技术方案.md](./AI_Scientist_v2/docs/技术方案.md)  
**快速开始**：[AI_Scientist_v2/docs/快速开始.md](./AI_Scientist_v2/docs/快速开始.md)  
**提交清单**：[AI_Scientist_v2/docs/提交清单.md](./AI_Scientist_v2/docs/提交清单.md)

## 技术栈速览

- **后端**：Python 3.12 · FastAPI · SQLAlchemy async · SQLite（可切 PostgreSQL）· Alembic · pytest
- **前端**：Vue 3.5 · TypeScript 5.7 · Vite 6 · Pinia · Element Plus · Tailwind
- **基座模型**：通义千问 Qwen（qwen-max · qwen-plus · qwen-vl-max）
- **调用平台**：阿里云百炼 DashScope

## 快速起服务

```bash
# 后端
cd AI_Scientist_v2/backend
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env        # 编辑填入 QWEN_API_KEY
python -m app.database.init_db
python run.py --reload        # http://localhost:8000

# 前端（另开终端）
cd AI_Scientist_v2/frontend
npm ci && npm run dev         # http://localhost:5173
```

或一键 Docker：

```bash
cd AI_Scientist_v2
docker compose up --build
```

## 冒烟测试

```bash
cd AI_Scientist_v2/backend
pip install -r requirements-dev.txt
pytest -q                     # 预期：12 passed
```

## 工作区目录

```
111-1/
├── README.md                       ← 你在这里
└── AI_Scientist_v2/
    ├── backend/                    FastAPI 后端
    ├── frontend/                   Vue 3 前端
    ├── docs/                       交付文档（技术方案 / 快速开始 / 提交清单）
    ├── .github/workflows/ci.yml    CI
    ├── docker-compose.yml
    └── README.md                   项目主文档
```
