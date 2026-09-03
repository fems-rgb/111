"""智研星瀚 - 125题批量运行API"""
from fastapi import APIRouter, BackgroundTasks
from app.services.batch_engine import batch_engine

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/run-125")
async def run_125_questions(background_tasks: BackgroundTasks):
    """触发125题批量运行"""
    if batch_engine.is_running:
        return {"error": "批量任务已在运行中，请稍后再试"}
    background_tasks.add_task(batch_engine.run_all)
    return {"message": "125题批量运行已启动", "status": "started"}


@router.get("/status")
async def get_batch_status():
    """获取批量运行状态"""
    return {
        "is_running": batch_engine.is_running,
        "results_count": len(batch_engine.results)
    }
