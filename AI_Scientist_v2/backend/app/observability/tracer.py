"""智研星枢 - 全链路追踪器"""
import uuid
import time
import json
import logging
from contextvars import ContextVar
from typing import Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_current_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_current_span_id: ContextVar[Optional[str]] = ContextVar('span_id', default=None)
_spans_buffer: ContextVar[list] = ContextVar('spans_buffer', default=[])


class Span:
    def __init__(self, span_type: str, span_name: str, project_id: int = None, task_id: int = None):
        self.span_id = uuid.uuid4().hex[:16]
        self.trace_id = _current_trace_id.get() or uuid.uuid4().hex[:32]
        self.parent_span_id = _current_span_id.get()
        self.span_type = span_type
        self.span_name = span_name
        self.project_id = project_id
        self.task_id = task_id
        self.input_data = ""
        self.output_data = ""
        self.metadata = {}
        self.tokens_used = 0
        self.cost_yuan = 0.0
        self.status = "ok"
        self.error_detail = ""
        self.start_time = time.time()
        self.duration_ms = 0

    def set_input(self, data: Any):
        self.input_data = json.dumps(data, ensure_ascii=False, default=str)[:50000]

    def set_output(self, data: Any):
        self.output_data = json.dumps(data, ensure_ascii=False, default=str)[:50000]

    def set_error(self, error: str):
        self.status = "error"
        self.error_detail = str(error)[:2000]

    def finish(self):
        self.duration_ms = int((time.time() - self.start_time) * 1000)

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id, "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "span_type": self.span_type, "span_name": self.span_name,
            "project_id": self.project_id, "task_id": self.task_id,
            "input_data": self.input_data, "output_data": self.output_data,
            "metadata": self.metadata, "tokens_used": self.tokens_used,
            "cost_yuan": self.cost_yuan, "status": self.status,
            "error_detail": self.error_detail, "duration_ms": self.duration_ms,
            "created_at": datetime.now(timezone.utc).isoformat()
        }


class Tracer:
    @staticmethod
    def start_trace() -> str:
        trace_id = uuid.uuid4().hex[:32]
        _current_trace_id.set(trace_id)
        _current_span_id.set(None)
        _spans_buffer.set([])
        logger.debug(f"新追踪开始: {trace_id}")
        return trace_id

    @staticmethod
    def create_span(span_type: str, span_name: str, project_id: int = None, task_id: int = None) -> Span:
        span = Span(span_type, span_name, project_id, task_id)
        old_span_id = _current_span_id.get()
        _current_span_id.set(span.span_id)
        span.parent_span_id = old_span_id
        buffer = _spans_buffer.get()
        buffer.append(span)
        _spans_buffer.set(buffer)
        return span

    @staticmethod
    def finish_span(span: Span):
        span.finish()
        icon = "✅" if span.status == "ok" else "❌"
        logger.info(f"[Trace] {icon} {span.span_name} | {span.span_type} | {span.duration_ms}ms | tokens={span.tokens_used} | cost={span.cost_yuan:.4f}")

    @staticmethod
    def get_all_spans() -> list:
        return _spans_buffer.get()

    @staticmethod
    def get_trace_id() -> Optional[str]:
        return _current_trace_id.get()


async def save_spans_to_db(db, spans: list):
    from app.database.models import TraceRecord
    records = []
    for span in spans:
        if span.project_id:
            records.append(TraceRecord(
                project_id=span.project_id, task_id=span.task_id,
                trace_id=span.trace_id, parent_span_id=span.parent_span_id,
                span_id=span.span_id, span_type=span.span_type,
                span_name=span.span_name, input_data=span.input_data,
                output_data=span.output_data, metadata_=span.metadata,
                tokens_used=span.tokens_used, cost_yuan=span.cost_yuan,
                duration_ms=span.duration_ms, status=span.status,
                error_detail=span.error_detail
            ))
    if records:
        db.add_all(records)
        await db.commit()
        logger.info(f"💾 已保存 {len(records)} 条追踪记录")