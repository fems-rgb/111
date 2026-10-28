# 智研星枢 · AI Scientist v3

> **基于国产开源大模型（Qwen）的多智能体科研平台 + 课程课件中心**
>
> 挑战杯「揭榜挂帅」专项赛参赛作品 · 题目编号 **XH-202619**
> 发榜单位：浙江阿里巴巴云计算有限公司
> 基座模型：通义千问 Qwen（qwen-max / qwen-plus / qwen-vl-max）· 调用平台：阿里云百炼（DashScope）
> 多供应商可选：DeepSeek / Kimi（Moonshot）/ 智谱 GLM / 任意 OpenAI 兼容端点 —— 配了对应密钥即在顶栏模型切换器与所有生成入口可选

---

## 目录

- **0.** 功能模块地图 · **1.** 项目简介（核心特性 / 关键指标）· **2.** 快速开始（本地 / Docker / 免 Node）
- **3.** 生成文件目录 · **4.** 课程中心与课件工坊（PPT 全链路）· **5.** 平台治理（模型·预警·预测·图谱·计划）
- **6.** 系统架构 · **7.** 技术栈 · **8.** 多智能体九阶段 · **9.** 实验引擎 · **10.** 目录结构
- **11.** 配置与环境变量 · **12.** API 参考 · **13.** 数据库 Schema（33 表）
- **14.** Docker 部署（单容器 · 开发/体验）· **15.** 质量闸门 · **16.** 测试 · **17.** 可观测性与安全
- **18.** 已知问题与排坑 · **19.** FAQ · **20.** 多端形态（PWA·原生 App·小程序）
- **21.** 可扩展性（Redis 分布式 · 生成队列 · PostgreSQL）· **22.** 一键上云（生产编排）· **23.** 许可证与致谢

> **两条部署路径**：① 单容器一体化（`docker-compose.yml` + `backend/Dockerfile`，SPA+API 同端口，§2 / §14）适合本地与小规模；② 生产上云（`deploy/`：nginx → app×N → PostgreSQL + Redis，§22）适合多副本横向扩展。二者数据同源、代码同一套。

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
| 追踪 / 成本 | 🔍 追踪回放 · 💵 成本分析 | `/traces` `/cost` | Span 链路回放；Token 花费统计 + 30 天历史 + 本月费用线性预测 | `observability.py` `services/prediction.py` |
| **计划中心** | 🗒️ 计划中心 | `/plans` | 个人 / 团队(项目) / 流水线 / AI 自主 四形态计划；AI 按主题拆解；流水线计划一键转 Pipeline 执行 | `plans.py` |
| **AI 通识课** | 🌐 AI 通识课 | `/general` | 图文微课 · 随堂自测 · AI 助教 · 课程知识图谱 · 学习进度预测 | `general_courses.py` |
| **知识图谱** | （四处内嵌） | 通识课详情 / 课程详情 / 资料库 / 项目详情 | 一张表四个 scope，AI 抽取 or 零 LLM 组装，自研 SVG 力导向交互 | `graphs.py` |
| 管理后台 | 🛡️ 管理后台 | `/admin` | 用户、配额、系统开关 | `admin.py` |

**顶栏两个全局控件**：`◀ 模型 ▶` 切换器 —— 一处选定，全站所有 AI 生成入口生效（localStorage 持久化，「自动」档按模式定档）；`🔔` 预警铃铛 —— 60s 轮询 `/api/v1/alerts`，成本超阈 / 模型限流 / 供应商密钥缺失 / 任务失败四类聚合，按严重级分组可直接跳转。

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
- **🔀 多模型供应商**：Qwen 系为默认基座，DeepSeek / Kimi / GLM / 自定义 OpenAI 兼容端点配密钥即用；顶栏全局切换 + 各生成面板下拉旁 ◀▶ 循环，优先级「面板显式选择 > 全局首选 > 模式档位」
- **📈 线性预测与预警**：本月成本、任务 ETA、学习完课天数三类最小二乘外推，统一 `/alerts` 预警中心承载
- **🕸️ 通用知识图谱**：一张表四个 scope（通识课 / 大纲 / 知识库 / 项目），零依赖 SVG 力导向组件内嵌四处视图
- **🗒️ 自由计划中心**：个人 / 团队 / 流水线 / AI 自主四形态，AI 拆解主题后可一键转 Pipeline 真正跑起来
- **🔁 一键复现**：Docker / pip + npm / 免 Node（预构建 SPA）/ Alembic 迁移
- **🔐 自主可控**：默认全链路 Qwen，满足赛题「国产模型」要求；多供应商为可选增强，不配密钥不出现在切换列表

### 关键指标（脚本实测，非估算）

| 指标 | 数值 |
| --- | --- |
| 后端 Python（`backend/app`） | 115 文件 / 22,909 行 |
| 前端 Vue + TS（`frontend/src`） | 76 文件 / 16,577 行 |
| REST API | 178 个操作 / 145 条 `/api` 路径 |
| 数据表 | 33 张（含 `knowledge_graphs` · `plans` · `cost_daily` · `generate_jobs` · 通识课 3 表） |
| Agent | 15 项注册 · 9 阶段默认流水线 |
| 内置科学问题 | 125 题（Science 2005 前沿难题） |
| 前端视图 / 组件 / API 模块 | 24 / 17 / 19 |
| 测试 | 12 用例 pytest 全通过 · Redis 双进程分布式自测 10/10（§21.5）· 生产镜像本机 Docker 端到端起站验证（§22.1） |

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

