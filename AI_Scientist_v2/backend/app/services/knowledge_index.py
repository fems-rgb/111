"""知识库索引服务 —— 当前为轻量级全文检索抽象层。

生产级扩展路径：
- 嵌入模型：DashScope text-embedding-v3
- 向量库：ChromaDB / FAISS
- 混合检索：BM25 + Dense 并行后融合
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def reindex_knowledge_base(user_id: int = None):
    """
    重建知识库索引（后台任务调用）
    
    TODO: 实现以下功能
    - 遍历用户所有 Document
    - 对 structured_data / summary 做向量化嵌入
    - 写入向量数据库（如 ChromaDB / FAISS）
    - 更新 Document.parse_status
    """
    logger.info(f"[KnowledgeIndex] reindex triggered for user_id={user_id}")
    # 当前为 no-op 占位，不影响其他功能
    return {"status": "ok", "message": "知识索引重建完成（占位）"}
