# 智研星枢 · AI Scientist v3

> **基于国产开源大模型（Qwen）的多智能体科研平台 + 课程课件中心**
>
> 挑战杯「揭榜挂帅」专项赛参赛作品 · 题目编号 **XH-202619**
> 发榜单位：浙江阿里巴巴云计算有限公司
> 基座模型：通义千问 Qwen（qwen-max / qwen-plus / qwen-vl-max）· 调用平台：阿里云百炼（DashScope）

---

## 0. 功能模块地图（想做什么，直接看这张表）

| 模块 | 侧边栏入口 | 路由 | 能做什么 | 主要后端 |
| --- | --- | --- | --- | --- |
| 工作台 | 📊 工作台 | `/` | 研究计划设计器、科研动态流、跨模块快捷入口 | `api/v1/projects.py` |
| AI 对话 | 💬 AI对话 | `/chat` | 多轮学术对话、文件/图片上传、`/skill` 指令派发技能 | `api/v1/chat.py` `stream.py` |
| 资料库 | 🗂️ 资料库 | `/knowledge` | 本地文档解析入库 + 外部学术检索（arXiv 等） | `knowledge.py` `knowledge_external.py` |
| **课程中心** | 🎓 课程中心 | `/courses` | 开课 / 选课 / 课程网站 / 学员进度 / PPT 电子化 | `courses.py`（`/courses`） |
| **课件工坊（生成 PPT）** | **📽️ AI 生成 PPT** | **`/courseware-studio`** | **给一个主题 → AI 产出整套课件（全程进度可视）→ 下载 `.pptx` / 导出讲义** | `POST /coursewares/quick-generate` |
| 课件阅读 | （课程内点开） | `/course/{id}/read/{cwId}` | 逐页阅读 · 📕 电子书 · 📄 学生/教师讲义 · AI 陈旧体检与更新 · 版本链 · 反向导出 pptx | `courses.py`（`/coursewares`） |
| 科学问题题库 | 🔬 科学问题题库 | `/questions` | Science 2005 125 题、研究方案生成、报告导出 | `questions.py` |
| 实验模拟场 | 🧪 实验模拟场 | `/experiment-lab` | 沙箱执行代码、产出图表/动画、模板复用 | `experiment_lab.py` |
| 技能市场 | 🛠️ 技能市场 | `/skills` | 内置 / 自主 prompt / git 与网络搜集的 webhook 外接技能 | `skills.py` |
| 自动化流水线 | ⚡ 自动化流水线 | `/automation` | 多 Agent 编排、定时触发、反馈迭代、断点续跑（retry-from） | `automation.py` `agents/orchestrator.py` |
| Agent 中心 | 🤖 Agent中心 | `/agents` | 单 Agent Playground 调试 | `agents.py` |
| 追踪 / 成本 | 🔍 追踪回放 · 💵 成本分析 | `/traces` `/cost` | Span 链路回放与 Token 花费统计 | `observability.py` |
| 管理后台 | 🛡️ 管理后台 | `/admin` | 用户、配额、系统开关 | `admin.py` |

**找「生成 PPT」的三个入口**：① 侧边栏 `📽️ AI 生成 PPT`（教师/研究员角色可见）；② 工作台「课程中心 · 课件工坊」条上的渐变主按钮；③ `Ctrl+K` 命令面板输入 `做 PPT`。
AI 对话页工具栏还有 `📽️` 按钮，可把当前项目（含对话记录）作为素材直接带进工坊。

---

## 1. 项目简介

**智研星枢（AI Scientist）** 面向「AI for Science」，基于国产开源大模型 Qwen 构建多智能体系统，实现从「科学问题输入」到「可验证科学假设输出」的全链路闭环，并向下延伸到**教学场景**：把研究产出直接变成能上课的课件。

```
文献 / 数据 / 科学问题
   │
   ▼
知识缺口识别 → 文献挖掘 → 假设生成 → 逻辑论证 / 多轮迭代 → 实验设计与验证
   │                                                            │
   ▼                                                            ▼
《科学假设与研究计划》（符合赛题规范）  ────联动────▶  课程中心 · 课件工坊（.pptx / 电子书）
```

### 核心特性