### 方式 B：Docker 一键（单容器 · SPA+API）

```bash
cd AI_Scientist_v2
docker compose up --build
# → http://localhost:8000 （前端 SPA + API 同端口，SQLite 落命名卷）
```

> 生产多副本 / PostgreSQL / Redis / Nginx 反代的一键上云见 §22（`deploy/`）。

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
        ↓  每一阶段写内存作业表，并低频镜像到数据库 generate_jobs 表（services/generate_progress.py）
GET /api/v1/coursewares/quick-generate/{job_id}   ← 前端每 1.2s 轮询，驱动真实进度条
        ↓
④  status=done 时 result 里拿到 courseware_id / slide_count / cost /
    pptx_url / ebook_url / handout_url / reader_url / sources_used
        ↓
⬇️ 下载 .pptx  ·  📕 电子书  ·  📄 学生讲义 / 🗒️ 教师讲义  ·  📖 逐页阅读  ·  ✏️ 逐页微调  ·  🎓 发布课程
```

**进度可视化**：阶段枚举 `material → outline → chapter → summary → render → persist`，
前端（`views/course/CoursewareStudio.vue` 与课程详情页的生成弹窗）展示百分比进度条、
已完成章节数 `x/y`、已产出页数与逐条阶段日志；作业进度同时存内存与数据库
`generate_jobs` 表，因此服务重启或超过内存 30 分钟 TTL 后仍能轮询到最终结果（内存未命中自动回查数据库）；
启动时会把上次进程遗留的 `running` 作业对账为 `failed`（后台 asyncio 任务已随进程消失）。

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

## 5. 平台治理：模型 · 预警 · 预测 · 图谱 · 计划

### 5.1 模型选用与多供应商

- **供应商注册表**：Qwen（DashScope，默认）+ DeepSeek / Kimi / 智谱 GLM / 自定义 OpenAI 兼容端点；`.env` 里配了对应 `*_API_KEY` 才出现在可选列表（自定义供应商需 `CUSTOM_BASE_URL` + `CUSTOM_API_KEY` + `CUSTOM_MODELS` 三元组齐全）
- **优先级三档**：`mode_policy.apply_mode()` 统一裁决 —— 显式模型 > 模式档位（快速/专家）> 默认；回退管线不变
- **顶栏全局切换器**：`◀ 模型 ▶` 一处选定全站生效，localStorage `ai_pref_model` 持久化，「自动」档按模式定档
- **各生成面板下拉旁 ◀▶** 循环切换（课件工坊 / 课程详情 / Agent Playground）；请求层兜底规则：面板显式选择 > 全局首选 > 不传（后端按 mode 定档）
- 模型列表来自 `GET /coursewares/generate-models`（含 provider_label 分组）

### 5.2 统一预警中心

`GET /api/v1/alerts` 聚合四类（全部数据驱动，不新增人工规则配置）：

| type | 触发条件 | 跳转 |
| --- | --- | --- |
| `cost_over_threshold` | 线性外推本月费用超 `COST_ALERT_THRESHOLD_YUAN`（含预计超阈日） | 成本分析 |
| `model_rate_limited` | `qwen_client.model_status()` 报告限流 | 课件工坊 |
| `provider_key_missing` | 已注册模型但 `CUSTOM_*` 三元组不齐 | 设置 / `.env` |
| `job_failed` | 近 24h 失败的生成作业与 PipelineRun | 对应项目 |

前端：顶栏铃铛 60s 轮询，按 severity 分组，error 级首次出现 toast 一次。

### 5.3 三类线性预测（`services/prediction.py`）

统一最小二乘外推 `linear_forecast(series)` → slope / predicted / confidence（R²），数据不足 3 天返回 `insufficient` 不瞎猜：

| 预测 | 数据源 | 展示位 |
| --- | --- | --- |
| 本月 API 成本 | `cost_daily` 日桶（内存热路径累计 + ≥ 60s 低频刷库，挂既有 5s progress_sync 循环） | `/cost` 折线 + 预测虚线段 + 概览卡 |
| 任务完成时间 ETA | 生成作业 / PipelineRun 已完成比例 × 开始时间 | 小窗进度条与自动化页「预计还需 N 分钟」 |
| 学习完课进度 | `general_progress` 近 14 天学习频次 | 通识课首页 / 课程卡「预计 X 天后学完」 |

### 5.4 通用知识图谱（一张表 · 一个组件 · 四处落位）

```
KnowledgeGraph(scope, scope_id, nodes JSON, edges JSON, status)   唯一约束 (scope, scope_id)
scope ∈ general（通识课+章节）| syllabus（课程大纲）| kb（用户文档标题+摘要）| project（结构图）
```

- **AI 抽取**：general / syllabus / kb 每次 rebuild 只调 **1 次** `call_qwen`（复用模式档位与回退管线），产出 `{nodes:[{id,label,group}], edges:[[s,t,rel]]}`，服务端收敛 ≤ 40 节点、去重、剔除悬空/自环边；结果缓存，命中不重复耗 token
- **零 LLM**：project scope 由 Project + AgentTask + Hypothesis 外键直接组装，GET 即出图
- **前端**：自研 `components/common/GraphView.vue`（约 300 行 SVG 力导向：斥力+弹簧+中心引力，缩放平移拖拽，group 分色），**不引入任何新 npm 依赖**；落位：通识课详情折叠面板 / 课程详情大纲区 / 资料库图谱视图 / 项目详情结构图

### 5.5 自由计划中心

```
Plan(scope: personal|team|pipeline|auto, items:[{text,due,agent,done}], source: manual|ai)
  └─ pipeline 计划──POST /plans/{id}/to-pipeline──▶ Pipeline.steps（可立即 run）
