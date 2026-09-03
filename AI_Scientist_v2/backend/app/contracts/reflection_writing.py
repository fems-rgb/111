
from pydantic import BaseModel
from typing import List, Optional

class HypothesisRevision(BaseModel):
    original: str
    revised: str
    rationale: str

class StatThreshold(BaseModel):
    test_name: str
    p_value: float
    confidence_level: float

class ProtocolVersion(BaseModel):
    instrument: str
    model_name: str
    version: str

class ReflectionFeedback(BaseModel):
    hypothesis_revisions: List[HypothesisRevision] = []
    statistical_requirements: List[StatThreshold] = []
    protocol_updates: List[ProtocolVersion] = []
    maturity_score: float = 0.0

class WritingRevisionRequest(BaseModel):
    original_content: str
    feedback: ReflectionFeedback
    target_sections: List[str] = ['introduction', 'methods', 'results']
