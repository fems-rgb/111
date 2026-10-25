# 智研星枢 · AI Scientist v3.0

> **基于国产开源大模型（Qwen）的多智能体科研假设自动生成平台**
>
> 挑战杯「揭榜挂帅」专项赛参赛作品 · 题目编号 **XH-202619**  
> 发榜单位：浙江阿里巴巴云计算有限公司  
> 基座模型：通义千问 Qwen（qwen-max / qwen-plus / qwen-vl-max，全部国产开源）  
> 调用平台：阿里云百炼（DashScope）

---

## 目录

1. [项目简介](#1-项目简介)
2. [快速开始](#2-快速开始)
3. [赛题要求与方案映射](#3-赛题要求与方案映射)
4. [评分标准对照](#4-评分标准对照100-分拆解)
5. [系统架构](#5-系统架构)
6. [技术栈](#6-技术栈)
7. [多智能体架构](#7-多智能体架构16-agent)
8. [九阶段流水线](#8-九阶段流水线从问题到假设)
9. [实验执行引擎](#9-实验执行引擎与可验证性)
10. [标准化输出](#10-标准化输出科学假设与研究计划)
11. [多模态能力](#11-多模态能力)
12. [认证与通信](#12-认证与前后端通信)
13. [配置与环境变量](#13-配置与环境变量)
14. [目录结构](#14-目录结构)
15. [API 参考](#15-api-参考核心端点)
16. [数据库 Schema](#16-数据库-schema)
17. [真实案例演示](#17-真实案例演示)
18. [Docker 部署](#18-docker-部署)
19. [CI/CD](#19-cicd)
20. [测试策略](#20-测试策略)
21. [可观测性与安全](#21-可观测性与安全)
22. [已知问题与排坑](#22-已知问题与排坑)
23. [提交清单](#23-提交清单)
24. [FAQ](#24-faq)
25. [许可证与致谢](#25-许可证与致谢)

---

## 1. 项目简介

**智研星枢（AI Scientist）** 面向「AI for Science」，基于 **国产开源大模型 Qwen** 构建 **多智能体系统（Multi-Agent）架构**，实现从「科学问题输入」到「可验证科学假设输出」的全链路智能闭环。

```
科学问题（文献 / 数据）
   │
   ▼
┌──────────────────────────────────────────────┐
│  知识缺口识别 → 文献挖掘 → 假设生成          │
│  → 逻辑论证 / 多轮迭代 → 实验设计与验证     │
└──────────────────────────────────────────────┘
   │
   ▼
《科学假设与研究计划》（符合赛题规范）
```

### 核心特性

- **🤖 多智能体协作**：16 Agent + Orchestrator，支持反思循环（Reflection）
- **📚 文献挖掘与事实提取**：结构化信息抽取，避免断章取义
- **💡 逻辑驱动假设生成**：归纳 + 演绎推理，基于已知事实生成假设
- **🔄 多轮迭代与论证**：跨学科技术迁移、可行性论证、人在回路
- **🧪 代码级可验证**：实验模拟场沙箱执行，产出图表 / 动画验证结果
- **📄 标准化输出**：自动生成符合赛题规范的《科学假设与研究计划》
- **🖼️ 多模态**：Qwen-VL 处理图像 / 科学图表
- **🔐 自主可控**：全链路 Qwen，满足赛题「国产模型」要求
- **🔁 一键复现**：Docker / pip + npm / 预构建 SPA / Alembic 迁移

### 关键指标

| 指标 | 数值 |
|---|---|
| 后端 Python 代码 | ~14,000 行（110 文件） |
| 前端 Vue/TS 代码 | ~8,300 行（54 文件） |
| REST API 端点 | 97 个 |
| Agent 数量 | 16 个 |
| 数据库表 | 20+ |
| 内置科学问题 | 125 题（Science 2005 前沿难题） |
| 单元测试 | 12 用例 pytest 全通过 |

---

## 2. 快速开始

### 方式 A：本地开发

```powershell
# 后端
cd AI_Scientist_v2/backend
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env        # 填入 QWEN_API_KEY
python -m app.database.init_db
python run.py --reload        # → http://localhost:8000

# 前端（新终端）
cd AI_Scientist_v2/frontend
npm ci && npm run dev         # → http://localhost:5173
```

### 方式 B：Docker 一键

```bash
cd AI_Scientist_v2
docker compose up --build
# → http://localhost:8000 （前端 SPA + API 同端口）
```

### 方式 C：无需 Node（预构建 SPA）

`backend/static/` 已包含前端构建产物，`main.py` 自动检测并 serve。  
仅需 Python 即可完整体验所有功能：

```bash
cd AI_Scientist_v2/backend
pip install -r requirements.txt
python run.py
# 访问 http://localhost:8000
```

---

## 3. 赛题要求与方案映射

### 3.1 核心任务

| 赛题核心任务 | 本方案实现 | 对应模块 |
|---|---|---|
| 基于国产开源大模型（Qwen）开发 | 基座模型全部为 Qwen，通过百炼调用 | `agents/qwen_client.py` |
| 多智能体系统（Multi-Agent）架构 | 16 Agent + Orchestrator 编排 | `agents/orchestrator.py` |
| 问题理解 | 科学问题解析、领域识别、约束提取 | `agents/knowledge_gap.py` |
| 知识整合 | 文献挖掘、知识库检索、事实提取 | `agents/literature.py` + `services/literature_search.py` |
| 关联发现 | 跨学科技术迁移、规律挖掘 | `agents/hypothesis.py` + `reflection.py` |
| 可验证假设生成 | 假设生成 + 实验设计 + 代码验证闭环 | `agents/analysis.py` + `services/experiment_engine.py` |
| 从「数据/文献输入」到「假设输出」闭环 | 题库流水线（9 阶段）端到端实现 | `api/v1/questions.py` |

### 3.2 能力项

| 赛题能力项 | 本方案实现 |
|---|---|
| (一) 文献挖掘与事实提取 | LiteratureAgent + DocumentPlannerAgent，结构化抽取 + 引用溯源 |
| (二) 逻辑驱动的假设生成 | HypothesisAgent（归纳）+ DesignAgent（演绎），Pydantic 契约约束 |
| (三) 论证可行与多轮迭代 | ReflectionAgent 反思循环 + ReviewAgent 门禁 + IterationRecord |
| (四) 智能体思辨与人在回路 | 评审反馈接口 + 假设修订 + 前端协作 UI |

### 3.3 生成结果规范

赛题要求《科学假设与研究计划》包含以下字段，本平台**全部支持并自动生成**：

| 规范字段 | 对应字段 | 说明 |
|---|---|---|
| 待研究问题 | `Hypothesis.problem_statement` | 领域局限性 |
| 解决思路 | `Hypothesis.rationale` | 逻辑推导链 |
| 技术手段 | `Hypothesis.technical_details` | 具体方法 |
| 数据集 | `Hypothesis.datasets` | Source + Target |
| 标题/摘要/方法论 | `paper_title` / `abstract` / `methods` | 学术规范 |
| 实验设计 | `Hypothesis.experiments` | 基线 + 指标 |
| 实验结果 | `ExperimentRun` 产物 | 代码级验证 |
| 参考论文 | `Hypothesis.references` | **严禁虚构，真实文献** |

### 3.4 技术基础

| 赛题要求 | 本方案 |
|---|---|
| 基座必须基于 Qwen | ✅ qwen-max / qwen-vl-max |
| 通过百炼调用 | ✅ DashScope SDK |
| 技术方案文档 ≤ 20 页 | ✅ `docs/技术方案.pdf`（15 页） |
| 可交互前端 | ✅ Vue 3 SPA |
| 源代码完整可复现 | ✅ 本仓库 |

---

## 4. 评分标准对照（100 分拆解）

| 评分项 | 分值 | 本方案得分点 |
|---|---|---|
| 核心假设创新性与自洽性 | 20 | 多 Agent 交叉论证 + Reflection + 真实文献 |
| 方案可落地验证性 | 20 | 实验模拟场代码级验证 + 125 题批量生成 |
| 多智能体协作设计 | 15 | 16 Agent + Orchestrator + 反思循环 |
| 多模态大模型处理成效 | 15 | Qwen-VL 解析科学图像 |
| 实际场景问题支撑 | 10 | 自然科学 + 人文社科双赛道 |
| 论文/专利转化潜力 | 10 | 标准化输出可直接投稿 |
| 代码与结果可复现性 | 10 | Docker + CI + Alembic + pytest 全通过 |
| **加分** 演示视频 + 国产模型 | +5 | 可交互前端 + 全链路 Qwen |

---

## 5. 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                  浏览器 / 评审                                         │
└──────────────────────┬───────────────────────────────────────────────┘
                       │  HTTP / SSE / WebSocket
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI 后端 (:8000)                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │
│  │  auth (JWT)  │  │  questions.py    │  │  experiment_lab.py  │    │
│  │  登录 / 注册 │  │  题库流水线 ★    │  │  沙箱执行 / 图表     │    │
│  └──────┬───────┘  └────────┬─────────┘  └─────────┬──────────┘    │
│         │                    │                       │               │
│         │            ┌───────▼────────┐              │               │
│         │            │  Orchestrator  │──────────────┐              │
│         │            │  (16 Agent)    │              │              │
│         │            └───────┬────────┘              │              │
│         │                    │ Qwen API               │              │
│         │            ┌───────▼────────┐              │              │
│         │            │ DashScope 百炼 │              │              │
│         │            │ qwen-max       │              │              │
│         │            │ qwen-vl-max    │              │              │
│         │            └────────────────┘              │              │
│         │                                            │              │
│         ▼                                            ▼              │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │  SQLAlchemy (async) → SQLite / PostgreSQL               │        │
│  │  Alembic Migration (0001 → 0002)                        │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  StaticFiles ← backend/static/ (前端 SPA 预构建)                    │
└──────────────────────────────────────────────────────────────────────┘
```

**关键设计**：
- 单端口部署：`main.py` 自动检测 `frontend/dist` 或 `backend/static`，无需额外 nginx
- progress_sync 每 5s 聚合 AgentTask 完成度 → QuestionTask.progress
- BackgroundTasks 异步执行流水线，前端 SSE/轮询获取状态

---

## 6. 技术栈

| 层面 | 选型 | 说明 |
|---|---|---|
| **基座大模型** | Qwen（qwen-max / qwen-plus / qwen-vl-max） | 国产开源，百炼调用 |
| 后端 | Python 3.12 + FastAPI 0.115 + Uvicorn | 异步高性能 |
| ORM | SQLAlchemy 2.0 async + Alembic | SQLite/PostgreSQL |
| 校验 | Pydantic 2 | 数据契约 |
| 认证 | python-jose + passlib/bcrypt | JWT HS256 |
| 科学计算 | numpy/pandas/scipy/matplotlib/seaborn | 实验验证 |
| PDF 导出 | WeasyPrint 69 + Jinja2 | 技术方案 / 报告生成 |
| 前端 | Vue 3.5 + TypeScript 5.7 + Vite 6 | SPA 可交互 |
| UI | Element Plus 2.14 + Tailwind CSS 3.4 | 组件库 + 原子样式 |
| 实时通信 | SSE + WebSocket + 轮询 | 进度推送 |
| 国际化 | vue-i18n 11 | 中英双语 |
| 文档渲染 | markdown-it + KaTeX + highlight.js | 公式 / 代码高亮 |
| 容器化 | Docker 单容器 + docker-compose | 一键部署 |
| CI | GitHub Actions | pytest + npm build |

---

## 7. 多智能体架构（16 Agent）

### 7.1 Agent 总览

| Agent | 文件 | 职责 |
|---|---|---|
| **Orchestrator** | `agents/orchestrator.py` | 中央编排器：状态机、调度、反思循环 |
| KnowledgeGapAgent | `agents/knowledge_gap.py` | 识别知识缺口、问题结构化 |
| LiteratureAgent | `agents/literature.py` | 文献检索、事实提取 |
| HypothesisAgent | `agents/hypothesis.py` | 归纳/演绎生成假设 |
| HypothesisValidator | `agents/hypothesis_validator.py` | 假设可证伪性校验 |
| DesignAgent | `agents/design.py` | 实验方案设计 |
| ExperimentPlanAgent | `agents/experiment_plan.py` | 实验步骤编排 |
| AnalysisAgent | `agents/analysis.py` | 数据分析与统计 |
| WritingAgent | `agents/writing.py` | 研究报告撰写 |
| ReviewAgent | `agents/review.py` | 结果评审门禁 |
| ReflectionAgent | `agents/reflection.py` | 反思迭代（人在回路核心） |
| DocumentPlannerAgent | `agents/doc_planner.py` | 文档结构规划 |
| QualityGateAgent | `agents/doc_quality.py` | 质量门禁 |
| SectionReviewerAgent | `agents/doc_reviewer.py` | 章节级审阅 |
| MultimodalEnricherAgent | `agents/doc_multimodal.py` | Qwen-VL 多模态增强 |
| BaseAgent | `agents/base.py` | 抽象基类（共享 Qwen 调用） |

### 7.2 协作模式

```
Orchestrator (中央状态机)
    ├── knowledge_gap → literature → hypothesis → design → ...
    │                                         ▲
    │                    ┌────────────────────┘
    │                    │
    │              [QualityGate] ──fail──▶ [ReflectionAgent]
    │                                          │
    └──── pass ◀── 修订后重新假设生成 ◀────────┘
```

### 7.3 人在回路

- `POST /api/v1/questions/feedback` — 评审反馈
- `POST /api/v1/projects/{id}/review` — 项目评审
- 前端协作 UI（评审 / 修订 / 采纳）

---

## 8. 九阶段流水线（从问题到假设）

| # | 阶段 | 对应赛题能力 |
|---|---|---|
| 1 | knowledge_gap | (一) 文献挖掘 |
| 2 | literature | (一) 避免断章取义 |
| 3 | hypothesis | (二) 逻辑驱动 |
| 4 | design | (三) 论证可行 |
| 5 | experiment_plan | (三) 多轮迭代 |
| 6 | analysis | 可验证性 |
| 7 | writing | 标准化输出 |
| 8 | review | 自洽性 |
| 9 | reflection | (四) 人在回路 |

**内置模式**：

| 模式 | 阶段范围 | 用途 |
|---|---|---|
| `builtin_default_mode` | 全部 9 阶段 | 完整科研闭环 |
| `builtin_quick_analysis` | 1-3 | 快速分析 |
| `builtin_literature_hypothesis` | 1-4 | 文献+假设 |

内置 **125 题 Science 前沿科学问题**，覆盖自然科学 + 人文社科（赛题双赛道）。

---

## 9. 实验执行引擎与可验证性

```
POST /api/v1/experiment-lab/run
   │  { code, data_table, timeout, generate_video }
   ▼
_build_wrapper(): 动态生成 _run.py
   • import numpy/pandas/matplotlib/seaborn
   • df = pd.DataFrame(data_table)
   • patch plt.savefig → 自动收集图表
   • animation.FuncAnimation → 捕获视频
   ▼
subprocess 隔离运行（超时控制）
   ▼
ExperimentRun { status, output_text, charts, video_path }
```

**可验证性闭环**：假设 → 实验设计 → 代码执行 → 图表/视频产物 → 验证结论

---

## 10. 标准化输出：《科学假设与研究计划》

自动生成符合赛题规范，对应数据库 `Hypothesis` 模型：

```json
{
  "problem_statement": "在[领域]中，现有方法存在[具体局限性]...",
  "rationale": "基于[已知事实A、B]，通过[归纳/演绎]推导出...",
  "technical_details": ["统计方法: ...", "ML: GNN/Transformer", ...],
  "datasets": { "source": "...", "target": "..." },
  "paper_title": "基于[方法]的[领域][现象]研究",
  "abstract": "背景... 方法... 预期结果...",
  "methods": "1. 数据清洗 2. 特征工程 3. 模型构建...",
  "experiments": { "baselines": [...], "metrics": [...] },
  "results": "通过[代码执行]验证...",
  "references": [{"title": "真实文献", "doi": "...", "year": 2023}]
}
```

---

## 11. 多模态能力

- **模型**：qwen-vl-max（Qwen-VL）
- **模块**：`agents/doc_multimodal.py`（MultimodalEnricherAgent, 134 行）
- **能力**：解析实验图像/图表、提取定量信息、注入研究报告
- **接口**：`POST /api/v1/multimodal/analyze-image`

---

## 12. 认证与前后端通信

**JWT 流程**：

```
POST /api/v1/auth/login { username, password }
  → { access_token (24h), refresh_token (30d) }
  → Authorization: Bearer <token>
```

**进度更新**：

| 方式 | 场景 |
|---|---|
| 轮询 Polling | 题库/项目状态（`usePolling`） |
| SSE | 实时事件流（`/api/v1/stream/events`） |
| WebSocket | 实验运行 |

**开发代理**：Vite `server.proxy['/api']` → `http://localhost:8000`

---

## 13. 配置与环境变量

所有变量在 `backend/.env`（样板 `backend/.env.example`），由 `app/config.py` 加载。

| 变量 | 说明 |
|---|---|
| `QWEN_API_KEY` | **百炼 API Key（必填）** |
| `QWEN_MODEL_NAME` | qwen-max |
| `QWEN_VISION_MODEL` | qwen-vl-max |
| `DATABASE_URL` | sqlite+aiosqlite:///./zhixing.db |
| `SECRET_KEY` | JWT 密钥（⚠️ 生产必换随机字符串） |
| `ADMIN_PASSWORD` | 初始管理员密码（⚠️ 部署前必换） |
| `ALLOWED_ORIGINS` | CORS 白名单 |
| `RATE_LIMIT_PER_MINUTE` | API 限流 60/min |

---

## 14. 目录结构

```
AI_Scientist_v2/
├── backend/
│   ├── run.py                  # 启动入口
│   ├── requirements.txt        # 生产依赖
│   ├── requirements-dev.txt    # 开发/测试依赖
│   ├── .env.example            # 环境变量样板
│   ├── Dockerfile              # 单容器镜像（含 SPA）
│   ├── .dockerignore           # 构建忽略
│   ├── alembic.ini             # 数据库迁移配置
│   ├── migrations/             # Alembic 迁移版本 (0001→0002)
│   ├── app/
│   │   ├── main.py             # FastAPI 装配 + SPA 挂载
│   │   ├── config.py           # pydantic-settings
│   │   ├── api/v1/             # 97 个端点（auth/questions/projects/...）
│   │   ├── agents/             # 16 Agent + Orchestrator
│   │   ├── services/           # 业务逻辑（沙箱/文献/知识库/...）
│   │   ├── database/           # SQLAlchemy 模型 + 初始化
│   │   ├── schemas/            # Pydantic 数据契约
│   │   ├── security/           # JWT / PromptGuard / 限流
│   │   ├── core/              # progress_sync / exceptions
│   │   └── observability/      # 链路追踪 + 成本统计
│   ├── static/                 # 前端 SPA 预构建产物
│   ├── scripts/                # 工具脚本（PDF 生成等）
│   └── tests/                  # pytest 测试
├── frontend/
│   ├── package.json / vite.config.ts
│   └── src/
│       ├── views/              # 页面组件
│       ├── stores/             # Pinia 状态管理
│       ├── api/modules/        # Axios 接口封装
│       ├── components/         # 通用组件
│       ├── composables/        # useSSE / usePolling
│       ├── i18n/               # 中英双语
│       └── data/               # 125 科学问题集
├── docs/                       # 交付文档
│   ├── 技术方案.md             # 评审核心（462 行）
│   ├── 技术方案.pdf            # 15 页 PDF（≤20 页要求）
│   ├── 快速开始.md             # 部署指南
│   └── 提交清单.md             # 赛题材料对照
├── .github/workflows/ci.yml    # GitHub Actions CI
├── docker-compose.yml          # 单容器一键部署
├── .gitignore
└── README.md                   ← 你在这里
```

---

## 15. API 参考（核心端点）

Base URL：`http://localhost:8000`，前缀 `/api/v1`。

| 分组 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 认证 | POST | `/auth/login` | 登录 |
| 题库 | POST | `/questions/batch-generate` | **批量生成（流水线入口）** |
| 题库 | GET | `/questions/tasks/{id}` | 任务状态/进度 |
| 题库 | GET | `/questions/tasks/{id}/document` | 下载《科学假设与研究计划》 |
| 题库 | POST | `/questions/feedback` | **人在回路反馈** |
| 项目 | POST | `/projects/{id}/start` | 启动流水线 |
| 项目 | POST | `/projects/{id}/review` | **人在回路评审** |
| 实验场 | POST | `/experiment-lab/run` | 运行验证代码 |
| 实验场 | GET | `/experiment-lab/status/{run_id}` | 结果/图表/视频 |
| 多模态 | POST | `/multimodal/analyze-image` | **Qwen-VL 图像分析** |
| 知识库 | POST | `/knowledge/upload` | 上传文档 |
| 可观测 | GET | `/observability/cost` | 成本统计 |
| 健康 | GET | `/api/health` | 健康检查 |

---

## 16. 数据库 Schema

核心定义在 `backend/app/database/models.py`（524 行，27 表）。

| 模型 | 说明 |
|---|---|
| `User` | 用户/管理员 |
| `Project` | 研究项目 |
| `QuestionTask` | 题库任务（status/progress/document_path） |
| `ScienceQuestion` | 科学问题库（125 题） |
| `Hypothesis` | 生成假设（标准化 13 字段） |
| `AgentTask` | 单步 Agent 任务 |
| `ExperimentRun` | 实验运行（图表/视频） |
| `TraceRecord` / `CostRecord` | 链路追踪/成本 |

**迁移**：
```bash
cd backend
python -m alembic upgrade head   # 0001→0002
python -m alembic check          # 验证无 drift
```

---

## 17. 真实案例演示

### 案例 1：数学物理（Yang-Mills）

- **Problem**：标准模型在 Yang-Mills 质量间隙问题上存在理论缺口
- **Rationale**：基于规范场论 + Millennium 约束推导
- **Technical Details**：代数几何 + 数值格点 QCD
- **Experiments**：传统微扰论基线 + 质量间隙精度指标
- **References**：Clay Institute 官方说明、Atiyah 相关论文

### 案例 2：发展经济学（撒哈拉贫困）

- 违规行为识别 + 风险预警假设
- 行为数据/交易数据分析策略
- 面板数据固定效应 + 工具变量法

> 全部 125 题均可一键批量生成：`POST /api/v1/batch_run/run-125`

---

## 18. Docker 部署

### 单容器模式（推荐）

```bash
cd AI_Scientist_v2
docker compose up --build
```

**docker-compose.yml**：

```yaml
services:
  app:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: ./backend/.env
    ports: ['8000:8000']
    volumes:
      - zhixing-data:/app/data
      - ./backend/uploads:/app/uploads
      - ./backend/output:/app/output
    healthcheck:
      test: ['CMD', 'curl', '-fsS', 'http://127.0.0.1:8000/api/health']
```

### Dockerfile 特性

- `python:3.12-slim` 基底
- WeasyPrint 系统依赖（libpango/libcairo/libgdk-pixbuf）
- 中文字体 `fonts-noto-cjk`
- 前端 SPA 预构建产物 COPY 进镜像
- Alembic 迁移目录包含
- HealthCheck + 多 worker CMD

**手动构建**：

```bash
docker build -f backend/Dockerfile -t zhixing:3.0 backend/
docker run --rm -p 8000:8000 --env-file backend/.env zhixing:3.0
```

---

## 19. CI/CD

**`.github/workflows/ci.yml`**：

| Job | 内容 |
|---|---|
| backend | Python 3.12 → apt 安装 WeasyPrint 系统依赖 → pip → pytest (SQLite) |
| frontend | Node 20 → npm ci → npm run build → upload dist artifact |

触发条件：push/PR to main/develop + workflow_dispatch。

---

## 20. 测试策略

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q           # 预期：12 passed
```

| 层级 | 工具 | 范围 |
|---|---|---|
| 冒烟 | pytest + httpx | config 加载、models import、async engine |
| API | httpx.AsyncClient | 端点契约、认证、限流 |
| E2E（建议） | Playwright | 登录→创建→运行→验证 |

---

## 21. 可观测性与安全

**可观测**：
- 链路追踪：每次 Qwen/工具调用 → `TraceRecord`
- 成本统计：Token/金额实时追踪，超阈值自动告警
- 端点：`GET /api/v1/observability/traces`、`/cost`

**安全**：
- 全链路国产 Qwen（自主可控）
- `.env` 不入仓，SECRET_KEY / ADMIN_PASSWORD 须更换
- 实验代码沙箱隔离 + 超时
- JWT + CORS + 限流（60 req/min）
- Pydantic 严格输入校验
- AuditLog 审计关键操作

---

## 22. 已知问题与排坑

| 问题 | 根因 | 修复 |
|---|---|---|
| 进度 100% 但未完成 | progress_sync 只写 progress 不写 status | 原子绑定 + 运行中上限 95% |
| 阿里云欠费 Arrearage | DashScope 余额不足 | 充值 → 等待同步 → 重跑 |
| seaborn 简洁写法报错 | `sns.scatterplot(x='col')` 未传 data | wrapper 自动注入 |
| `_exec` 异常被吞 | BackgroundTask 未捕获 | try/except → status='failed' |
| Windows GBK 编码 | 控制台默认 GBK | `sys.stdout.reconfigure(encoding="utf-8")` |

---

## 23. 提交清单

| 赛题提交项 | 本仓库对应 |
|---|---|
| 技术方案文档（PDF ≤ 20 页） | `docs/技术方案.pdf`（15 页） |
| 源代码 | 本仓库 |
| 可交互前端 | `frontend/` Vue 3 SPA |
| 演示视频（≤10 分钟） | 录制后附入 |
| 百炼调用凭证/截图 | `docs/` |
| 报名表（盖章） | `docs/` |

**截止**：2026 年 9 月 5 日  
**提交地址**：https://survey.aliyun.com/apps/zhiliao/A4e_qqNGu

---

## 24. FAQ

**Q: 如何验证 Qwen 连通性？**  
A: `python -c "import dashscope; ..."` 返回 Pong 即正常。

**Q: 不用 Node 能跑吗？**  
A: 能。`backend/static/` 已包含预构建 SPA，直接 `python run.py` 即可访问完整前端。

**Q: 如何切换 PostgreSQL？**  
A: 改 `DATABASE_URL` + 装 asyncpg + `alembic upgrade head`。

**Q: 假设的参考文献会虚构吗？**  
A: 不会。全部来自 LiteratureAgent 真实检索。

**Q: 算力成本如何控制？**  
A: 阿里云 300 元/人补贴 + CostRecord 实时监控。

---

## 25. 许可证与致谢

- **竞赛专用**：挑战杯「揭榜挂帅」XH-202619 参赛作品
- **基座模型**：通义千问 Qwen（Apache 2.0 / 通义千问开源协议）
- **致谢**：阿里云算力补贴 + 百炼平台 + 中国科学院国家天文台 AI 推进委员会 + 他山学科交叉创新协会