```

- 四 tab：个人待办 / 团队（以项目为载体，同项目成员可见）/ 流水线 / AI 自主
- `POST /plans/ai`：主题 → 5-8 条可执行分解；团队/流水线场景注入项目研究问题与已有进展；`agent` 字段按 `AGENT_REGISTRY` 白名单收敛
- `to-pipeline`：items[].agent 必须在注册表内且 ≥ 2 步；已有 pipeline_id 时幂等更新步骤
- 到期提醒复用 `/alerts` 机制；流水线 tab 保存后可一键启动执行

---

## 6. 系统架构

```
┌─ 浏览器（Vue 3 SPA，vite build 产物由后端 static 直出）
│
├─ FastAPI · /api/v1
│   ├─ 认证 JWT（access / refresh，支持 ?token= 的 flexible 模式）
│   ├─ SSE 实时通道（流水线进度、Token 流、实验状态）
│   ├─ REST：projects · questions · courses · coursewares · automation · plans
│   │        skills · knowledge(+external) · documents · evidence · export
│   │        chat · stream · multimodal · experiment-lab · observability · alerts · graphs
│   │        general（通识课）· admin · team · batch
│   └─ Orchestrator（多 Agent 编排 + 反思循环 + retry-from 断点续跑）
│
├─ 服务层：qwen_client · mode_policy · prediction · literature_search · experiment_engine
│          ppt_service · course_ai_service · generate_progress · external_collector · skill_engine · …
├─ 数据层：SQLAlchemy 2.x async + SQLite（aiosqlite），Alembic 迁移
└─ 文件层：uploads/（用户原件） · generated/（系统产物，固定根） · logs/（滚动日志）
```

## 7. 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite 6 · Pinia · vue-router · TailwindCSS · Element Plus · KaTeX · vite-plugin-pwa |
| 后端 | Python 3.11+（实测 3.12）· FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · Alembic · Uvicorn |
| 数据 / 分布式 | SQLite（aiosqlite，默认）· PostgreSQL（asyncpg，可平滑切换并启用连接池）· Redis（可选：分布式限流 / 登录锁定 / 并发闸）· APScheduler（定时流水线） |
| 模型 | Qwen-Max / Plus / VL（默认基座）· DashScope SDK；可选 DeepSeek / Kimi / GLM / 自定义 OpenAI 兼容端点 |
| 课件 / 文档 | python-pptx（解析与反向导出）· python-docx · PyMuPDF · openpyxl · Pillow（逐页渲染压缩）· xhtml2pdf / weasyprint（PDF 导出） |
| 实验 | matplotlib / numpy / scipy / pandas，子进程沙箱执行 |
| 部署 | 两条路径：单容器一键（`docker-compose.yml` + `backend/Dockerfile`，SPA+API 同端口）；生产上云（`deploy/`：多阶段镜像 + nginx → app×N → PostgreSQL + Redis） |

## 8. 多智能体与九阶段流水线

默认工作流（可在自动化模块自定义顺序、增删步骤，支持从任意阶段续跑）：

```
knowledge_gap → literature → hypothesis → design → experiment_plan
              → analysis → writing → review → reflection
