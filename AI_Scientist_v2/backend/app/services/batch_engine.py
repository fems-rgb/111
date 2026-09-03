"""智研星瀚 - 125题批量运行引擎（赛道一P13/P19/P20）"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Science 125 Questions 子集（示例，实际应加载完整列表）
SCIENCE_125_QUESTIONS = [
    {"id": "Q001", "text": "宇宙由什么构成？"},
    {"id": "Q002", "text": "意识的生物学基础是什么？"},
    {"id": "Q003", "text": "为什么人类会做梦？"},
    {"id": "Q004", "text": "地球生命如何起源？"},
    {"id": "Q005", "text": "是否存在其他宜居星球？"},
    # ... 实际使用时加载完整125题JSON文件
]


class BatchRunEngine:
    """批量运行125个科学问题的科研闭环"""

    def __init__(self):
        self.results: dict[str, dict] = {}
        self.is_running = False

    async def run_all(self, questions: Optional[list[dict]] = None,
                      output_dir: str = "batch_results",
                      max_concurrent: int = 3) -> dict:
        """批量执行所有问题"""
        if self.is_running:
            return {"error": "批量任务已在运行中"}

        self.is_running = True
        questions = questions or SCIENCE_125_QUESTIONS
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"🚀 开始批量运行 {len(questions)} 个科学问题")
        start_time = time.time()

        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []
        for q in questions:
            tasks.append(self._run_single(q, semaphore, output_path))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        completed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
        failed = len(results) - completed

        summary = {
            "total": len(questions),
            "completed": completed,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_dir": str(output_path)
        }

        # 保存汇总
        with open(output_path / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.is_running = False
        logger.info(f"✅ 批量运行完成: {completed}/{len(questions)} 成功, 耗时 {elapsed:.1f}s")
        return summary

    async def _run_single(self, question: dict, semaphore: asyncio.Semaphore,
                          output_path: Path) -> dict:
        """执行单个问题的科研闭环"""
        async with semaphore:
            qid = question["id"]
            qtext = question["text"]
            start = time.time()

            try:
                from app.database.session import AsyncSessionLocal
                from app.agents.orchestrator import orchestrator
                from app.database.models import Project, User
                from sqlalchemy import select

                async with AsyncSessionLocal() as db:
                    # 创建临时项目
                    project = Project(
                        title=f"[Batch] {qid}: {qtext[:50]}",
                        research_question=qtext,
                        user_id=1,  # 默认管理员
                        status="planning"
                    )
                    db.add(project)
                    await db.commit()
                    await db.refresh(project)

                    # 运行完整流水线
                    result = await orchestrator.start_project(
                        db=db, project_id=project.id, user_id=1, mode="quick"
                    )

                    # 等待完成（简化版，实际应轮询状态）
                    await asyncio.sleep(5)

                    # 获取最终输出
                    proj_result = await db.execute(
                        select(Project).where(Project.id == project.id)
                    )
                    proj = proj_result.scalar_one_or_none()

                    duration = time.time() - start
                    output_data = {
                        "question_id": qid,
                        "question_text": qtext,
                        "status": "completed",
                        "final_output": proj.final_output if proj else "",
                        "duration_seconds": round(duration, 2),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # 保存单题结果
                    with open(output_path / f"{qid}.json", "w", encoding="utf-8") as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)

                    return output_data

            except Exception as e:
                duration = time.time() - start
                logger.error(f"❌ {qid} 执行失败: {e}", exc_info=True)
                error_data = {
                    "question_id": qid,
                    "question_text": qtext,
                    "status": "failed",
                    "error_message": str(e),
                    "duration_seconds": round(duration, 2)
                }
                with open(output_path / f"{qid}.json", "w", encoding="utf-8") as f:
                    json.dump(error_data, f, ensure_ascii=False, indent=2)
                return error_data


batch_engine = BatchRunEngine()