- **🤖 多智能体协作**：Orchestrator + 15 项 Agent 注册（9 阶段默认流水线），支持反思循环
- **🧪 代码级可验证**：实验模拟场沙箱执行，产出图表 / 动画，拒绝纸上谈兵
- **🎓 课程与课件闭环**：开课选课、PPT 电子化、AI 陈旧度体检与自动更新、一个主题秒出整套课件
- **🧩 跨模块素材**：课件生成可引用原资料、科学问题、研究报告、项目对话、流水线产出、技能结果
- **🖼️ 多模态**：Qwen-VL 处理图像与科学图表；文档上传支持分片与解析
- **🔁 一键复现**：Docker / pip + npm / 免 Node（预构建 SPA）/ Alembic 迁移
- **🔐 自主可控**：全链路 Qwen，满足赛题「国产模型」要求

### 关键指标（脚本实测，非估算）

| 指标 | 数值 |
| --- | --- |
| 后端 Python（`backend/app`） | 101 文件 / 15,829 行 |
| 前端 Vue + TS（`frontend/src`） | 59 文件 / 11,723 行 |
| REST API | 150 个操作 / 127 条唯一路径（课程中心 27：`/courses` 13 · `/coursewares` 14） |
| 数据表 | 26 张 |
| Agent | 15 项注册 · 9 阶段默认流水线 |
| 内置科学问题 | 125 题（Science 2005 前沿难题） |
| 前端视图 / 组件 / API 模块 | 18 / 12 / 13 |
| 单元测试 | 12 用例 pytest 全通过 |

---

## 2. 快速开始

### 方式 A：本地开发

```powershell
# 后端
cd AI_Scientist_v2\backend
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env         # 至少写入 QWEN_API_KEY=sk-xxxx
python -m app.database.init_db
python run.py --reload          # → http://localhost:8000

# 前端（新终端）
cd AI_Scientist_v2\frontend
npm ci && npm run dev           # → http://localhost:5173
```

### 方式 B：Docker 一键

```bash
cd AI_Scientist_v2
docker compose up --build
# → http://localhost:8000 （前端 SPA + API 同端口）
```

### 方式 C：免 Node（预构建 SPA）

`backend/static/` 已随仓库提供前端构建产物，`main.py` 自动检测并 serve：

```bash
cd AI_Scientist_v2/backend
pip install -r requirements.txt
python run.py
```

前端改动后的构建与同步：

```bash
cd AI_Scientist_v2/frontend && npm run build          # vue-tsc && vite build
robocopy dist ..\backend\static /MIR                  # 同步进后端
```

---

## 3. 生成文件都落在哪（固定目录）

**所有由系统生成的文件，统一写入 `backend/generated/`，与启动时的工作目录无关。**
路径由 `app/utils/paths.py` 单点计算（`Path(__file__).resolve()` 上溯到 backend 根），不再使用 `os.getcwd()` 或相对路径 —— 从任意目录启动都不会把文件散落到 `C:\Windows\system32` 之类的地方。

| 子目录 | 内容 | 主要产生方 |
| --- | --- | --- |
| `generated/reports/` | 项目研究报告（Markdown / PDF） | `agents/orchestrator.py` `api/v1/export.py` |
| `generated/questions/` | 科学问题任务产物（`task_{id}/report.md`） | `api/v1/questions.py` |
| `generated/deliverables/` | 赛题交付物（`project_{id}/`） | `orchestrator.py` `export.py` |
| `generated/pdf/` | PDF 报告（含挑战杯 125 篇汇总） | `export.py` |
| `generated/experiments/` | 实验沙箱输出（图表 PNG / 动画 / 数据） | `services/experiment_engine.py` |
| `generated/courseware/` | 课件逐页渲染图（`c{n}/cw{id}/s{idx}.jpg`） | `services/ppt_service.py` |
| `generated/exports/` | 反向导出的原生 `.pptx` | `GET /coursewares/{id}/export/pptx` |
| `generated/agent_output/` | Agent 文件工具产出 | `agents/tools/file_tools.py` |
| `generated/tmp/external/` | 外部采集临时文件 | `services/external_collector.py` |
| `generated/cache/literature/` | 文献检索缓存 | `services/literature_search.py` |

要点：