```

另有文档生成工作流（`document_planner → section_writer → quality_gate → revision → multimodal_enricher`）与
`AGENT_REGISTRY` 中的 15 项注册（含 `experiment` 别名）。任一 Agent 都可在 Agent 中心单独调试并观察其 Trace。

## 9. 实验执行引擎

`services/experiment_engine.py` 在 backend 生成的隔离目录中执行代码，产出图表、动画与指标，全部写入
`generated/experiments/`；前端「实验模拟场」通过 `/experiment-lab/chart/{run}/{file}` 与 `/video/{run}` 懒加载。
沙箱限制执行时长、内存与网络，失败信息回灌反思循环。

## 10. 目录结构

```
AI_Scientist_v2/
├── backend/
│   ├── app/
│   │   ├── agents/            # 22 个 Agent 文件 + orchestrator + tools（15 项注册）
│   │   ├── api/v1/            # 28 个端点模块（courses.py 含课程 + 课件双 router；
│   │   │                      #   新增 alerts / graphs / plans / general_courses）
│   │   ├── services/          # qwen_client · mode_policy · prediction · ppt_service · course_ai_service ·
│   │   │                      #   generate_progress · job_queue（Redis 生成队列）· redis_client（可选分布式）· …
│   │   ├── schemas/           # Pydantic 契约
│   │   ├── database/          # models（33 表）· session（SQLite / PostgreSQL asyncpg 连接池）· init_db · Alembic
│   │   ├── security/          # JWT · 加密 · 分布式限流 rate_limiter · 账号锁定 login_guard
│   │   ├── scheduler/         # APScheduler 定时流水线（cron 触发九阶段）
│   │   ├── core/              # 事件总线 · 配置 · 依赖注入
│   │   ├── utils/paths.py     # ★ 生成文件唯一路径入口
│   │   ├── observability/     # tracer · 成本统计（含 cost_daily 内存日桶）
│   │   └── main.py            # 路由注册 · SPA 托管 · 启动建树
│   ├── scripts/              # redis_cluster_check.py 分布式自验证脚本等
│   ├── generated/             # ★ 所有系统生成文件（gitignore，保留骨架）
│   ├── uploads/               # 用户上传原件
│   ├── static/                # 前端构建产物（免 Node 运行）
│   ├── logs/ · tests/ · migrations/
│   └── run.py · requirements.txt · requirements-dev.txt · Dockerfile · .env
├── frontend/
│   └── src/{api,components,composables,router,stores,types,views,i18n,…}
│       ├── components/common/  # GraphView（自研 SVG 力导向）· ModelSwitcher（顶栏模型切换）
│       └── views/plans/        # PlansView（四 tab 计划中心）
├── deploy/                    # ★ 生产上云编排（§22）：多阶段镜像 + nginx → app×N → PostgreSQL + Redis
├── docs/                      # 技术方案.md / .pdf · 快速开始.md · 提交清单.md
├── docker-compose.yml         # 单容器一体化部署（§14）
└── README.md
```

## 11. 配置与环境变量

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

# ── 可选供应商（密钥留空则该供应商不出现在模型切换列表）──
DEEPSEEK_API_KEY=
DEEPSEEK_MODELS=deepseek-chat,deepseek-reasoner
MOONSHOT_API_KEY=
MOONSHOT_MODELS=moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k
ZHIPU_API_KEY=
ZHIPU_MODELS=glm-4-flash,glm-4-air,glm-4-plus
# 自定义 OpenAI 兼容端点：三元组齐全才生效
CUSTOM_API_KEY=
CUSTOM_BASE_URL=
CUSTOM_MODELS=

# ── 预警阈值 ──
COST_ALERT_THRESHOLD_YUAN=100.0

# ── 可扩展性（全部可选，留空即单机降级，见 §21）──
REDIS_URL=                       # 留空 → 队列/限流/缓存回落进程内，单副本照常运行
GENERATION_MAX_CONCURRENCY=4     # 并发生成上限（配合 Redis 队列做背压）
GENERATION_QUEUE_MAX=100         # 待处理生成任务队列长度上限
DB_POOL_SIZE=10                  # PostgreSQL asyncpg 连接池（SQLite 下忽略）
DB_MAX_OVERFLOW=20               # 连接池溢出上限
```

> 单机体验无需设置以上五项；配置 `REDIS_URL` 后生成队列、分布式限流、跨副本缓存自动切换为 Redis 后端，多副本共享同一套状态（§21）。

路径类配置在 `app/config.py` 里已改为**绝对默认值**，通常无需覆盖：

| 配置 | 默认值 | 含义 |
| --- | --- | --- |
| `UPLOAD_DIR` | `<backend>/uploads` | 用户上传原件 |
| `GENERATED_DIR` | `<backend>/generated` | 系统生成文件唯一根 |
| `LOG_DIR` | `<backend>/logs` | 滚动日志 |

## 12. API 参考

统一前缀 `/api/v1`，除 `/api/health` 外均需 `Authorization: Bearer <token>`（下载/图片类端点可用 `?token=`）。

| 模块 | 前缀 | 端点数 | 代表端点 |
| --- | --- | --- | --- |
| 认证 | `/auth` | 5 | `POST /auth/login` · `/auth/refresh` |
| 项目 | `/projects` | 13 | `POST /projects` · `/projects/{id}/pipeline` |
| 科学问题 | `/questions` | 19 | `POST /questions/{qid}/research` · `GET /questions/{qid}/report` |
| 课程中心 | `/courses` | 15 | `POST /courses` · `/{id}/courseware` · `/{id}/sync-from-pipeline` · `/ai/outline` |
| 课件 | `/coursewares` | 16 | `POST /quick-generate` · `GET /quick-generate/{job_id}` · `GET /generate-models` · `GET /ai-mine` · `/{id}/staleness-scan` · `/{id}/ai-refresh` · `/{id}/ebook` · `/{id}/handout` · `/{id}/export/pptx` · `/{id}/versions` |
| **计划中心** | `/plans` | 7 | CRUD · `POST /plans/ai`（主题拆解）· `POST /plans/{id}/to-pipeline`（转流水线） |
| **知识图谱** | `/graphs` | 2 | `GET /graphs/{scope}/{scope_id}`（project 零 LLM 即出）· `POST .../rebuild`（一次 LLM 抽取，缓存命中免耗） |
| **预警中心** | `/alerts` | 1 | `GET /alerts`：成本超阈 / 模型限流 / 密钥缺失 / 任务失败四类聚合 |
| **AI 通识课** | `/general` | 11 | 课程/微课列表 · 进度上报 · AI 助教 · 起草 · `GET /learning-forecast`（完课预测） |
| 自动化 | `/automation` | 12 | `POST /{pid}/run` · `/{pid}/run-from` · 定时与反馈迭代 |
| 实验模拟场 | `/experiment-lab` | 12 | `POST /run` · `GET /status/{run}` · `/chart/…` · `/video/{run}` |
| 资料库 | `/knowledge` · `/knowledge/external` | 9 · 5 | 上传解析 · 检索 · 外部学术源 |
| 技能市场 | `/skills` | 4 | 内置 / prompt 自主 / git·webhook 外接 |
| 对话 · 推送 | `/chat` · `/stream` | 5 · 1 | 多轮对话 · SSE |
| 多模态 · 文档 · 证据 | `/multimodal` · `/documents` · `/evidence` | 7 · 5 · 5 | 图文理解 · 分片上传 · 证据链 |
| 观测 · 管理 | `/observability` · `/admin` | 3 · 3 | Trace 回放 · 成本汇总+历史+预测 · 用户管理 |
| 导出 · 批量 · 团队 | `/export` · `/batch` · `/projects(team)` | 1 · 2 · 2 | 赛题文档一键导出 |

