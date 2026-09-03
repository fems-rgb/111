"""Document Engine - Production-grade document generation with quality gate loop.
Single entry point for all document generation. Delegates to DocumentOrchestrator
with embedded QualityGate → Revision cycle.
"""
import logging
import time
from typing import Optional, Callable

from app.agents.doc_orchestrator import DocumentOrchestrator
from app.agents.doc_quality import QualityGateAgent, RevisionAgent
from app.contracts.document_template import get_template

logger = logging.getLogger(__name__)

# Production limits
MAX_QUALITY_ITERATIONS = 3       # Max review-revise cycles
GLOBAL_TIMEOUT_SECONDS = 600     # 10 min hard cap
TOKEN_BUDGET = 80000             # Max tokens per generation
PASS_SCORE_THRESHOLD = 7.0       # Per-section pass line


class DocumentEngine:
    """
    Production document generation engine.
    
    Pipeline: Plan → Write Sections → Quality Gate → Revise (up to N rounds) → Assemble
    
    All document generation MUST go through this class.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def generate_document(
        self,
        research_question: str,
        context: str = "",
        template_id: str = "nh_202619_track1",
        review_callback: Optional[Callable] = None,
        project_id: int = None,
        task_id: int = None,
        max_quality_iterations: int = MAX_QUALITY_ITERATIONS,
        token_budget: int = TOKEN_BUDGET,
    ) -> dict:
        """
        Full production pipeline with quality gate.
        
        Returns:
            {
                "success": bool,
                "document": str,
                "plan": dict,
                "sections": dict,
                "quality_report": dict,
                "metadata": {tokens, cost, elapsed, iterations, ...}
            }
        """
        start_time = time.time()
        metadata = {
            "template_id": template_id,
            "project_id": project_id,
            "task_id": task_id,
            "iterations": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

        try:
            # === Phase 1: Generate ===
            logger.info(f"[DocEngine] Phase 1: Generating document (template={template_id})")
            orchestrator = DocumentOrchestrator(template_id=template_id, model=None)
            gen_result = await orchestrator.generate(
                research_question=research_question,
                context=context,
                project_id=project_id,
                task_id=task_id,
                progress_callback=review_callback,
            )

            document = gen_result["document"]
            sections = gen_result.get("sections", {})
            plan = gen_result.get("plan", {})
            gen_metadata = gen_result.get("metadata", {})
            metadata["total_tokens"] += gen_metadata.get("total_tokens", 0)
            metadata["total_cost"] += gen_metadata.get("total_cost", 0.0)

            # Token budget check
            if metadata["total_tokens"] > token_budget:
                logger.warning(
                    f"[DocEngine] Token budget exceeded: {metadata['total_tokens']}/{token_budget}. "
                    f"Skipping quality gate."
                )
                return self._build_result(True, document, plan, sections, None, metadata, start_time,
                                          warning="Token budget exceeded, quality gate skipped")

            # === Phase 2: Quality Gate Loop ===
            template = get_template(template_id)
            quality_gate = QualityGateAgent()
            revision_agent = RevisionAgent()
            quality_report = None

            for iteration in range(1, max_quality_iterations + 1):
                metadata["iterations"] = iteration
                elapsed = time.time() - start_time
                if elapsed > GLOBAL_TIMEOUT_SECONDS:
                    logger.warning(f"[DocEngine] Global timeout ({GLOBAL_TIMEOUT_SECONDS}s) reached at iteration {iteration}")
                    break

                logger.info(f"[DocEngine] Quality Gate iteration {iteration}/{max_quality_iterations}")

                # Review
                gate_result = await quality_gate.execute(
                    research_question=research_question,
                    context=context,
                    template_id=template_id,
                    document_content=document,
                    iteration=iteration,
                    project_id=project_id,
                    task_id=task_id,
                )
                metadata["total_tokens"] += gate_result.get("tokens", 0)
                metadata["total_cost"] += gate_result.get("cost", 0.0)

                report = quality_gate.parse_scores(gate_result["output"], template)
                quality_report = {
                    "overall_score": report.overall_score,
                    "passed": report.passed,
                    "iteration": iteration,
                    "revision_priority": report.revision_priority,
                    "global_issues": report.global_issues,
                    "section_scores": [
                        {"section_id": s.section_id, "overall": s.overall, "issues": s.issues}
                        for s in report.section_scores
                    ],
                }

                if review_callback:
                    await review_callback("quality_review_done", quality_report)

                logger.info(
                    f"[DocEngine] Iteration {iteration}: score={report.overall_score:.1f}, "
                    f"passed={report.passed}, revisions={len(report.revision_priority)}"
                )

                # Pass check
                if report.passed:
                    logger.info(f"[DocEngine] Quality gate PASSED at iteration {iteration}")
                    break

                # Budget re-check before revising
                if metadata["total_tokens"] > token_budget:
                    logger.warning("[DocEngine] Token budget exceeded before revision, stopping")
                    break

                # Revise failing sections
                score_map = {s.section_id: s for s in report.section_scores}
                for sid in report.revision_priority:
                    spec = next((s for s in template.sections if s.section_id == sid), None)
                    score = score_map.get(sid)
                    original = sections.get(sid, "")

                    if not spec or not score or not original:
                        continue

                    # Skip sections that are already above threshold
                    if score.overall >= PASS_SCORE_THRESHOLD:
                        continue

                    logger.info(f"[DocEngine] Revising section {sid} (score={score.overall:.1f})")
                    rev_result = await revision_agent.execute(
                        research_question=research_question,
                        context=context,
                        section_spec=spec,
                        original_content=original,
                        quality_score=score,
                        global_issues=report.global_issues,
                        project_id=project_id,
                        task_id=task_id,
                    )
                    metadata["total_tokens"] += rev_result.get("tokens", 0)
                    metadata["total_cost"] += rev_result.get("cost", 0.0)

                    revised_content = rev_result["output"]
                    sections[sid] = revised_content

                    if review_callback:
                        await review_callback("section_revised", {"section_id": sid, "chars": len(revised_content)})

                # Re-assemble after revision
                document = orchestrator._assemble(sections)

            # === Done ===
            success = True
            warning = None
            if quality_report and not quality_report.get("passed"):
                warning = f"Quality gate did not pass after {metadata['iterations']} iterations (score={quality_report.get('overall_score', 0):.1f})"
                logger.warning(f"[DocEngine] {warning}")

            return self._build_result(success, document, plan, sections, quality_report, metadata, start_time, warning=warning)

        except Exception as e:
            logger.error(f"[DocEngine] Generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "document": "",
                "plan": {},
                "sections": {},
                "quality_report": None,
                "metadata": metadata,
            }

    @staticmethod
    def _build_result(success, document, plan, sections, quality_report, metadata, start_time, warning=None):
        elapsed = round(time.time() - start_time, 2)
        metadata["elapsed_seconds"] = elapsed
        metadata["total_chars"] = len(document)
        result = {
            "success": success,
            "document": document,
            "plan": plan,
            "sections": sections,
            "quality_report": quality_report,
            "metadata": metadata,
        }
        if warning:
            result["warning"] = warning
        return result