- 启动时 `paths.ensure_tree()` 自动建好整棵骨架，日志打印 `📁 生成文件目录（固定）: <绝对路径>`
- **历史数据不会丢**：读取统一走 `paths.resolve(stored, kind=...)`，按「绝对路径 → generated → 旧 `output/` → 旧 `uploads/`」顺序探测，老库里存的相对/绝对路径都能打开
- 数据库里只记录**相对路径**（`paths.rel()`，posix 风格），换机器、换部署目录都不影响
- `uploads/` 只放**用户上传的原件**（课件源 `.pptx`、文档、图片），生成物一律不进 uploads
- `generated/` 已整体 gitignore，仅保留 `.gitkeep` 骨架；Docker 里作为独立卷 `./backend/generated:/app/generated` 持久化
- 路径穿越已被拦截：`paths` 拒绝绝对片段与 `..`，清理脚本 `utils/cleanup.py` 只能在生成根内删除

---

## 4. 课程中心与课件工坊（PPT 全链路）

### 4.1 课件工坊：不用先建课程

`/courseware-studio` 是独立模块，填一个主题就能拿到可下载的 PPT：

```
主题 / 章节数 / 每章页数 / 风格 / 受众
        +（可选）勾选多源素材 → 🧩 引用资料库·题目·报告·项目对话·流水线·技能
        ↓
POST /api/v1/coursewares/quick-generate   →  立即返回 job_id（202，不阻塞 HTTP）
        ↓
①  未指定 course_id → 自动创建一门【仅自己可见】的草稿课程承载（不污染公开课列表）
②  AI 先出大纲，再逐章撰写 slides（分章调用，避免一次性输出 80 页被 max_tokens 截断）
③  生成小结页 + 课后思考题 + 延伸阅读 → 逐页渲染轻量配图 → 落库→电子书文本入资料库
        ↓  每一阶段写进进程内作业表（services/generate_progress.py）
GET /api/v1/coursewares/quick-generate/{job_id}   ← 前端每 1.2s 轮询，驱动真实进度条
        ↓
④  status=done 时 result 里拿到 courseware_id / slide_count / cost /
    pptx_url / ebook_url / handout_url / reader_url / sources_used
        ↓
⬇️ 下载 .pptx  ·  📕 电子书  ·  📄 学生讲义 / 🗒️ 教师讲义  ·  📖 逐页阅读  ·  ✏️ 逐页微调  ·  🎓 发布课程
```

**进度可视化**：阶段枚举 `material → outline → chapter → summary → render → persist`，
前端（`views/course/CoursewareStudio.vue` 与课程详情页的生成弹窗）展示百分比进度条、
已完成章节数 `x/y`、已产出页数与逐条阶段日志；作业进度只存内存 30 分钟（服务重启或过期后
结果仍可在右侧「我生成过的课件」与课程页拿到）。

右侧「🗂️ 我生成过的课件」来自 `GET /api/v1/coursewares/ai-mine`，随时回看、再下载、按同样参数重跑。

> ⚠️ 路由顺序敏感：`/coursewares/ai-mine`、`/coursewares/quick-generate` 必须声明在 `/coursewares/{cw_id}` 之前，否则会被当成 `cw_id` 参数（FastAPI 按声明顺序匹配）。
> 下载类端点（`export/pptx`、`ebook`、`handout`）走 `get_current_user_flexible`，因为 `<a href>` 不会带 `Authorization` 头，前端用 `?token=` 认证。

### 4.2 课程中心： teaching 场景闭环

| 能力 | 说明 | 端点 |
| --- | --- | --- |
| 开课 / 课程网站 | 课程元信息、大纲、章节、封面 emoji、公开/私有、发布态 | `POST/PATCH /courses` |
| 选课与进度 | 学生自助选课、逐页阅读进度折算、断点续读 | `/courses/{id}/enroll` `POST /coursewares/{id}/progress` |
| **PPT 电子化** | 上传 `.pptx` → 拆成文本层 + 逐页瘦身图，首屏只加载几十 KB | `POST /courses/{id}/courseware` |
| AI 陈旧度体检 | 逐页打风险分、给出过时原因与修改建议 | `POST /coursewares/{id}/staleness-scan` |
| **AI 自动更新** | 只重写高风险页，生成新版本并保留版本链（原稿可回溯） | `POST /coursewares/{id}/ai-refresh` |
| 快速做课件 | 依托大纲 + 多源素材生成整套 deck（异步作业，可轮询进度） | `POST /coursewares/quick-generate` · `GET /coursewares/quick-generate/{job_id}` |
| 流水线转讲义 | 把研究流水线成功运行的产出变成课件 | `POST /courses/{id}/sync-from-pipeline` |
| AI 拟大纲 | 从长文本抽课程标题、领域与章节 | `POST /courses/ai/outline` |
| 电子书阅读 | 连贯读物 Markdown（真正的电子书形态，适合当书读） | `GET /coursewares/{id}/ebook` |
| **课堂讲义** | 按章分组的发放物：学生版（要点 + 笔记留白 + 课后思考题）/ 教师版（另附讲师速记、每章时长建议、陈旧页警示），本地渲染 Markdown 不花 token | `GET /coursewares/{id}/handout?audience=student\|teacher` |
| 反向导出 | 电子化后的课件仍可导出原生 `.pptx`，不改变老师的上课习惯 | `GET /coursewares/{id}/export/pptx` |