完整交互文档：启动后访问 `/docs`（Swagger）或 `/redoc`。

## 13. 数据库 Schema（33 表）

| 分组 | 表（`__tablename__`） |
| --- | --- |
| 用户与协作 | `users` · `project_shares` · `notifications` · `audit_logs` |
| 科研项目与执行 | `projects` · `agent_tasks` · `tool_calls` · `chat_messages` · `documents` · `upload_chunks` |
| 观测与成本 | `trace_records` · `cost_records` · `cost_daily`（日成本桶）· `generate_jobs`（异步作业落库） |
| 假设与迭代 | `hypotheses` · `iteration_records` |
| 流水线与计划 | `pipelines` · `pipeline_runs` · `pipeline_run_logs` · `plans` |
| 知识图谱 | `knowledge_graphs`（scope/scope_id 唯一，nodes/edges JSON） |
| 科学问题 | `science_questions` · `question_tasks` |
| 实验 | `experiment_runs` · `experiment_templates` |
| 技能 | `custom_skills` |
| 课程与课件 | `courses` · `coursewares` · `slides` · `enrollments` |
| AI 通识课 | `general_courses` · `general_lessons` · `general_progress` |

> 课件相关四表是课程中心的地基：`Courseware` 只存元数据与体积统计，页面正文存在 `Slide`（文本层 + 逐页图路径），
> AI 更新不覆盖原稿而是新开一条 `Courseware` 并用 `parent_id` 串成版本链；`Enrollment` 记录选课、进度与断点。

迁移：`alembic revision --autogenerate -m "..."` + `alembic upgrade head`；全新环境可直接 `python -m app.database.init_db`。

## 14. Docker 部署（单容器 · 开发 / 体验）

> 本节是**单容器一体化**部署（SPA + API 同端口，SQLite 落命名卷），适合本地验证与小规模使用；需要多副本横向扩展、PostgreSQL + Redis 的**生产上云**编排见 §22（`deploy/`）。

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

## 15. 质量闸门（CI 与本地）

仓库已内置 **GitHub Actions CI**（`AI_Scientist_v2/.github/workflows/ci.yml`，push / PR 到 `main`·`develop` 触发），两个 job：

| Job | 内容 |
| --- | --- |
| `backend` | Python 3.12 · 装 WeasyPrint 系统依赖 · `pip install -r requirements.txt + requirements-dev.txt` · `pytest -q --maxfail=1`（SQLite 临时库 + 占位 Key，不跑真实流水线） |
| `frontend` | Node 20 · `npm ci` · `npm run build`（含 vue-tsc 类型检查）· 上传 dist 产物 |

> CI 不持真实 `QWEN_API_KEY`（留给本地 / 评审演示）；流水线实跑需自备密钥。

提交前也可在本地手动跑同等三步（均已验证为绿）：

```bash
cd AI_Scientist_v2/frontend && npm run build        # vue-tsc 类型检查 + vite build
cd ../backend  && python -m pytest tests -q         # 12 用例
robocopy ../frontend/dist ./static /MIR         # 同步免 Node 产物
```

## 16. 测试

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

## 17. 可观测性与安全

- **Trace**：每个 Agent 步骤生成 span，落库后可在 `/traces` 逐层回放，含输入输出与耗时
- **成本**：按模型统计 prompt/completion token 与金额，`/cost` 汇总 + 近 30 天历史 + 线性预测，流水线级别可归因到项目；`cost_daily` 走「内存热路径累计 + ≥ 60s 低频刷库」的混合持久化，不拖慢请求
- **预警**：`/alerts` 四类聚合（见 §5.2），成本超阈预测到具体日期，失败作业覆盖近 24h 生成作业与 PipelineRun
- **认证**：JWT access + refresh（`python-jose`），密码 passlib/bcrypt 散列（**非明文**）；student / teacher / researcher / admin 角色分级，课程与课件按 owner 校验
- **文件安全**：文件名 sanitize + 扩展名白名单 + 大小上限；生成文件路径统一经 `paths` 校验，拒绝 `..` 与绝对路径注入
- **执行安全**：实验代码在受限子进程运行，超时/超限即终止；外部 webhook 技能带签名与超时

### 17.1 认证与防刷加固（已实测）

针对「注册数据加密」与「被多次/并发请求拖到卡死」两点：

