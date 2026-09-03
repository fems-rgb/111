"""智研星瀚 - Agent注册表"""
from app.agents.knowledge_gap import KnowledgeGapAgent
from app.agents.literature import LiteratureAgent
from app.agents.design import DesignAgent
from app.agents.analysis import AnalysisAgent
from app.agents.writing import WritingAgent
from app.agents.review import ReviewAgent
from app.agents.hypothesis import HypothesisAgent
from app.agents.experiment_plan import ExperimentPlanAgent
from app.agents.reflection import ReflectionAgent
from app.agents.doc_planner import DocumentPlannerAgent, SectionWriterAgent
from app.agents.doc_quality import QualityGateAgent, RevisionAgent
from app.agents.doc_multimodal import MultimodalEnricherAgent

AGENT_REGISTRY = {
    "knowledge_gap": KnowledgeGapAgent,
    "literature": LiteratureAgent,
    "design": DesignAgent,
    "analysis": AnalysisAgent,
    "writing": WritingAgent,
    "review": ReviewAgent,
    "hypothesis": HypothesisAgent,
    "experiment_plan": ExperimentPlanAgent,
    "experiment": ExperimentPlanAgent,
    "reflection": ReflectionAgent,
    # === 多模态文档生成引擎 ===
    "document_planner": DocumentPlannerAgent,
    "section_writer": SectionWriterAgent,
    "quality_gate": QualityGateAgent,
    "revision": RevisionAgent,
    "multimodal_enricher": MultimodalEnricherAgent,
}

DEFAULT_WORKFLOW = ["knowledge_gap", "literature", "hypothesis", "design", "experiment_plan", "analysis", "writing", "review", "reflection"]

# 多模态文档生成工作流（替代原writing单步）
DOCUMENT_WORKFLOW = ["knowledge_gap", "literature", "hypothesis", "design", "experiment_plan", "analysis", "document_generate", "review", "reflection"]


def get_agent_info() -> list:
    return [{"name": n, "display_name": c.display_name, "description": c.description,
             "requires_review": c.requires_review} for n, c in AGENT_REGISTRY.items()]
from app.agents.doc_reviewer import SectionReviewerAgent, DocumentReviewerAgent