### 4.3 跨模块联动

| 从哪来 | 到哪去 | 效果 |
| --- | --- | --- |
| 资料库文件 | 课件工坊 / AI 更新 | 作为参考素材注入 prompt，并可追溯引用来源 |
| 科学问题 / 研究报告 | 课件工坊 | 把题目与结论直接写进课件 |
| AI 对话项目 | 课件工坊（`📽️` 按钮） | 带上项目上下文 + 最近对话记录 |
| 自动化流水线 run | 课程中心 | 一次成功运行 → 一份讲义课件 |
| 技能市场（内置 / 自主 / git·webhook 外接） | 课件生成 | 技能运行结果叠加进 deck |
| 课件电子书 | 资料库 | 电子化后自动注册为文档，可被检索与引用 |

---

## 5. 系统架构

```
┌─ 浏览器（Vue 3 SPA，vite build 产物由后端 static 直出）
│
├─ FastAPI · /api/v1
│   ├─ 认证 JWT（access / refresh，支持 ?token= 的 flexible 模式）
│   ├─ SSE 实时通道（流水线进度、Token 流、实验状态）
│   ├─ REST：projects · questions · courses · coursewares · automation
│   │        skills · knowledge(+external) · documents · evidence · export
│   │        chat · stream · multimodal · experiment-lab · observability · admin · team · batch
│   └─ Orchestrator（多 Agent 编排 + 反思循环 + retry-from 断点续跑）
│
├─ 服务层：qwen_client · literature_search · experiment_engine · ppt_service
│          course_ai_service · external_collector · skill_engine · …
├─ 数据层：SQLAlchemy 2.x async + SQLite（aiosqlite），Alembic 迁移
└─ 文件层：uploads/（用户原件） · generated/（系统产物，固定根） · logs/（滚动日志）
```

## 6. 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite 6 · Pinia · vue-router · TailwindCSS · Element Plus · KaTeX |
| 后端 | Python 3.11+ · FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · Alembic |
| 模型 | Qwen-Max / Plus（文本）· Qwen-VL-Max（多模态）· DashScope SDK |
| 课件 | python-pptx（解析与反向导出）· Pillow（逐页渲染与压缩） |
| 实验 | matplotlib / numpy / pandas，子进程沙箱执行 |
| 部署 | Docker Compose · 单端口同时提供 SPA 与 API |

## 7. 多智能体与九阶段流水线

默认工作流（可在自动化模块自定义顺序、增删步骤，支持从任意阶段续跑）：

```
knowledge_gap → literature → hypothesis → design → experiment_plan
              → analysis → writing → review → reflection
```

另有文档生成工作流（`document_planner → section_writer → quality_gate → revision → multimodal_enricher`）与
`AGENT_REGISTRY` 中的 15 项注册（含 `experiment` 别名）。任一 Agent 都可在 Agent 中心单独调试并观察其 Trace。

## 8. 实验执行引擎

`services/experiment_engine.py` 在 backend 生成的隔离目录中执行代码，产出图表、动画与指标，全部写入
`generated/experiments/`；前端「实验模拟场」通过 `/experiment-lab/chart/{run}/{file}` 与 `/video/{run}` 懒加载。
沙箱限制执行时长、内存与网络，失败信息回灌反思循环。

## 9. 目录结构