- **bcrypt 移出事件循环**：登录/注册为 `async` 端点，早期直接同步调用慢哈希会**独占事件循环**，洪峰时冻结全站。现改为 `await run_in_threadpool(verify_password/hash_password, ...)`（`services/auth_service.py`），慢哈希在线程池执行，不再阻塞。
- **按 IP 限流**：`auth_rate_limiter`（每 IP 每分钟 10 次）经 `check_auth_rate_limit` 依赖挂在 `/auth/login`、`/auth/register`，抵御高频卡死。（注：`deps.py` 的 `check_rate_limit` 历史上定义了却从未挂载，等于无保护，现已修正。）
- **按账号失败锁定**：`security/login_guard.py` 的 `login_guard` —— 15 分钟内同一用户名连续失败 5 次即临时锁定该账号 15 分钟，返回 `429 ACCOUNT_LOCKED` + `Retry-After`；成功登录或到期自动解除。与按 IP 限流互补，专治撞库/暴力破解。
- **SECRET_KEY 守卫**：`config.py` 启动时检测 `SECRET_KEY`，若仍为样板占位值或长度 < 32，自动替换为 `secrets.token_hex(32)` 随机密钥并告警，避免用公开密钥签发可伪造的 JWT。**正式部署应在 `.env` 固定一个强随机密钥**（`.env` 已 gitignore，不入库）。
- **注册强度**：密码下限 6→8 位、邮箱加格式正则校验（登录仍允许旧的 6 位短密码，避免老用户登不进）；已移除登录页明文展示的默认管理员口令。

### 17.2 HTTPS 与生产部署

本应用签发 JWT 且处理上传文件，**生产必须走 HTTPS**，否则令牌与凭据在链路上明文可嗅探：

- **反向代理终结 TLS**：应用本身只监听 `http://:8000`，用 Nginx / Caddy 在前面挂证书并 `proxy_pass`。Caddy 一行即可自动签发 Let's Encrypt：`reverse_proxy 127.0.0.1:8000`。
- **代理头**：`app.main` 需信任 `X-Forwarded-Proto`/`X-Forwarded-For`（`ProxyHeadersMiddleware` 或 uvicorn `--proxy-headers --forwarded-allow-ips=*`），否则 `request.client.host` 会全是代理 IP，导致按 IP 限流失效。
- **Cookie/令牌**：跨端或公网部署时确保前端用 `https://` 访问 API；`Set-Cookie`（若有）加 `Secure; HttpOnly; SameSite=Lax`。
- **HSTS + 跳转**：代理层配置 80→443 强制跳转与 `Strict-Transport-Security`。
- **密钥与凭据**：生产 `.env` 固定强 `SECRET_KEY`；各供应商 `*_API_KEY` 只放服务端环境，绝不入库或下发前端。

## 18. 已知问题与排坑

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| Windows 下 `python -c "..."` 报 `unterminated string literal` | cmd 撕裂引号 | 写成临时脚本执行 |
| 静态路由 404 / 422 | FastAPI 按声明顺序匹配，`/{id}` 在前会吞掉静态段 | 静态路径（`ai-mine`、`quick-generate`）先声明 |
| `MissingGreenlet` | SQLAlchemy async 下懒加载关系 | 显式 `selectinload` 或 `.unique().all()` |
| 生成的文件到处乱跑 | 曾使用 `os.getcwd()` / 相对路径 | 已全部改为 `app/utils/paths.py` 绝对根 |
| 老课件图片打不开 | 历史数据存的是 `uploads/courses/…` 或绝对路径 | `paths.resolve()` 自动回退旧根，无需迁移 |
| PPT 解析失败 | `.ppt` 旧二进制格式 | 先在 Office 里另存为 `.pptx` |
| 刷新页面后生成进度条消失 | 内存作业表有 TTL 且进程重启即清空 | 作业状态已低频镜像到 `generate_jobs` 表，轮询内存未命中自动回查数据库；启动时残留 running 对账为 failed；结果本身也已落库，可去课程页拿 |
| 后台生成报错但页面不提示 | 失败信息写在作业表的 `error` 字段 | 轮询到 `status=failed` 会显示红色提示；也可 `GET /coursewares/quick-generate/{job_id}` 直查 |
| 聚合报告写进大模型时报 `SyntaxError: '(' was never closed` | f-string 里嵌了同种引号（PEP 701 仅 Py3.12+ 合法），如 `f"{'、'.join(x)}"` | 先在外部算好变量再插值 |
| 讲义/电子书里表格只剩一行表头 | `Slide.tables` 是 `[表格[行[单元格]]]` 三层，易误当成单行 | 按 `tbl[0]` 表头、`tbl[1:]` 正文渲染，单元格内的竖线自动转全角｜ |
| `from app.agents import mode_policy` 报 ImportError | 模式策略在服务层不在 Agent 层 | 正确路径 `from app.services import mode_policy` |
| 顶栏切换了模型但生成请求没生效 | 请求层兜底优先级被面板显式值覆盖 | 规则固定：面板显式选择 > `preferredModel` > 不传；面板选「自动」即交还全局首选 |
| 自定义供应商模型不出现在切换列表 | `CUSTOM_*` 三元组不齐（静默过滤） | `.env` 同时配 `CUSTOM_API_KEY` / `CUSTOM_BASE_URL` / `CUSTOM_MODELS`；预警铃铛会提示缺失项 |
| 图谱 rebuild 返回空节点 | 模型输出带 ```json 围栏或前后废话 | `_extract_json` 已容忍围栏与前置文本；仍失败时直接重试一次即可 |

## 19. FAQ

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

**Q：怎么切换生成用的模型？想用 DeepSeek/Kimi/GLM 怎么办？**
A：顶栏 `◀ 模型 ▶` 切换器一处选定全站生效；各生成面板下拉旁也有 ◀▶ 循环箭头。第三方供应商在 `.env` 配对应 `*_API_KEY` 即自动出现在列表，未配密钥的供应商不展示（铃铛预警会提示缺失项）。都不选时后端按「快速/专家」模式自动定档。

**Q：知识图谱耗 token 吗？**
A：general / syllabus / kb 三类每次 rebuild 只调 1 次 LLM，结果落 `knowledge_graphs` 表，缓存命中不重复耗；project 结构图由外键直接组装，完全零 LLM，GET 即出图。

**Q：AI 生成的计划能直接执行吗？**
A：流水线 scope 的计划可以：每条 item 指定 `agent`（限 `AGENT_REGISTRY` 白名单），`POST /plans/{id}/to-pipeline` 落成 `Pipeline.steps`（≥ 2 步）后可直接 run；重复点击幂等更新步骤。

## 20. 多端形态：桌面 · 手机 · 小程序

后端是**单 REST API + 单库**，数据天然多端共享。同一份前端可产出三种形态：

### 20.1 PWA（桌面 + 手机，零改动即可用）

已接入 `vite-plugin-pwa`（`frontend/vite.config.ts`），构建产物含 `manifest.webmanifest`、`sw.js` 与图标（`frontend/public/`）。

- **桌面安装**：Chrome / Edge 打开 `http://localhost:8000` → 地址栏右侧点“安装应用”→ 生成桌面图标，独立窗口运行。
- **手机安装**：手机与电脑连**同一 WiFi**，浏览器开 `http://<局域网IP>:8000`（如 `http://10.5.30.207:8000`）→ “添加到主屏幕”。
- **同步**：SW 只预缓存前端静态产物，**不缓存 `/api`**，因此各端读的都是同一份实时后端数据。
- `run.py` 已绑 `host="0.0.0.0"`，局域网可达；SPA 与 API 同源，无需改 CORS。

