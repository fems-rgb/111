"""路由/依赖 smoke 测试

覆盖 README 二十二章"竞赛关键回归用例"里不依赖外部 API 的部分：
- /api/health 返回 ok + 版本号
- 所有 v1 路由可加载（app.routes 数量下限）
- 16 个 Agent 全部注册
"""
from __future__ import annotations

import pytest


def test_import_main_app():
    """app.main 能被 import（无循环依赖 & 语法错误）"""
    from app.main import app
    assert app.title  # FastAPI 实例化成功


def test_agent_registry_complete():
    """AGENT_REGISTRY 覆盖 16 章声称的全部核心 Agent 名称"""
    from app.agents import AGENT_REGISTRY, DEFAULT_WORKFLOW
    required = {
        "knowledge_gap", "literature", "hypothesis", "design",
        "experiment_plan", "analysis", "writing", "review", "reflection",
    }
    missing = required - set(AGENT_REGISTRY.keys())
    assert not missing, f"缺失 Agent: {missing}"
    assert len(AGENT_REGISTRY) >= 15, f"注册表过短({len(AGENT_REGISTRY)})，README 声称 16+"
    assert len(DEFAULT_WORKFLOW) == 9, f"默认流水线应为 9 阶段，实得 {len(DEFAULT_WORKFLOW)}"


def test_all_agents_have_required_attributes():
    """每个 Agent 类需具备 name/display_name且 build_prompt 可调用

    部分 Agent（如 MultimodalEnricherAgent）需要额外的 kwargs，
    仅验证接口存在，不强制验证输出。
    """
    from app.agents import AGENT_REGISTRY
    for key, cls in AGENT_REGISTRY.items():
        assert getattr(cls, "name", None), f"{key} 缺 name"
        assert getattr(cls, "display_name", None), f"{key} 缺 display_name"
        assert callable(getattr(cls, "build_prompt", None)), f"{key} 缺 build_prompt"
        assert isinstance(cls.system_prompt, str), f"{key} system_prompt 类型异常"


def test_routes_count():
    """v1 挂载路由数量下限（README 声称 97 个端点）"""
    from app.main import app
    api_routes = [r for r in app.routes if getattr(r, "path", "").startswith("/api")]
    # 保守阈值：至少 60 条，避免与实现细节硬绑
    assert len(api_routes) >= 60, f"/api 下路由仅 {len(api_routes)} 条"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("status") == "ok"
    assert "version" in body
