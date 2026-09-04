---
title: "智研星枢 · AI Scientist v3.0"
subtitle: "基于国产开源大模型（Qwen）的多智能体科研假设自动生成平台"
competition: "挑战杯「揭榜挂帅」专项赛 · 题目编号 XH-202619"
organization: "发榜单位：浙江阿里巴巴云计算有限公司"
model: "基座模型：通义千问 Qwen（qwen-max / qwen-plus / qwen-vl-max，全部国产开源）"
platform: "调用平台：阿里云百炼（DashScope）"
version: "v3.0.0"
---

# 智研星枢 · AI Scientist v3.0

> **基于国产开源大模型（Qwen）的多智能体科研假设自动生成平台**
>
> 挑战杯「揭榜挂帅」专项赛参赛作品 · 题目编号 **XH-202619**
> 发榜单位：浙江阿里巴巴云计算有限公司
> 基座模型：通义千问 Qwen（全部国产开源） · 调用平台：阿里云百炼（DashScope）

---

## 📑 目录

1. [一、项目简介](#一项目简介)
2. [二、赛题要求与方案映射（重点）](#二赛题要求与方案映射重点)
3. [三、评分标准对照（100 分拆解）](#三评分标准对照100-分拆解)
4. [四、系统架构](#四系统架构)
5. [五、技术栈](#五技术栈)
6. [六、多智能体架构（对应技术深度 15 分）](#六多智能体架构对应技术深度-15-分)
7. [七、流水线机制（从问题到假设）](#七流水线机制从问题到假设)
8. [八、实验执行引擎与可验证性（对应科学价值 20 分）](#八实验执行引擎与可验证性对应科学价值-20-分)
9. [九、标准化输出：《科学假设与研究计划》](#九标准化输出科学假设与研究计划)
10. [十、多模态能力（对应技术深度 15 分）](#十多模态能力对应技术深度-15-分)
11. [十一、前后端通信](#十一前后端通信)
12. [十二、认证与权限](#十二认证与权限)
13. [十三、配置与环境变量](#十三配置与环境变量)
14. [十四、目录结构](#十四目录结构)
15. [十五、API 参考（核心端点）](#十五api-参考核心端点)
16. [十六、数据库 Schema](#十六数据库-schema)
17. [十七、真实案例演示（对应应用潜力 20 分）](#十七真实案例演示对应应用潜力-20-分)
18. [十八、可复现性（对应应用潜力 10 分）](#十八可复现性对应应用潜力-10-分)
19. [十九、部署](#十九部署)
20. [二十、容器化（Docker）](#二十容器化docker)
21. [二十一、CI/CD](#二十一cicd)
22. [二十二、测试策略](#二十二测试策略)
23. [二十三、可观测性与成本](#二十三可观测性与成本)
24. [二十四、安全考量](#二十四安全考量)
25. [二十五、开发规范](#二十五开发规范)
26. [二十六、已知问题与排坑](#二十六已知问题与排坑)
27. [二十七、路线图](#二十七路线图)
28. [二十八、提交清单（对照赛题第八点）](#二十八提交清单对照赛题第八点)
29. [二十九、FAQ](#二十九faq)
30. [三十、术语表](#三十术语表)
31. [三十一、关键文件索引](#三十一关键文件索引)
32. [三十二、许可证与致谢](#三十二许可证与致谢)
33. [附录 A：评审得分点速查](#附录-a评审得分点速查)
34. [附录 B：数据库重置与诊断 SQL](#附录-b数据库重置与诊断-sql)
35. [附录 C：前端 Vue 组件与后端端点对照](#附录-c前端-vue-组件与后端端点对照)
36. [附录 D：竞赛答辩要点（建议）](#附录-d竞赛答辩要点建议)

---

## 一、项目简介

**智研星枢（AI Scientist）** 是面向「AI for Science」的科研智能化平台，也是本团队针对**挑战杯「揭榜挂帅」题目 XH-202619《基于国产开源大模型的 AI Scientist 的研发与应用》** 提交的参赛作品。

平台基于**国产开源大模型 Qwen（千问）系列**，采用**多智能体系统（Multi-Agent）架构**，实现从「科学问题输入」到「可验证科学假设输出」的全链路智能闭环：

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

平台同时内置**实验模拟场（Experiment Lab）**，可对生成的假设进行代码级验证（数据分析、统计检验、可视化、动画仿真），真正实现赛题要求的「**可验证**」。

### 1.1 发榜单位与题目信息

| 项目 | 内容 |
|---|---|
| 赛事名称 | 「揭榜挂帅」专项赛（挑战杯主体赛、揭榜挂帅、红色专项之外的独立赛道） |
| 发榜单位 | 浙江阿里巴巴云计算有限公司 |
| 题目编号 | **XH-202619** |
| 题目名称 | 基于国产开源大模型的 AI Scientist 的研发与应用 |
| 基座模型 | Qwen 系列（qwen-max / qwen-plus / qwen-vl-max，**全部国产开源**） |
| 调用平台 | 阿里云百炼（DashScope，提供调用凭证 / 截图） |
| 适用方向 | 自然科学 + 人文社科（双赛道覆盖） |
| 官网 | https://www.tiaozhanbei.net/ |

### 1.2 核心特性

- **🤖 多智能体协作**：16 个专职 Agent + 中央 Orchestrator，支持反思循环（reflection）
- **📚 文献挖掘与事实提取**：结构化信息抽取，避免断章取义
- **💡 逻辑驱动假设生成**：归纳 + 演绎推理，基于已知事实生成假设
- **🔄 多轮迭代与论证**：跨学科技术迁移、可行性论证、人在回路（human-in-the-loop）
- **🧪 代码级可验证**：实验模拟场沙箱执行，产出图表 / 视频验证实验结果
- **📄 标准化输出**：自动生成符合赛题规范的《科学假设与研究计划》
- **🖼️ 多模态支持**：Qwen-VL 处理图像 / 图表（对应评分「多模态大模型」项）
- **🔐 基于国产模型**：全链路 Qwen，满足「自主可控」要求
- **🔁 可复现**：完整代码 + requirements + 一键运行 + 数据库持久化

### 1.3 关键指标

| 指标 | 数值 |
|---|---|
| 前端代码 | ~8,300 行（Vue / TS，54 文件） |
| 后端代码 | ~14,000 行（Python，110 文件） |
| REST API 端点 | 97 个 |
| Agent 数量 | 16 个 |
| 数据库表 | 20+ |
| 内置科学问题 | 125 题（Science 2005 年版） |
| 总代码量 | Python 13,939 行 + 前端 8,268 行 |

---

## 二、赛题要求与方案映射（重点）

> 本章节是**评审对照核心**，逐条说明本方案如何满足赛题要求。

### 2.1 核心任务映射

| 赛题核心任务 | 本方案实现 | 对应模块 |
|---|---|---|
| 基于国产开源大模型（Qwen）开发 | 基座模型全部为 Qwen（文本 qwen-max、视觉 qwen-vl-max），通过百炼平台调用 | `agents/qwen_client.py` |
| 多智能体系统（Multi-Agent）架构 | 16 个 Agent + Orchestrator 编排 | `agents/orchestrator.py` |
| 问题理解 | 科学问题解析、领域识别、约束提取 | `agents/knowledge_gap.py` |
| 知识整合 | 文献挖掘、知识库检索、事实提取 | `agents/literature.py` + `services/knowledge_index.py` |
| 关联发现 | 跨学科技术迁移、规律挖掘 | `agents/hypothesis.py` + `reflection.py` |
| 可验证假设生成 | 假设生成 + 实验设计 + 代码验证闭环 | `agents/analysis.py` + `experiment_engine.py` |
| 从「数据 / 文献输入」到「假设输出」闭环 | 题库流水线（9 阶段）端到端实现 | `api/v1/questions.py` |

### 2.2 能力项映射

| 赛题能力项 | 本方案实现 |
|---|---|
| (一) 文献挖掘与事实提取（避免断章取义） | LiteratureAgent + DocumentPlannerAgent，结构化抽取 + 引用溯源 |
| (二) 逻辑驱动的假设生成（归纳与演绎） | HypothesisAgent（归纳）+ DesignAgent（演绎），Pydantic 契约约束 |
| (三) 论证可行与多轮迭代 | ReflectionAgent 反思循环 + ReviewAgent 门禁 + 迭代记录 |
| (四) 智能体思辨与人在回路 | 评审反馈接口 + 假设修订流程 + 前端协作 UI |

### 2.3 生成结果规范映射（标准化字段）

赛题要求《科学假设与研究计划》必须包含以下字段，本平台**全部支持并自动生成**：

| 规范字段 | 本方案对应 | 说明 |
|---|---|---|
| 待研究问题（Problem Statement） | `Hypothesis.problem_statement` | 明确指出领域局限性 |
| 解决思路（Rationale） | `Hypothesis.rationale` | 逻辑推导链条 |
| 必要的技术手段（Technical Details） | `Hypothesis.technical_details` | 统计 / ML / 深度学习具体技术栈 |
| 数据集（Datasets） | `Hypothesis.datasets` | Source + Target 分离 |
| Source（历史数据依据） | `Hypothesis.source_data` | 引用真实历史数据 |
| Target（拟采集数据特征） | `Hypothesis.target_data` | 验证实验所需数据 |
| 标题（Paper Title） | `Hypothesis.paper_title` | 符合学术规范 |
| 摘要（Paper Abstract） | `Hypothesis.abstract` | 背景 / 方法 / 预期结果 |
| 方法论（Methods） | `Hypothesis.methods` | 模型架构 / 实验流程 |
| 实验设计（Experiments） | `Hypothesis.experiments` | 基线对比 + 评估指标 |
| 实验结果（Results） | 实验模拟场产物 | 公式推导 / 实际执行验证 |
| 参考论文（References） | `Hypothesis.references` | **严禁虚构，真实文献列表** |

### 2.4 技术基础要求映射

| 赛题要求 | 本方案 |
|---|---|
| 基座必须基于 Qwen | ✅ qwen-max（文本）、qwen-vl-max（视觉） |
| 通过阿里云百炼调用并提供凭证 / 截图 | ✅ DashScope 调用，`.env` 配置 QWEN_API_KEY |
| 允许微调（SFT） | ✅ 预留 SFT 接口（下游任务 / 领域数据） |
| 鼓励演示、推荐前端 | ✅ Vue 3 前端 + 演示视频 |
| 提交技术方案文档（PDF ≤ 20 页） | ✅ 本文档即核心内容来源 |
| 提交源代码 | ✅ 完整可复现代码 |
| 可选：可交互前端 + 演示视频 | ✅ 已实现 + 可录制 |

---

## 三、评分标准对照（100 分拆解）

> 评分 = 科学价值(40) + 技术深度(30) + 应用潜力(30)

### 3.1 科学价值（40 分）

| 子项 | 分值 | 本方案得分点 |
|---|---|---|
| 核心假设创新性与自洽性 | 20 | 多 Agent 交叉论证 + Reflection 迭代 + 引用真实文献 |
| 方案可落地验证性 | 20 | 实验模拟场代码级验证 + 实验设计（基线 / 指标）+ 真实案例 |

**关键证据**：平台对题库 125 个真实科学问题批量生成标准化假设（详见第九章真实案例），每个假设均含可验证的实验设计。

### 3.2 技术深度（30 分）

| 子项 | 分值 | 本方案得分点 |
|---|---|---|
| 超级智能体 / 多智能体协作设计 | 15 | 16 Agent + Orchestrator + Skills + 反思循环 |
| 基于多模态大模型对科学模态数据的处理成效 | 15 | Qwen-VL 处理实验图表 / 图像 + 多模态增强 Agent |

**关键证据**：`agents/doc_multimodal.py`（MultimodalEnricherAgent）调用 qwen-vl-max 解析科学图像，注入研究报告。

### 3.3 应用潜力（30 分）

| 子项 | 分值 | 本方案得分点 |
|---|---|---|
| 实际场景问题支撑能力 | 10 | 自然科学 + 人文社科双赛道覆盖 |
| 论文 / 专利成果转化潜力 | 10 | 标准化《科学假设与研究计划》可直接投稿 |
| 代码与结果可复现性 | 10 | 完整代码 + requirements + 一键运行 + 数据库持久化 |

### 3.4 评审加分项（额外 5 分）

- ✅ 演示视频（≤10 分钟）+ 可交互前端
- ✅ 方案 / 代码 / 演示三位一体，全流程可复现
- ✅ 使用通义千问系列（符合「采用国产模型」加分）

---

## 四、系统架构

### 4.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                  浏览器 / 演示前端（用户 & 评审）                      │
└──────────────────────┬───────────────────────────────────────────────┘
                       │  HTTP / WebSocket / SSE
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Vue 3 SPA (Vite :5173)  ──Vite proxy──▶  /api/*                  │
│  · 题库(QuestionsView) · 工作台(ProjectDetail) · 实验场(ExperimentLab)│
│  · Pinia stores · 轮询/SSE 进度 · 人在回路评审 UI                    │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI 后端 (:8000)  ── 阿里云百炼 DashScope ──▶  Qwen（国产开源） │
│                                                                      │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────────────────┐     │
│  │ auth.py │  │ questions.py │  │ experiment_lab.py          │     │
│  │ JWT登录 │  │ 题库流水线1441行│  │ /run /status/{id}          │     │
│  └────┬────┘  └──────┬───────┘  └──────────┬─────────────────┘     │
│       │               │                      │                       │
│       │         ┌─────▼──────┐         ┌─────▼──────────┐          │
│       │         │ Project    │  BG    │ ExperimentRun   │          │
│       │         │ (工作台)   │ Tasks  │ (BackgroundTask)│          │
│       │         └─────┬──────┘         └─────┬──────────┘          │
│       │               │                      │ 代码沙箱执行          │
│       │         ┌─────▼──────┐         ┌─────▼──────────┐          │
│       │         │ 多智能体    │ 调用   │ experiment_    │ 产物        │
│       │         │ Orchestrator│──────▶│ engine.py      │ (图表/视频)│
│       │         │ (16 Agent) │ Qwen  │ (动态 wrapper) │          │
│       │         └──┬──┬──┬──┘         └────────────────┘          │
│       │            │  │  │                                          │
│       │     ┌──────┘  │  └───────┐                                 │
│       │     ▼         ▼          ▼                                 │
│       │  Knowledge  Hypothesis  Reflection   ... (16 Agent)         │
│       │  Gap        Agent      Agent                                │
│       │         ┌─────▼──────┐   ┌──────────────────────┐          │
│       │         │ 通义千问   │   │ progress_sync (每5s) │          │
│       │         │ qwen-max   │   │ → QuestionTask.progr.│          │
│       │         │ qwen-vl-max│   └──────────────────────┘          │
│       │         └─────────────┘                                    │
│       └──▶ SQLAlchemy(async) ──▶ SQLite / PostgreSQL (zhixing.db)  │
│                                                                  │
│  Lifespan: start_progress_sync() / register_pipeline_jobs()        │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 请求生命周期

1. 用户操作 → Vue 组件 → Pinia action → `api/modules/*.ts` (Axios)
2. Vite dev-server 代理 `/api` → `http://localhost:8000`
3. FastAPI 路由 → 依赖注入（DB session + JWT 当前用户）
4. Service 层执行业务；重任务丢给 `BackgroundTasks`
5. Agent Orchestrator 调用 Qwen，逐步产出，写回 `AgentTask` / `QuestionTask`
6. `progress_sync`（每 5s）聚合 `AgentTask` 完成度 → `QuestionTask.progress`
7. 前端轮询 `/status` 或 SSE → 实时刷新进度条与文档

### 4.3 与赛题"科研灵感流水线"的对应关系

赛题要求实现从"输入问题/文献/数据"到"输出假设"的流水线，本平台对应如下：

| 赛题流水线环节 | 本平台阶段 | 关键 Agent / 模块 |
|---|---|---|
| 输入：科学问题 | QuestionTask 创建 | `questions.py` |
| 问题理解 | knowledge_gap | KnowledgeGapAgent |
| 知识整合 | literature | LiteratureAgent |
| 关联发现 | hypothesis | HypothesisAgent |
| 假设生成 | hypothesis + design | HypothesisAgent + DesignAgent |
| 逻辑论证 | review + reflection | ReviewAgent + ReflectionAgent |
| 多轮迭代 | reflection 循环 | ReflectionAgent |
| 人在回路 | feedback / review | `projects.py` 评审接口 |
| 输出：科学假设 | writing + export | WritingAgent + `export.py` |

---

## 五、技术栈

| 层面 | 技术选型 | 说明 |
|---|---|---|
| **基座大模型** | **Qwen（qwen-max / qwen-plus / qwen-vl-max）** | **国产开源，阿里云百炼调用** |
| 前端 | Vue 3.5 + TypeScript 5.7 + Vite 6 + Pinia 2.3 + Vue Router 4.5 | 可交互前端（演示加分项） |
| UI | Element Plus 2.14 + Tailwind CSS 3.4 | 竞赛演示 UI |
| 国际化 | vue-i18n 11 | 中英双语 |
| 文档渲染 | markdown-it / marked + KaTeX + highlight.js | 公式 / 代码高亮 |
| 后端 | Python 3.12 + FastAPI 0.115 + Uvicorn | 异步高性能 |
| ORM | SQLAlchemy 2.0（async）+ Alembic | 数据库迁移 |
| 校验 | Pydantic 2 | 数据契约 |
| 认证 | python-jose + passlib/bcrypt | JWT |
| 数据库 | SQLite（aiosqlite）/ 可迁 PostgreSQL | 开发 / 生产灵活切换 |
| 科学计算 | numpy、pandas、scipy、matplotlib、seaborn、Pillow | 实验验证 |
| 实时通信 | WebSocket + SSE + 轮询 | 进度推送 |
| 文档导出 | python-docx、docx、html-to-docx | 《科学假设与研究计划》导出 |

---

## 六、多智能体架构（对应技术深度 15 分）

> **这是本方案技术深度的核心，对应评分标准「超级智能体或多智能体协作设计 (0-15 分)」。**

### 6.1 Agent 总览（16 个）

| Agent | 文件 | 行数 | 职责 |
|---|---|---|---|
| **Orchestrator** | `agents/orchestrator.py` | 732 | **中央编排器**：状态机、调度 16 Agent、反思循环控制 |
| KnowledgeGapAgent | `agents/knowledge_gap.py` | 48 | 识别知识缺口、问题结构化 |
| LiteratureAgent | `agents/literature.py` | — | 文献检索与综述、事实提取 |
| HypothesisAgent | `agents/hypothesis.py` | — | 归纳 / 演绎生成假设 |
| HypothesisValidator | `agents/hypothesis_validator.py` | 93 | 假设可证伪性校验 |
| DesignAgent | `agents/design.py` | — | 实验方案设计 |
| ExperimentPlanAgent | `agents/experiment_plan.py` | — | 实验步骤编排 |
| AnalysisAgent | `agents/analysis.py` | — | 数据分析与统计 |
| WritingAgent | `agents/writing.py` | 215 | 研究报告撰写 |
| ReviewAgent | `agents/review.py` | 54 | 结果评审 |
| ReflectionAgent | `agents/reflection.py` | 54 | **反思与迭代决策**（人在回路） |
| DocumentPlannerAgent | `agents/doc_planner.py` | 167 | 文档结构规划 |
| SectionWriterAgent | `doc_planner.py` | — | 分章节写作 |
| QualityGateAgent | `doc_quality.py` | 193 | 质量门禁 |
| SectionReviewerAgent | `doc_reviewer.py` | 123 | 章节级审阅 |
| DocumentReviewerAgent | `doc_reviewer.py` | — | 全文审阅 |
| MultimodalEnricherAgent | `doc_multimodal.py` | 134 | **多模态增强**（Qwen-VL，对应 15 分） |

### 6.2 协作模式

采用「**编排器 + 专业化 Agent + 反思循环**」模式：

```
                     ┌───────────────┐
                     │  Orchestrator  │ (中央状态机)
                     └──┬────┬────┬──┘
               ┌────────┘    │    └───────┐
               ▼             ▼            ▼
        [知识缺口]      [假设生成]     [实验设计]
        KnowledgeGap → Hypothesis → Design → ... → Writing
               ▲                            │
               │      ┌─────────────────────┘
               │      ▼
               │   [质量门禁] ─fail─▶ [反思迭代] ─▶ 回到 Hypothesis
               │    QualityGate   ReflectionAgent
               │
               └──── 满足自洽性 / 可行性 → 输出标准化假设
```

### 6.3 反思循环（Reflection）伪代码

```python
# agents/orchestrator.py (简化示意)
async def run_pipeline(question: str) -> Hypothesis:
    state = await knowledge_gap(question)
    state = await literature(state)
    state = await hypothesis(state)

    for iteration in range(MAX_ITERATIONS):
        state = await design(state)
        state = await analysis(state)
        review = await quality_gate(state)

        if review.passed and review.self_consistent:
            break
        # 人在回路：将评审意见反馈给假设生成
        feedback = await get_human_feedback(state) or review.comments
        state = await reflection(state, feedback)

    return await writing(state)
```

### 6.4 人在回路（Human-in-the-Loop）

对应赛题「(四) 智能体思辨与人在回路」：
- 评审反馈接口 `POST /api/v1/questions/feedback`、`POST /api/v1/projects/{id}/review`
- 假设修订流程（基于 feedback 重新迭代）
- 前端协作 UI（评审 / 修订 / 采纳）

---

## 七、流水线机制（从问题到假设）

### 7.1 九阶段流水线（对应赛题"科研灵感流水线"）

题库任务的生成走 `batch_pipeline`，由 **9 个阶段**组成（对应 `builtin_default_mode`），完整实现赛题「文献挖掘 → 假设生成 → 论证迭代 → 思辨」流程：

| # | 阶段 | 名称 | 对应赛题能力项 |
|---|---|---|---|
| 1 | knowledge_gap | 知识缺口识别 | (一) 文献挖掘 |
| 2 | literature | 文献调研与事实提取 | (一) 避免断章取义 |
| 3 | hypothesis | 假设生成（归纳+演绎） | (二) 逻辑驱动 |
| 4 | design | 实验设计 | (三) 论证可行 |
| 5 | experiment_plan | 实验编排 | (三) 多轮迭代 |
| 6 | analysis | 数据分析 | 可验证性 |
| 7 | writing | 报告撰写 | 标准化输出 |
| 8 | review | 质量评审 | 自洽性 |
| 9 | reflection | 反思迭代 | (四) 人在回路 |

**内置模式**：

| 模式 | 阶段 | 用途 |
|---|---|---|
| `builtin_default_mode` | 全部 9 阶段 | 完整科研闭环（默认） |
| `builtin_full_closure` | 全部 9 阶段 | 完整闭环 |
| `builtin_quick_analysis` | knowledge_gap → literature → hypothesis | 快速分析 |
| `builtin_literature_hypothesis` | + design | 文献 + 假设 |

### 7.2 内置科学问题集

平台内置 **125 题 Science 2005 前沿科学问题**（赛题「科研问题集参考」），覆盖：

- **自然科学**：数学（黎曼 zeta、Navier-Stokes、Yang-Mills、Hodge 猜想）、物理、生物等
- **人文社科**：发展经济学、政治经济学、社会科学等

### 7.3 数据流与契约

每个阶段的输出作为下阶段的输入，均经 Pydantic 契约（`agents/contracts/`）校验；任一步失败 → 异常向上传播 → `QuestionTask.status='failed'` + `error_message`。

---

## 八、实验执行引擎与可验证性（对应科学价值 20 分）

> **赛题硬性要求「可验证」** —— 这是本平台的差异化亮点。

### 8.1 沙箱架构

```
POST /experiment-lab/run
   │  RunRequest { code, data_table, timeout, generate_video, ... }
   ▼
ExperimentRun(status='running') → DB
   │
   ▼ (BackgroundTask)
_exec(run_id, code, timeout, gen_video, data_table)
   │
   ▼
run_experiment(code, run_id, timeout, gen_video, meta={data_table})
   │  1. _build_wrapper(): 动态生成 _run.py
   │     - import numpy / pandas / matplotlib / seaborn
   │     - df = pd.DataFrame(data_table['rows'], columns=cols)
   │     - patch plt.savefig / plt.show 自动收集图表
   │     - animation.FuncAnimation 捕获视频
   │  2. subprocess 隔离运行 (超时控制)
   │  3. 解析 stdout + 图表 + 视频 → result
   ▼
ExperimentRun { status, output_text, charts, video_path, error_message }
```

### 8.2 内置实验模板

| 模板 | 类别 | 验证类型 |
|---|---|---|
| 鸢尾花数据探索 | 入门 | DataFrame / 散点图 |
| 正态分布随机数分析 | 统计 | 直方图 / 均值检验 |
| 简单线性回归 | 建模 | 最小二乘拟合 |

### 8.3 可验证性闭环

对应赛题「实验结果（Results）通过公式推导或实际执行验证」：
- 假设 → 实验设计 → **代码执行** → 图表 / 视频产物 → 验证结论
- 结果持久化到 `ExperimentRun`，关联回 `QuestionTask`

---

## 九、标准化输出：《科学假设与研究计划》

> 严格遵循赛题「四、生成结果规范」的字段要求。

平台自动生成符合规范的《科学假设与研究计划》，对应数据库 `Hypothesis` 模型：

```json
{
  "problem_statement": "在[领域]中，现有方法存在[具体局限性]...",
  "rationale": "基于[已知事实A、B]，通过[归纳/演绎]推导出...",
  "technical_details": [
    "统计方法: t检验 / ANOVA",
    "机器学习: GNN / Transformer",
    "深度学习: ..."
  ],
  "datasets": {
    "source": "引用真实公开数据集 (如 UCI, Nature Scientific Data)",
    "target": "拟采集数据特征描述"
  },
  "paper_title": "基于[方法]的[领域][现象]研究",
  "abstract": "背景... 方法... 预期结果...",
  "methods": "1. 数据清洗 2. 特征工程 3. 模型构建...",
  "experiments": {
    "baselines": ["方法A", "方法B"],
    "metrics": ["准确率", "F1", "MSE"]
  },
  "results": "通过[公式推导/代码执行]在[范围]内验证...",
  "references": [
    {"title": "真实文献1", "doi": "...", "year": 2023}
  ]
}
```

**关键**：`references` 字段**严禁虚构**，全部来自 LiteratureAgent 的真实检索结果。

---

## 十、多模态能力（对应技术深度 15 分）

对应评分「基于多模态大模型对科学模态数据的处理成效」：

- **模型**：Qwen-VL（qwen-vl-max）
- **模块**：`agents/doc_multimodal.py`（MultimodalEnricherAgent, 134 行）
- **能力**：
  - 解析实验图像 / 图表 / 显微照片
  - 提取科学图像中的定量信息
  - 注入到研究报告的图文证据链
- **接口**：`POST /api/v1/multimodal/analyze-image`、`/upload-research-file`

---

## 十一、前后端通信

**开发模式（Vite 代理）** — `frontend/vite.config.ts`：

```typescript
server: {
  port: 5173,
  proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } }
}
```

**进度更新三种方式**：

| 方式 | 场景 |
|---|---|
| 轮询 Polling | 题库 / 项目状态（`usePolling`） |
| SSE | 实时日志 / 事件 (`/api/v1/stream/events`) |
| WebSocket | 双向通信、实验运行 |

---

## 十二、认证与权限

**JWT 流程**：

```
POST /api/v1/auth/login { username, password }
  → { access_token, refresh_token }
  → 后续请求: Authorization: Bearer <token>
```

| 配置项 | 值 |
|---|---|
| 算法 | HS256 |
| 访问令牌有效期 | 1440 分钟（24h） |
| 刷新令牌有效期 | 30 天 |
| 初始管理员 | admin / admin123456 |

---

## 十三、配置与环境变量

所有变量在 `backend/.env`，由 `app/config.py`（pydantic-settings）加载。

| 变量 | 说明 |
|---|---|
| `QWEN_API_KEY` | **千问 API Key（百炼平台申请，必填）** |
| `QWEN_MODEL_NAME` | qwen-max |
| `QWEN_VISION_MODEL` | qwen-vl-max |
| `QWEN_MAX_TOKENS` | 8192 |
| `QWEN_TEMPERATURE` | 0.7 |
| `DATABASE_URL` | sqlite+aiosqlite:///.../zhixing.db |
| `SECRET_KEY` | JWT 密钥 |
| `ALLOWED_ORIGINS` | ['http://localhost:5173'] |

> **竞赛凭证**：`QWEN_API_KEY` 对应阿里云百炼平台调用凭证，需在提交材料中附调用截图。
---

## 十四、目录结构

```
AI_Scientist_v2/
├── backend/                    # FastAPI 后端
│   ├── run.py                  # 启动入口 (uvicorn :8000)
│   ├── main.py                 # FastAPI app 装配
│   ├── requirements.txt        # Python 依赖
│   ├── .env                    # 环境变量 (QWEN_API_KEY 等)
│   ├── app/
│   │   ├── api/
│   │   │   ├── documents.py    # 文档生成
│   │   │   ├── projects.py     # 项目启停 / 评审
│   │   │   └── v1/             # 版本化 API (97 个端点)
│   │   │       ├── auth.py, projects.py, agents.py, chat.py
│   │   │       ├── questions.py    (1441行, 题库流水线 ★)
│   │   │       ├── experiment_lab.py (314行, 实验场)
│   │   │       ├── knowledge.py, knowledge_external.py
│   │   │       ├── automation.py (545行), batch_run.py
│   │   │       ├── observability.py, export.py
│   │   │       └── multimodal.py (多模态)
│   │   ├── agents/             # 16 个 Agent (多智能体核心)
│   │   │   ├── orchestrator.py     (732行, 编排器 ★)
│   │   │   ├── knowledge_gap.py, literature.py
│   │   │   ├── hypothesis.py, hypothesis_validator.py
│   │   │   ├── design.py, experiment_plan.py, analysis.py
│   │   │   ├── writing.py (215行), review.py, reflection.py
│   │   │   ├── doc_planner.py, doc_quality.py (193行)
│   │   │   ├── doc_reviewer.py, doc_multimodal.py (134行)
│   │   │   ├── qwen_client.py  (★ Qwen 调用封装)
│   │   │   ├── base.py, contracts/
│   │   │   └── tools/ (search, code_exec)
│   │   ├── core/
│   │   │   ├── progress_sync.py    (每5s进度同步)
│   │   │   └── exceptions.py (92行, 9类)
│   │   ├── database/
│   │   │   ├── models.py       (524行, 20+表)
│   │   │   └── session.py, init_db.py
│   │   ├── services/           # 业务逻辑
│   │   │   ├── experiment_engine.py (472行, 代码沙箱 ★)
│   │   │   ├── batch_engine.py, doc_engine.py
│   │   │   ├── knowledge_index.py, literature_search.py
│   │   │   └── ...
│   │   ├── schemas/            # Pydantic 契约
│   │   ├── security/           # JWT, prompt_guard, sanitizer
│   │   ├── scheduler/          # 定时任务
│   │   └── observability/      # 链路追踪 + 成本统计
│   ├── logs/, scripts/, static/, tests/, uploads/
│   └── output/experiments/<id>/   # 实验产物
├── frontend/                   # Vue 3 前端 (演示加分项)
│   ├── package.json            # zhixing-frontend v3.0.0
│   ├── vite.config.ts          # :5173, 代理 /api → :8000
│   └── src/
│       ├── router/, stores/ (Pinia)
│       ├── api/modules/        # 按业务分模块
│       ├── components/         # layout, chat, hypothesis, pipeline
│       ├── composables/        # useSSE, usePolling
│       ├── views/              # workspace, agents, chat, knowledge,
│       │                       # observability, settings, skills, admin
│       ├── i18n/locales/       # 中英双语
│       └── data/ (science125.ts)  # 125 科学问题集
├── docs/                       # 竞赛文档
└── README.md
```

---

## 十五、API 参考（核心端点）

全部 97 个端点，按业务分组。Base URL：`http://localhost:8000`，前缀 `/api/v1`。

| 分组 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 认证 | POST | `/api/v1/auth/login` | 登录 |
| 认证 | POST | `/api/v1/auth/register` | 注册 |
| 认证 | GET/PATCH | `/api/v1/auth/me` | 当前用户 |
| 题库 | GET | `/api/v1/questions/` | 题库列表 / 分类 |
| 题库 | POST | `/api/v1/questions/create` | 创建任务 |
| 题库 | POST | **`/api/v1/questions/batch-generate`** | **批量生成（流水线入口）** |
| 题库 | GET | `/api/v1/questions/my-tasks` | 我的任务 |
| 题库 | GET | `/api/v1/questions/tasks/{id}` | 任务状态 |
| 题库 | GET | `/api/v1/questions/tasks/{id}/document` | **下载《科学假设与研究计划》** |
| 题库 | POST | `/api/v1/questions/tasks/{id}/retry` | 重试 |
| 题库 | POST | `/api/v1/questions/feedback` | **人在回路反馈** |
| 项目 | GET/DELETE | `/api/v1/projects/{id}` | 项目详情 / 删除 |
| 项目 | POST | `/api/v1/projects/{id}/start` | 启动流水线 |
| 项目 | POST | `/api/v1/projects/{id}/pause` | 暂停 |
| 项目 | GET | `/api/v1/projects/{id}/status` | 项目状态 |
| 项目 | POST | **`/api/v1/projects/{id}/review`** | **人在回路评审** |
| 实验场 | POST | **`/api/v1/experiment-lab/run`** | 运行验证代码 |
| 实验场 | GET | `/api/v1/experiment-lab/status/{run_id}` | 运行状态 / 图表 / 视频 |
| 实验场 | GET | `/api/v1/experiment-lab/chart/{run_id}/{f}` | 获取图表 |
| 实验场 | GET | `/api/v1/experiment-lab/video/{run_id}` | 获取视频 |
| 实验场 | CRUD | `/api/v1/experiment-lab/templates` | 模板增删改查 |
| 知识库 | POST | `/api/v1/knowledge/upload` | 上传文档 |
| 知识库 | GET | `/api/v1/knowledge/search` | 语义检索 |
| 知识库 | POST | `/api/v1/knowledge/reindex` | 重建索引 |
| 自动化 | CRUD | `/api/v1/automation/{pipeline_id}` | 流水线管理 |
| 自动化 | POST | `/api/v1/automation/{id}/run` | 运行流水线 |
| 多模态 | POST | **`/api/v1/multimodal/analyze-image`** | **图像分析 (Qwen-VL)** |
| 批跑 | POST | `/api/v1/batch_run/run-125` | Science 125 批跑 |
| 可观测 | GET | `/api/v1/observability/traces` | 链路追踪 |
| 可观测 | GET | **`/api/v1/observability/cost`** | **成本统计（算力补贴参考）** |
| 导出 | GET | `/api/v1/export/competition-report/{pid}` | 竞赛报告导出 |
| 文档 | POST | `/api/v1/documents/generate` | 生成文档 |
| 文档 | POST | `/api/v1/documents/review/section` | 章节评审 |
| 聊天 | POST/GET/DELETE | `/api/v1/chat/*` | AI 对话 |
| 流式 | GET | `/api/v1/stream/events` | SSE 事件流 |
| 管理员 | GET | `/api/v1/admin/stats` | 后台统计 |
| 健康 | GET | `/api/health` | 健康检查（根路径） |

---

## 十六、数据库 Schema

核心模型定义在 `backend/app/database/models.py`（524 行，27 个表类）。

| 模型 | 说明 |
|---|---|
| `User` | 用户 / 管理员 |
| `Project` | 研究项目（工作台），含 `final_output` |
| `AgentTask` | 单步 Agent 任务（status / progress） |
| **`QuestionTask`** | **题库任务（关键）**：status / progress / document_path / error_message |
| `ScienceQuestion` | 科学问题题库（125 题） |
| **`Hypothesis`** | **生成的假设（对应标准化 13 字段）** |
| `ExperimentRun` | 实验运行（图表 / 视频） |
| `ExperimentTemplate` | 实验模板 |
| `Document` | 知识库文档 |
| `CustomSkill` | 自定义技能 / Skill |
| `Pipeline` / `PipelineRun` / `PipelineRunLog` | 自动化流水线 |
| `TraceRecord` / `CostRecord` | 链路追踪 / 成本 |
| `ChatMessage` / `ToolCallRecord` | 对话与工具调用 |
| `UploadChunk` | 大文件分片上传 |
| `Notification` / `AuditLog` | 通知 / 审计 |
| `IterationRecord` | 反思迭代记录 |

**关键关系**：
- `QuestionTask` → `ScienceQuestion` → 触发 `Project`
- `Project` → 多个 `AgentTask` → 产出 `Hypothesis` / `IterationRecord` / `final_output`
- `ExperimentRun` 归属 `Project` 或 `QuestionTask`
- `TraceRecord` / `CostRecord` 全局记录调用链与成本

**`QuestionTask` 字段详解**（前端进度 / 状态的真相来源）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| question_id | int | 关联 ScienceQuestion |
| user_id | int | 所属用户 |
| status | str | 'running' / 'completed' / 'failed' |
| result | JSON | 生成模式 / 流水线元数据 |
| document_path | str | 研究报告路径（**完成时必填**） |
| version | int | 版本号 |
| feedback | str | 评审反馈 |
| error_message | str | 失败原因（**应透传到前端**） |
| started_at | datetime | 开始时间 |
| completed_at | datetime | 完成时间（**完成时必填**） |
| created_at | datetime | 创建时间 |
| progress | int | 0-100（由 progress_sync 写入） |

---

## 十七、真实案例演示（对应应用潜力 20 分）

> 赛题要求「真实案例（基于问题集、满足规范的生成结果）」。

### 案例 1：自然科学方向 — 数学物理

**问题**：对粒子物理标准模型研究是否会停止在量子 Yang-Mills 理论上？（数学物理）

流水线（9 阶段）生成：

- **Problem Statement**：现有标准模型在 Yang-Mills 质量间隙问题上存在理论缺口
- **Rationale**：基于规范场论 + Millennium 问题约束推导
- **Technical Details**：代数几何 + 数值格点 QCD
- **Experiments**：Baselines（传统微扰论）+ Metrics（质量间隙精度）
- **References**：真实文献（Clay Institute 官方说明、Atiyah 相关论文等）

### 案例 2：自然科学方向 — 数学

**问题**：黎曼 zeta 函数的零解都有 a+bi 形式吗？（黎曼猜想）

- **Problem Statement**：黎曼猜想的临界线假设尚未证明
- **Rationale**：基于解析数论 + 已知零点的对称性推导
- **Technical Details**：数值验证（Odlyzko 算法）+ 概率启发式模型
- **Experiments**：大规模数值扫描 + 统计偏差检验

### 案例 3：人文社科方向 — 发展经济学

**问题**：为什么改变撒哈拉地区贫困状态的努力几乎全部失败？（发展经济学）

流水线生成：
- 违规行为识别 + 风险预警假设
- 行为数据 / 交易数据分析策略
- 合规性建议（对应赛题「合规操作建议」）

### 案例 4：人文社科方向 — 政治经济学

**问题**：政治与经济自由密切相关吗？（政治经济学）

- **假设**：制度质量中介了政治自由对经济增长的影响
- **Technical Details**：面板数据固定效应模型 + 工具变量法
- **Datasets**：Source（WGI、Freedom House）+ Target（跨国面板）

> **全部 125 个问题均可一键批量生成标准化《科学假设与研究计划》**（`POST /api/v1/batch_run/run-125`）。

---

## 十八、可复现性（对应应用潜力 10 分）

### 18.1 一键运行

```powershell
# 1) 克隆
git clone <repo> && cd AI_Scientist_v2

# 2) 后端
cd backend
python -m venv .venv && .venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate                          # Linux/Mac
pip install -r requirements.txt
copy .env.example .env          # 填入 QWEN_API_KEY
python -m app.database.init_db  # 初始化 SQLite + 内置模板
python run.py --reload          # 启动 :8000

# 3) 前端 (新终端)
cd frontend
npm install
npm run dev                     # 启动 :5173
```

### 18.2 可复现性保障

- ✅ 完整 `requirements.txt` 锁定依赖版本
- ✅ `docker-compose.yml` 容器化部署
- ✅ GitHub Actions CI/CD
- ✅ 数据库持久化 + Alembic 迁移
- ✅ 实验产物（代码 / 图表 / 视频）全部落盘可追溯
- ✅ 每个 QuestionTask 关联 Project + AgentTask，全流程可回溯

---

## 十九、部署

### 19.1 生产构建

```powershell
cd frontend && npm run build       # → dist/
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

`main.py` 通过 `StaticFiles` 挂载 `frontend/dist`，**单端口托管**。

### 19.2 Nginx 反代

```nginx
server {
    listen 80; server_name your.domain;
    client_max_body_size 50m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 二十、容器化（Docker）

**`Dockerfile`（后端）**：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`**：

```yaml
version: '3.9'
services:
  backend:
    build: .
    env_file: ./backend/.env
    ports: ['8000:8000']
    volumes: ['./backend/zhixing.db:/app/zhixing.db']
  frontend:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "npm ci && npm run build && npx vite preview --port 5173"
    volumes: [./frontend:/app]
    ports: ['5173:5173']
```

---

## 二十一、CI/CD

`.github/workflows/ci.yml`：

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_DB: zhixing }
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: cd backend && alembic upgrade head && pytest -q
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/zhixing
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npm ci && npm run build
```

---

## 二十二、测试策略

| 层级 | 工具 | 范围 |
|---|---|---|
| 单元测试 | pytest + httpx | Agent 逻辑、engine wrapper |
| API 测试 | httpx.AsyncClient | 端点契约、认证 |
| E2E | Playwright（建议） | 登录 → 创建项目 → 运行实验 |

**竞赛关键回归用例**：
- `POST /run` → 轮询 `/status` → 期望 `completed` + 图表
- `POST /batch-generate` → `QuestionTask` 最终 `completed` 且 `document_path` 非空
- Mock Qwen 返回 `Arrearage` → 期望 `status='failed'` + 错误透传
- 进度一致性：运行中 `progress <= 95`，`completed` 后 100
- `sns.scatterplot(x='col', y='col')` 不传 data → wrapper 自动注入

---

## 二十三、可观测性与成本

- **链路追踪** (`observability/tracer.py`)：每次 Qwen / 工具调用 → `TraceRecord`
- **成本统计** (`observability/cost_tracker.py`)：Token / 金额，超 `COST_ALERT_THRESHOLD_YUAN` 告警
- **端点**：`/api/v1/observability/traces`、`/cost`
- **竞赛意义**：**成本可控**（阿里云 300 元/人算力补贴可覆盖开发）

---

## 二十四、安全考量

- **自主可控**：全链路国产 Qwen，符合赛题「安全、开放、可持续」要求
- **密钥管理**：`.env` 不入仓，生产用环境变量
- **代码沙箱**：实验代码隔离进程 + 超时（生产建议加 cgroups / firejail）
- **输入校验**：Pydantic 严格校验
- **CORS**：`ALLOWED_ORIGINS` 白名单
- **限流**：`RATE_LIMIT_PER_MINUTE=60`
- **审计**：`AuditLog` 记录关键操作

---

## 二十五、开发规范

- **分支**：`main` / `develop` / `feature/*` / `fix/*`
- **提交**：Conventional Commits (`feat:` / `fix:` / `docs:`)
- **代码**：Black + isort / Prettier + ESLint，TypeScript `strict`
- **API**：RESTful，版本化 `/api/v1`，统一错误响应
- **契约**：`contracts/` Pydantic 模型前后端共用

---

## 二十六、已知问题与排坑

> 沉淀真实踩过的坑（开发 / 答辩均可引用，体现工程深度）。

| 优先级 | 问题 | 根因 | 修复 |
|---|---|---|---|
| P0 | 进度显示 100% 但未生成完 | `progress_sync` 只更新 progress 不更新 status | 让 progress=100 与 status=completed 原子绑定；运行中上限 95% |
| P0 | 阿里云欠费 `Arrearage` | DashScope 账号欠费，Qwen API 400 | 充值 → 等同步 → 验证连通；错误透传前端 |
| P1 | `POST /run` 返回 500 | `RunRequest` 缺 `data_table` 字段 | 加 `data_table: Optional[dict] = None` |
| P1 | seaborn 简洁写法报错 | `sns.scatterplot(x='col')` 未传 data | wrapper 自动注入 `data=df` |
| P2 | `_exec` 异常被吞 | BackgroundTask 异常未写回 status | try/except 写 `status='failed'` |
| P2 | 前端「资源解析服务请求失败」 | 前端直连 DashScope CORS | 统一走后端代理 |

### P0-2 阿里云欠费排查（竞赛常见）

```
1. 登录阿里云费用控制台确认欠费 → 充值（阿里云 300 元算力补贴可覆盖开发）
2. 等待 3-5 分钟（余额同步延迟）
3. 验证：python -c "import dashscope; ..."  (应返回 Pong)
4. 新建任务重跑（旧任务已脏，需重置）
```

### P0-1 进度 100% 但任务未完成

**现象**：题库任务 `status='running'` 但 `progress=100`、`document_path=None`。

**根因**：`progress_sync.py` 每 5s 只写 `progress`；`status` 仅在 `questions.py` 文档回写成功分支设置。

**修复**：

```sql
-- 1) 重置脏数据
UPDATE question_tasks
SET status='failed', error_message='已重置: 进度异常'
WHERE status='running' AND progress=100 AND document_path IS NULL AND completed_at IS NULL;
```

```python
# 2) 前端进度上限 (questions.py 附近)
progress = (100 if r.status == 'completed' and r.completed_at else
            (r.progress if (r.progress or 0) < 100 else 95))
```

---

## 二十七、路线图

| 状态 | 项目 |
|---|---|
| ✅ 已完成 | 题库批量生成、多智能体流水线、实验沙箱、图表 / 视频、知识库、多模态、可观测性、CI/CD |
| 🔄 进行中 | 进度 / 状态一致性修复、Celery 持久化队列、容器隔离沙箱 |
| 📋 计划 | 多 LLM 路由（Qwen/GPT/DeepSeek）、协作编辑、论文自动投稿、移动端 |

---

## 二十八、提交清单（对照赛题第八点）

> 赛题要求提交材料，本仓库组织结构直接对应：

| 赛题提交项 | 本仓库对应 |
|---|---|
| 技术方案文档（PDF ≤ 20 页） | `docs/技术方案.md`（本文档扩展） |
| 研究问题与解决方法 | 本文档第二、三、十七章 |
| AI Scientist 架构设计 | 第四、六章（含架构图） |
| 基于 Qwen 的多智能体架构 | 第六章（16 Agent + Orchestrator） |
| 真实案例 | 第十七章（125 问题集批量生成） |
| 源代码 | `backend/` + `frontend/` |
| 智能体工作流程核心代码 | `agents/orchestrator.py` + `experiment_engine.py` |
| 上下文工程设计 | `agents/contracts/` + `schemas/` |
| 可交互前端页面 | `frontend/`（Vue 3） |
| 演示视频（≤10 分钟） | `docs/demo.mp4` |
| 百炼调用凭证 / 截图 | `docs/百炼调用截图.png` |
| 报名表（盖章） | `docs/报名表.pdf` |

**压缩包命名**：`学校-姓名-作品名-联系电话`
**提交地址**：https://survey.aliyun.com/apps/zhiliao/A4e_qqNGu
**截止时间**：**2026 年 9 月 5 日前**

---

## 二十九、FAQ

**Q: 为什么进度 100% 却还在运行？**
A: 见第二十六章 P0-1，本质是进度与状态解耦的 Bug，修复方案见该章。

**Q: 如何验证 Qwen 连通性？**
A: `python -c "import dashscope; print(...)"`，返回 Pong 即正常。

**Q: 如何切换数据库？**
A: 改 `DATABASE_URL` 为 PostgreSQL + 装 asyncpg + `alembic upgrade head`。

**Q: 前端连不上后端？**
A: 确认 Vite 代理 `/api` → `:8000`，或生产 Nginx 配置。

**Q: 假设生成的参考文献会虚构吗？**
A: 不会。`references` 全部来自 LiteratureAgent 真实检索，**严禁虚构**。

**Q: 支持哪些学科方向？**
A: 自然科学 + 人文社科全覆盖（赛题双赛道）。

**Q: 算力成本如何控制？**
A: 阿里云提供 300 元/人算力补贴；通过 `CostRecord` 实时统计，单次生成可控在数元内。

---

## 三十、术语表

| 术语 | 含义 |
|---|---|
| Agent | 专职 AI 角色（假设生成、文献调研等），继承 BaseAgent |
| Orchestrator | 中央编排器，管理 Agent 间状态流转 |
| QuestionTask | 题库维度的生成任务 |
| Hypothesis | 生成的科学假设（对应标准化 13 字段） |
| Wrapper | 动态生成的 `_run.py`，为实验代码注入 df / 图表捕获 |
| progress_sync | 每 5s 同步进度的后台任务 |
| data_table | 前端传入的表格数据 `{columns, rows}` |
| batch_pipeline | 题库批量生成流水线（9 阶段） |
| DashScope / 百炼 | 阿里云大模型服务平台，提供 Qwen API |
| Reflection | 反思迭代（人在回路核心） |

---

## 三十一、关键文件索引

| 文件 | 作用 |
|---|---|
| `backend/run.py` | 启动入口 |
| `backend/main.py` | FastAPI app 装配 |
| `backend/app/api/v1/questions.py` | **题库流水线（1441 行）★** |
| `backend/app/api/v1/experiment_lab.py` | 实验模拟场 API |
| `backend/app/services/experiment_engine.py` | **代码沙箱引擎（472 行）★** |
| `backend/app/core/progress_sync.py` | 进度同步器 |
| `backend/app/agents/orchestrator.py` | **Agent 编排器（732 行）★** |
| `backend/app/agents/qwen_client.py` | **Qwen 调用封装 ★** |
| `backend/app/database/models.py` | 数据库模型（Hypothesis 等） |
| `backend/.env` | 环境变量（QWEN_API_KEY） |
| `frontend/vite.config.ts` | Vite 配置 + API 代理 |
| `frontend/src/data/science125.ts` | 125 科学问题集 |
| `frontend/src/views/workspace/QuestionsView.vue` | 题库视图（最大，1355 行） |

---

## 三十二、许可证与致谢

- **竞赛专用**：挑战杯「揭榜挂帅」XH-202619 参赛作品
- **基座模型**：阿里云百炼 Qwen（国产开源，Apache 2.0 / 通义千问开源协议）
- **致谢**：阿里云算力补贴 + 百炼平台 + 中国科学院国家天文台人工智能推进委员会 + 他山学科交叉创新协会

---

## 附录 A：评审得分点速查

| 评分项 | 分值 | 本方案对应章节 |
|---|---|---|
| 核心假设创新性与自洽性 | 20 | 六、七、十七 |
| 方案可落地验证性 | 20 | 八、十八 |
| 多智能体协作设计 | 15 | **六（重点）** |
| 多模态大模型处理成效 | 15 | **十（重点）** |
| 实际场景问题支撑 | 10 | 十七 |
| 论文 / 专利转化潜力 | 10 | 九、十七 |
| 代码与结果可复现性 | 10 | **十八（重点）** |

---

## 附录 B：数据库重置与诊断 SQL

```sql
-- 重置卡住的脏任务
UPDATE question_tasks
SET status='failed', error_message='已重置: 进度异常'
WHERE status='running' AND progress=100 AND document_path IS NULL AND completed_at IS NULL;

-- 查看运行中任务
SELECT id, status, progress, document_path, started_at
FROM question_tasks WHERE status='running';

-- 查看已完成任务的标准化输出
SELECT id, result, document_path, completed_at
FROM question_tasks WHERE status='completed' ORDER BY id DESC LIMIT 10;

-- 查看 Agent 任务完成度 (progress_sync 依据)
SELECT project_id, COUNT(*) as total,
       SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) as done
FROM agent_tasks GROUP BY project_id;
```

---

## 附录 C：前端 Vue 组件与后端端点对照

| 前端视图 | 路由 | 主要调用的后端端点 |
|---|---|---|
| 题库视图 | `/questions` | `questions.py` (batch-generate, tasks) |
| 工作台 / 项目详情 | `/project/:id` | `projects.py` (start, review, status) |
| 实验模拟场 | `/experiment-lab` | `experiment_lab.py` (run, status, chart) |
| 知识库 | `/knowledge` | `knowledge.py` (upload, search) |
| 自动化流水线 | `/automation` | `automation.py` |
| 智能体广场 | `/agents` | `agents.py` |
| 链路追踪 | `/traces` | `observability.py` |
| 成本统计 | `/cost` | `observability.py` |
| 管理员后台 | `/admin` | `admin.py` |

---