> 注：PWA 安装与 Service Worker 需要安全上下文（`localhost` 或 HTTPS）；纯局域网 IP 的 `http://` 在手机浏览器里可能不弹出“安装”，但页面与同步照常可用。真正要“像 App 一样”就走下面的原生包。

### 20.2 原生 App（Capacitor）

已装 `@capacitor/{core,cli,android}` 并生成 `capacitor.config.ts`；`android/` 工程不入库，一条命令重生成。

```bash
cd AI_Scientist_v2/frontend
copy .env.example .env          # 将 VITE_API_BASE=http://<后端IP>:8000 填上（webview 需绝对地址）
npm run build                    # 产出 dist
npx cap add android              # 首次：生成 android/ 工程
npx cap sync                     # 把 dist 同步进原生工程
npx cap open android             # 用 Android Studio 打开
# 在 Android Studio 里 Build > Build APK(s)，或命令：cd android && ./gradlew assembleDebug
```

打包 APK 需要本机装 **Android Studio + JDK**（首次会下载 SDK）。iOS 同理 `npx cap add ios`（需 macOS + Xcode）。

### 20.3 微信小程序（需重写，分期交付）

当前前端基于 **Element Plus（网页组件）**，小程序运行环境不支持，**无法直接复用**，需用 **uni-app / Taro** 重写 UI 层（API 层可直接复用，因为后端就是同一套 REST）。这是独立且成本最高的一条赛道，建议排在 PWA + 原生 App 跑通之后。

## 21. 可扩展性（Redis 分布式状态 · 生成队列 · PostgreSQL）

针对「很多人同时用会不会崩」，已把三处「单机天花板」按业界常规姿势改造。**原则：不配 Redis / 不换 PostgreSQL 也照常跑（自动降级内存 + SQLite），配置后无缝升级为分布式。**

### 21.1 分布式限流与登录锁定（`app/security/`）

- `rate_limiter.py`：滑动窗口优先走 **Redis 有序集**（`ZADD/ZREMRANGEBYSCORE/ZCARD` 事务管道），多实例共享同一份计数；`REDIS_URL` 留空或 Redis 抖动时**自动回退进程内存**。
- `login_guard.py`：登录失败计数与账号锁定用 **Redis + TTL**（到期自动解锁、跨实例一致），同样带回退。
- 三者的 `is_allowed / record_fail / is_locked` 均为 **async**；`api/deps.py` 反代后取真实客户端 IP（`X-Forwarded-For`），避免所有用户共用一个限流桶。
- `app/services/redis_client.py`：懒单例 + 可用性探测，`redis` 包未装 / 连不上都返回「不可用」，主流程绝不因此报错。

### 21.2 课件生成削峰队列（`app/services/job_queue.py`）

生成一次课件要几十上百秒、且吃 LLM 配额，旧实现「每请求 `create_task` 直接跑」会被同时点击打爆。现改为：

- **固定 worker 池 + 有界队列**：请求先入队拿 `job_id`，worker 按 `GENERATION_MAX_CONCURRENCY`（默认 4）逐个取出执行。
- **背压/削峰**：等待队列 `GENERATION_QUEUE_MAX`（默认 100）排满时，`/coursewares/quick-generate` **直接返回 429 + Retry-After**，不无限堆积。
- **集群级并发闸**：接 Redis 后用「租约 ZSET」限制跨实例总并发，进程崩溃时租约到期自动回收；无 Redis 仅用单实例 worker 数。
- worker 池在 `main.py` lifespan 启停，关服优雅取消。

### 21.3 数据层 PostgreSQL 兼容（`app/database/session.py`）