```
AI_Scientist_v2/
├── backend/
│   ├── app/
│   │   ├── agents/            # 25 个 Agent 文件 + orchestrator + tools
│   │   ├── api/v1/            # 22 个端点模块（courses.py 含课程 + 课件双 router）
│   │   ├── services/          # 16 个服务：qwen_client / ppt_service / course_ai_service / generate_progress / …
│   │   ├── schemas/           # Pydantic 契约
│   │   ├── database/          # models（26 表）· session · init_db · Alembic
│   │   ├── core/ · security/  # 事件总线 · 加密 · JWT · 速率限制
│   │   ├── utils/paths.py     # ★ 生成文件唯一路径入口
│   │   ├── observability/     # tracer · 成本统计
│   │   └── main.py            # 路由注册 · SPA 托管 · 启动建树
│   ├── generated/             # ★ 所有系统生成文件（gitignore，保留骨架）
│   ├── uploads/               # 用户上传原件
│   ├── static/                # 前端构建产物（免 Node 运行）
│   ├── logs/ · tests/ · migrations/
│   └── run.py · requirements.txt · .env
├── frontend/
│   └── src/{api,components,composables,router,stores,types,views,i18n,…}
├── docker-compose.yml · Dockerfile
└── README.md
```

## 10. 配置与环境变量

`backend/.env`（片段）：

```ini
APP_NAME=智研星枢
APP_VERSION=3.0.0
SECRET_KEY=change-me-in-prod
DATABASE_URL=sqlite+aiosqlite:///./zhixing.db
QWEN_API_KEY=sk-xxxx
QWEN_MODEL=qwen-max
QWEN_VL_MODEL=qwen-vl-max
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

路径类配置在 `app/config.py` 里已改为**绝对默认值**，通常无需覆盖：

| 配置 | 默认值 | 含义 |
| --- | --- | --- |
| `UPLOAD_DIR` | `<backend>/uploads` | 用户上传原件 |
| `GENERATED_DIR` | `<backend>/generated` | 系统生成文件唯一根 |
| `LOG_DIR` | `<backend>/logs` | 滚动日志 |

## 11. API 参考

统一前缀 `/api/v1`，除 `/api/health` 外均需 `Authorization: Bearer <token>`（下载/图片类端点可用 `?token=`）。

| 模块 | 前缀 | 端点数 | 代表端点 |
| --- | --- | --- | --- |
| 认证 | `/auth` | 5 | `POST /auth/login` · `/auth/refresh` |
| 项目 | `/projects` | 13 | `POST /projects` · `/projects/{id}/pipeline` |
| 科学问题 | `/questions` | 19 | `POST /questions/{qid}/research` · `GET /questions/{qid}/report` |
| 课程中心 | `/courses` | 13 | `POST /courses` · `/{id}/courseware` · `/{id}/sync-from-pipeline` · `/ai/outline` |
| 课件 | `/coursewares` | 14 | `POST /quick-generate` · `GET /quick-generate/{job_id}` · `GET /ai-mine` · `/{id}/staleness-scan` · `/{id}/ai-refresh` · `/{id}/ebook` · `/{id}/handout` · `/{id}/export/pptx` · `/{id}/versions` |
| 自动化 | `/automation` | 12 | `POST /{pid}/run` · `/{pid}/run-from` · 定时与反馈迭代 |
| 实验模拟场 | `/experiment-lab` | 12 | `POST /run` · `GET /status/{run}` · `/chart/…` · `/video/{run}` |
| 资料库 | `/knowledge` · `/knowledge/external` | 9 · 5 | 上传解析 · 检索 · 外部学术源 |
| 技能市场 | `/skills` | 4 | 内置 / prompt 自主 / git·webhook 外接 |
| 对话 · 推送 | `/chat` · `/stream` | 5 · 1 | 多轮对话 · SSE |
| 多模态 · 文档 · 证据 | `/multimodal` · `/documents` · `/evidence` | 7 · 5 · 5 | 图文理解 · 分片上传 · 证据链 |
| 观测 · 管理 | `/observability` · `/admin` | 3 · 3 | Trace 回放 · 成本 · 用户管理 |
| 导出 · 批量 · 团队 | `/export` · `/batch` · `/projects(team)` | 1 · 2 · 2 | 赛题文档一键导出 |

完整交互文档：启动后访问 `/docs`（Swagger）或 `/redoc`。

## 12. 数据库 Schema（26 表）

| 分组 | 表（`__tablename__`） |
| --- | --- |
| 用户与协作 | `users` · `project_shares` · `notifications` · `audit_logs` |
| 科研项目与执行 | `projects` · `agent_tasks` · `tool_calls` · `chat_messages` · `documents` · `upload_chunks` |
| 观测与成本 | `trace_records` · `cost_records` |
| 假设与迭代 | `hypotheses` · `iteration_records` |
| 流水线 | `pipelines` · `pipeline_runs` · `pipeline_run_logs` |
| 科学问题 | `science_questions` · `question_tasks` |
| 实验 | `experiment_runs` · `experiment_templates` |
| 技能 | `custom_skills` |
| 课程与课件 | `courses` · `coursewares` · `slides` · `enrollments` |

> 课件相关四表是课程中心的地基：`Courseware` 只存元数据与体积统计，页面正文存在 `Slide`（文本层 + 逐页图路径），
> AI 更新不覆盖原稿而是新开一条 `Courseware` 并用 `parent_id` 串成版本链；`Enrollment` 记录选课、进度与断点。

迁移：`alembic revision --autogenerate -m "..."` + `alembic upgrade head`；全新环境可直接 `python -m app.database.init_db`。

## 13. Docker 部署

`docker-compose.yml`（实际配置，单容器同时提供 SPA 与 API）：

```yaml
services:
  app:
    build: { context: ./backend, dockerfile: Dockerfile }
    env_file: ["./backend/.env"]
    ports: ["8000:8000"]
    volumes:
      - zhixing-data:/app/data                    # SQLite（命名卷）
      - ./backend/uploads:/app/uploads            # 用户上传原件
      - ./backend/generated:/app/generated        # ★ 系统生成文件唯一根
      - ./backend/output:/app/output             # 历史产物（只读兼容）
    healthcheck: ["...", "http://127.0.0.1:8000/api/health"]
