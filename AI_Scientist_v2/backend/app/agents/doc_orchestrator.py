"""智研星瀚 - 多Agent文档编排器
按 nh_202619_track1 模板的12字段依赖顺序，逐字段调用 SectionWriterAgent 生成文档。
"""
import logging
import time
from typing import Optional, Dict, Callable

from app.contracts.document_template import get_template, DocumentTemplate
from app.agents.doc_planner import DocumentPlannerAgent, SectionWriterAgent

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    """按模板驱动的12字段文档生成编排器"""

    def __init__(self, template_id: str = "nh_202619_track1", model: str = None):
        self.template_id = template_id
        self.template: DocumentTemplate = get_template(template_id)
        self.model = model or "qwen-max"
        # Agent 内部自动调用 call_qwen，无需手动管理 LLM client
        self.planner = DocumentPlannerAgent()
        self.writer = SectionWriterAgent()

    async def generate(
        self,
        research_question: str,
        context: str,
        project_id: int = None,
        task_id: int = None,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """
        完整文档生成流程：
        1. Planner 规划12字段的写作计划
        2. 按依赖拓扑排序逐字段生成
        3. 组装最终文档

        Returns: {"document": str, "metadata": dict}
        """
        start_time = time.time()
        metadata = {
            "template_id": self.template_id,
            "project_id": project_id,
            "task_id": task_id,
            "sections": {},
            "total_tokens": 0,
            "total_cost": 0.0,
            "final_score": 0.0,
        }

        # === Step 1: Planner 规划 ===
        logger.info("[Orchestrator] Step 1: Planning document structure...")
        plan_result = await self.planner.execute(
            research_question=research_question,
            context=context,
            model=self.model,
            project_id=project_id,
            task_id=task_id,
            template_id=self.template_id,
        )
        plan_raw = plan_result["output"]
        plan = self.planner.parse_plan(plan_raw)
        section_plans = {sp["section_id"]: sp for sp in plan.get("section_plans", [])}
        hypothesis_list = plan.get("hypothesis_list", [])
        metadata["total_tokens"] += plan_result.get("tokens", 0)
        metadata["total_cost"] += plan_result.get("cost", 0.0)
        logger.info(f"[Orchestrator] Plan ready: {len(section_plans)} sections, {len(hypothesis_list)} hypotheses")

        if progress_callback:
            await progress_callback("planning_done", {"plan": plan})

        # === Step 2: 拓扑排序 + 逐字段生成 ===
        execution_order = self._topo_sort(self.template.sections)
        completed_sections: Dict[str, str] = {}

        for i, spec in enumerate(execution_order):
            logger.info(f"[Orchestrator] Generating section {i+1}/{len(execution_order)}: {spec.section_id} ({spec.title_cn})")

            section_plan = section_plans.get(spec.section_id, {})
            writer_result = await self.writer.execute(
                research_question=research_question,
                context=context,
                model=self.model,
                project_id=project_id,
                task_id=task_id,
                section_spec=spec,
                section_plan=section_plan,
                completed_sections=completed_sections,
                hypothesis_list=hypothesis_list,
            )
            content = writer_result["output"]
            completed_sections[spec.section_id] = content
            metadata["sections"][spec.section_id] = {
                "words": len(content),
                "status": "completed",
            }
            metadata["total_tokens"] += writer_result.get("tokens", 0)
            metadata["total_cost"] += writer_result.get("cost", 0.0)
            logger.info(f"[Orchestrator] Done {spec.section_id}: {len(content)} chars")

            if progress_callback:
                await progress_callback("section_done", {
                    "section_id": spec.section_id,
                    "index": i + 1,
                    "total": len(execution_order),
                    "chars": len(content),
                })

        # === Step 3: 组装文档 ===
        document = self._assemble(completed_sections)
        elapsed = time.time() - start_time
        metadata["elapsed_seconds"] = round(elapsed, 2)
        metadata["total_chars"] = len(document)
        metadata["section_count"] = len(completed_sections)

        logger.info(
            f"[Orchestrator] Document generated: {len(document)} chars, "
            f"{len(completed_sections)} sections, {elapsed:.1f}s"
        )

        return {"document": document, "metadata": metadata}

    def _topo_sort(self, sections: list) -> list:
        """按 depends_on 拓扑排序"""
        resolved = []
        resolved_ids = set()
        remaining = list(sections)

        while remaining:
            progress = False
            for s in remaining[:]:
                if all(dep in resolved_ids for dep in s.depends_on):
                    resolved.append(s)
                    resolved_ids.add(s.section_id)
                    remaining.remove(s)
                    progress = True
            if not progress:
                logger.warning(f"[Orchestrator] Circular dependency, forcing order for: {[s.section_id for s in remaining]}")
                resolved.extend(remaining)
                break
        return resolved

    def _assemble(self, sections: Dict[str, str]) -> str:
        """按模板顺序组装最终文档，带中英文标题"""
        parts = []
        for spec in self.template.sections:
            content = sections.get(spec.section_id, "[MISSING]")
            header = f"## {spec.title_cn}（{spec.title_en}）"
            parts.append(f"{header}\n\n{content}")
        return "\n\n---\n\n".join(parts)