同一套代码兼容 SQLite 与 PostgreSQL/MySQL：`DATABASE_URL` 换成 `postgresql+asyncpg://...` 即自动启用**连接池**（`DB_POOL_SIZE/DB_MAX_OVERFLOW/DB_POOL_RECYCLE`）；SQLite 分支维持 WAL。切换示例见 `.env`。

### 21.4 启用方式

```bash
# 分布式（生产）
REDIS_URL=redis://127.0.0.1:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/zhixing
GENERATION_MAX_CONCURRENCY=8
# 均留空/默认即回到单机内存 + SQLite，开发机无需装任何中间件
```

> 现实边界：以上解决的是「单机→可横向扩展」的第一步（状态外置 + 削峰 + 连接池）。真正的百万/亿级还需对象存储替代本地 `generated/`、消息队列独立进程、读写分离与 CDN，属产品公司级工程。

### 21.5 双进程真实验证（已实测通过）

`backend/scripts/redis_cluster_check.py`：把「进程 A 执行完即销毁（内存归零）→ 全新进程 B 仍能看到 A 的封锁状态」作为判准，状态只可能来自 Redis，而非同进程内的“假分布式”。实测 10/10 项全过（本机 Docker 跑 Redis 7）：

- IP 限流：A 把测试 IP 的 10 次/分钟配额用完 → B 同 IP 被拒、其他 IP 不受牵连
- 账号锁定：A 累计 5 次失败触发锁定 → B 新进程查到该账号锁定中（TTL 897s）
- 集群并发闸：A 占 3 个生成作业租约 → B 只能占到第 4 个，第 5 个被挡；过期租约自动回收（崩溃自愈）

一键复跑：`python scripts/redis_cluster_check.py`（需 `.env` 配了可用的 `REDIS_URL`）。

## 22. 一键上云（Docker Compose 生产编排）

`deploy/` 目录提供与市面网站部署同构的全套产物：多阶段 Dockerfile（容器内构建前端 + 后端运行时合一，单镜像即全站）、docker-compose（nginx → app×N → PostgreSQL + Redis）、生产 nginx 配置（SSE 关缓冲 / XFF 真实 IP / 30m 上传 / 长任务超时）、`.env.example` 配置样板。

上线五步（任选一家云厂商 2C4G 主机，Ubuntu 22+，装好 Docker）：

```bash
git clone https://github.com/fems-rgb/111.git && cd 111/AI_Scientist_v2/deploy
cp .env.example .env        # 填 SECRET_KEY / POSTGRES_PASSWORD / QWEN_API_KEY
docker compose up -d --build # 首次构建含前端编译，约 5–10 分钟
docker compose up -d --scale app=3   # 人多时一条命令加副本（无状态，状态全在 Redis/PG）
```

对接域名/HTTPS：证书放 `deploy/certs/`（fullchain.pem + privkey.pem），解开 `nginx.conf` 末尾 443 块注释；域名解析到服务器后浏览器即走 https。验证入口：`http://服务器IP/`（全站）、`/api/health`（存活探测，compose healthcheck 兼用）。

数据备份：`pgdata`（业务库）、`generated`/`uploads`（生成与上传文件）、`redisdata` 三个命名 volume，云盘快照或 `docker run --volumes-from` 导出均可。

### 22.1 构建产物真实验证（已在本机 Docker 实测）

用与生产同款的 `deploy/Dockerfile`、`deploy/nginx.conf`、`deploy/docker-compose.smoke.yml` 在本机 Docker 端到端拉起并验证：

- 多阶段镜像真实构建成功：容器内 `npm ci + vue-tsc + vite build`（PWA）编译前端 → `pip install` 后端依赖，产出 `deploy-app:latest`（含全部运行依赖）。
- `nginx → app → redis` 全链路起站：经 nginx 反代访问 `/api/health` 返回 **200 `{"status":"ok","version":"3.0.0","name":"智研星枢"}`**，`/` 返回 **200** 且带 SPA 挂载点（前端产物已从镜像内 `/app/frontend/dist` 直供，单容器即全站）。
- 启动日志实测确认关键子系统均已加载：`apscheduler Scheduler started`、`Redis 已连通，分布式限流/锁定/并发闸启用`、`课件生成队列已启动：worker=4`、`数据库表结构已创建 / 自动迁移完成`、`Application startup complete`。

> 构建中发现并修复的真实缺陷：`requirements.txt` 原先漏声明 **apscheduler（进程启动即 import）、python-docx、PyMuPDF、openpyxl、xhtml2pdf、lxml** 等依赖——开发机因 venv 恰好装过而“看起来正常”，干净镜像内会 `ModuleNotFoundError` 直接起不来。已全部补入并重新构建验证。

> 本机网络边界：`postgres:16-alpine` 官方镜像在本机因 Docker Hub 分层 blob 被持续限速而无法拉全（纯本机网络问题，与编排产物无关；PG 连接池逻辑已在 §21 的单测/双进程验证中实证）。任意云主机 `docker compose up -d --build` 会正常拉取并拉起 PG；受限网络下可先用 `docker-compose.smoke.yml`（SQLite 兜底 DB）验证 `nginx→app→redis` 主链路。

## 23. 许可证与致谢

本项目为挑战杯「揭榜挂帅」专项赛参赛作品，基座模型为阿里巴巴通义千问 Qwen，通过阿里云百炼（DashScope）调用。
感谢发榜单位浙江阿里巴巴云计算有限公司提供赛题与算力支持。