```

```bash
cd AI_Scientist_v2
docker compose up --build     # → http://localhost:8000 ｜ /docs
```

Dockerfile 已 `mkdir -p /app/generated`，容器内路径与本地完全一致；环境变量 `DATABASE_URL` 在容器内指向 `./data/zhixing.db`。

## 14. 质量闸门（本地执行）

项目未随仓提供 CI 配置文件；推荐在提交前执行下面三步（已验证均绿）：

```bash
cd AI_Scientist_v2/frontend && npm run build        # vue-tsc 类型检查 + vite build
cd ../backend  && python -m pytest tests -q         # 12 用例
robocopy ../frontend/dist ./static /MIR         # 同步免 Node 产物
```

若需接入 CI，直接把上面三段写进 `.github/workflows/ci.yml` 即可。

## 15. 测试

```bash
cd AI_Scientist_v2/backend
pytest tests -q          # 12 用例，约 1s 跑完（不依赖外部 API Key）
```

| 文件 | 覆盖 |
| --- | --- |
| `tests/test_smoke.py` | `app.main` 可导入（无循环依赖/语法错误）· `AGENT_REGISTRY` 含 9 阶段全部 Agent · 每个 Agent 具备 `name/display_name/build_prompt/system_prompt` · `/api` 路由数量下限 · `/api/health` 返 ok+版本 |
| `tests/test_experiment_engine.py` | 实验引擎：沙箱执行、图表产出、超时与失败回灌 |

未覆盖部分（课程/课件、路径解析）目前以端到端冒烟脚本 + 人工验证为主；后续可为 `courses.py` 与
`utils/paths.py` 补上 pytest（重点：跨角色权限、版本链不覆盖原稿、旧路径回退、`..` 穿越拒绝）。

## 16. 可观测性与安全

- **Trace**：每个 Agent 步骤生成 span，落库后可在 `/traces` 逐层回放，含输入输出与耗时
- **成本**：按模型统计 prompt/completion token 与金额，`/cost` 汇总，流水线级别可归因到项目
- **认证**：JWT access + refresh（`python-jose`），密码 passlib/bcrypt 散列；student / teacher / researcher / admin 角色分级，课程与课件按 owner 校验
- **文件安全**：文件名 sanitize + 扩展名白名单 + 大小上限；生成文件路径统一经 `paths` 校验，拒绝 `..` 与绝对路径注入
- **执行安全**：实验代码在受限子进程运行，超时/超限即终止；外部 webhook 技能带签名与超时
- **速率限制**：登录与生成类接口按 IP 限流

## 17. 已知问题与排坑

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| Windows 下 `python -c "..."` 报 `unterminated string literal` | cmd 撕裂引号 | 写成临时脚本执行 |
| 静态路由 404 / 422 | FastAPI 按声明顺序匹配，`/{id}` 在前会吞掉静态段 | 静态路径（`ai-mine`、`quick-generate`）先声明 |
| `MissingGreenlet` | SQLAlchemy async 下懒加载关系 | 显式 `selectinload` 或 `.unique().all()` |
| 生成的文件到处乱跑 | 曾使用 `os.getcwd()` / 相对路径 | 已全部改为 `app/utils/paths.py` 绝对根 |
| 老课件图片打不开 | 历史数据存的是 `uploads/courses/…` 或绝对路径 | `paths.resolve()` 自动回退旧根，无需迁移 |
| PPT 解析失败 | `.ppt` 旧二进制格式 | 先在 Office 里另存为 `.pptx` |
| 刷新页面后生成进度条消失 | 作业进度只存进程内（TTL 30 分钟），服务重启即失效 | 生成结果已落库，去「我生成过的课件」或课程页拿；无需重新生成 |
| 后台生成报错但页面不提示 | 失败信息写在作业表的 `error` 字段 | 轮询到 `status=failed` 会显示红色提示；也可 `GET /coursewares/quick-generate/{job_id}` 直查 |
| 聚合报告写进大模型时报 `SyntaxError: '(' was never closed` | f-string 里嵌了同种引号（PEP 701 仅 Py3.12+ 合法），如 `f"{'、'.join(x)}"` | 先在外部算好变量再插值 |
| 讲义/电子书里表格只剩一行表头 | `Slide.tables` 是 `[表格[行[单元格]]]` 三层，易误当成单行 | 按 `tbl[0]` 表头、`tbl[1:]` 正文渲染，单元格内的 `|` 转全角｜ |

## 18. FAQ

**Q：生成 PPT 的入口在哪？**
A：侧边栏 `📽️ AI 生成 PPT`（`/courseware-studio`）。若看不到，说明当前账号不是 teacher/researcher/admin 角色 —— 学生账号只做阅读与选课。

**Q：生成过程中有进度吗？**
A：有。`POST /coursewares/quick-generate` 立即返回 `job_id`（不阻塞 HTTP），前端每 1.2s 轮询
`GET /coursewares/quick-generate/{job_id}`，展示阶段步骤条（聚合素材 → 拟大纲 → 逐章撰写 →
小结与思考题 → 逐页配图 → 落库归档）、百分比进度条、已完成章节 `x/y` 与已产出页数。
课件工坊与课程详情页的生成弹窗用的是同一套作业接口。

**Q：电子书和讲义有什么区别？**
A：`GET /coursewares/{id}/ebook` 把整套 PPT 写成连贯读物，适合当一本书从头读到尾；
`GET /coursewares/{id}/handout?audience=student|teacher` 是**课堂发放物**：按章分组 + 每页要点，
学生版附笔记留白与课后思考题，教师版附讲师速记、每章时长建议与陈旧页警示。两者都是本地
渲染的 Markdown（不花 token），浏览器直接打开或 Ctrl+P 打印。

**Q：工坊生成的课件会出现在公开课列表里吗？**
A：不会。未指定课程时自动建一门 `visibility=private` 的草稿课程承载，你确认内容后再手动发布。

**Q：AI 生成的课件能改吗？**
A：能。逐页可编辑标题/要点/讲者备注（`PATCH /coursewares/{id}/slides`），改完仍导出为 `.pptx`。

**Q：AI 会不会把原来的课件覆盖掉？**
A：不会。AI 更新走「新版本 + 版本链」，`GET /coursewares/{id}/versions` 可看每一版并回溯原稿。

**Q：能引用我自己的资料吗？**
A：能，且不限于资料库 —— 原文件、科学问题、研究报告、项目对话、流水线成功运行、技能（含 git/网络搜集的外接 skill）都可勾选，结果里会列出实际注入的素材源。

**Q：换台机器跑，历史文件还在吗？**
A：只要 `backend/generated/`（产物）与 `backend/uploads/`（原件）以及 `zhixing.db` 一起搬走就都在；数据库中存的是相对路径。

## 19. 许可证与致谢

本项目为挑战杯「揭榜挂帅」专项赛参赛作品，基座模型为阿里巴巴通义千问 Qwen，通过阿里云百炼（DashScope）调用。
感谢发榜单位浙江阿里巴巴云计算有限公司提供赛题与算力支持。
