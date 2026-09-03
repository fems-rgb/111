"""智研星瀚 - 赛道一标准化科研输出Schema（对齐赛题12字段要求 v3）"""
import re
import json
import logging
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)


class ResearchOutput(BaseModel):
    """对标赛题要求的12个标准化字段 + 2个扩展字段"""
    paper_title: str = Field("", description="符合学术出版规范的标题(字段7)")
    paper_abstract: str = Field("", description="含背景、方法、预期结果的完整摘要(字段8)")
    problem_statement: str = Field("", description="待研究的科学问题(字段1)")
    rationale: str = Field("", description="解决思路与推理链(字段2)")
    technical_details: str = Field("", description="技术手段与方法论细节(字段3)")
    datasets: str = Field("", description="数据集总述(字段4)")
    datasets_source: str = Field("", description="假设推演依据的历史数据(字段5 Source)")
    datasets_target: str = Field("", description="验证实验所需的拟采集数据特征(字段6 Target)")
    methods: str = Field("", description="方法论详述(字段9)")
    experiments: str = Field("", description="实验设计含Baselines+Metrics(字段10)")
    results: str = Field("", description="实验结果与分析(字段11)")
    references: list[str] = Field(default_factory=list, description="参考文献列表(字段12 GB/T 7714)")
    ethics_statement: str = Field("", description="伦理合规声明(扩展字段)")
    system_architecture: str = Field("", description="AI Scientist系统架构(扩展字段)")
    iteration_version: int = Field(1, description="迭代版本号")
    closure_maturity: float = Field(0.0, description="闭环成熟度 0-100%")

    @classmethod
    def parse_from_llm(cls, raw_text: str) -> "ResearchOutput | None":
        """从Qwen输出中提取JSON并解析为ResearchOutput"""
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_text, re.DOTALL)
        if match:
            try:
                return cls.model_validate_json(match.group(1))
            except Exception as e:
                logger.warning(f"JSON代码块解析失败: {e}")
        try:
            return cls.model_validate_json(raw_text)
        except Exception:
            pass
        brace_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if brace_match:
            try:
                return cls.model_validate_json(brace_match.group(0))
            except Exception:
                pass
        try:
            data = {}
            field_patterns = {
                "paper_title": r"##\s*7\.\s*标题.*?\n([\s\S]*?)(?=##\s*8\.|\Z)",
                "paper_abstract": r"##\s*8\.\s*摘要.*?\n([\s\S]*?)(?=##\s*9\.|\Z)",
                "problem_statement": r"##\s*1\.\s*待研究问题.*?\n([\s\S]*?)(?=##\s*2\.|\Z)",
                "rationale": r"##\s*2\.\s*解决思路.*?\n([\s\S]*?)(?=##\s*3\.|\Z)",
                "technical_details": r"##\s*3\.\s*必要的技术手段.*?\n([\s\S]*?)(?=##\s*4\.|\Z)",
                "datasets": r"##\s*4\.\s*数据集.*?\n([\s\S]*?)(?=##\s*5\.|\Z)",
                "datasets_source": r"##\s*5\.\s*Source.*?\n([\s\S]*?)(?=##\s*6\.|\Z)",
                "datasets_target": r"##\s*6\.\s*Target.*?\n([\s\S]*?)(?=##\s*7\.|\Z)",
                "methods": r"##\s*9\.\s*方法论.*?\n([\s\S]*?)(?=##\s*10\.|\Z)",
                "experiments": r"##\s*10\.\s*实验设计.*?\n([\s\S]*?)(?=##\s*11\.|\Z)",
                "results": r"##\s*11\.\s*实验结果.*?\n([\s\S]*?)(?=##\s*12\.|\Z)",
            }
            for field, pattern in field_patterns.items():
                m = re.search(pattern, raw_text, re.IGNORECASE)
                data[field] = m.group(1).strip() if m else ""
            ref_match = re.search(r"##\s*12\.\s*参考论文.*?\n([\s\S]*?)$", raw_text, re.IGNORECASE)
            if ref_match:
                lines = [l.strip() for l in ref_match.group(1).split("\n") if l.strip()]
                data["references"] = [re.sub(r"^\d+[\.\)、]\s*", "", l) for l in lines]
            else:
                data["references"] = []
            obj = cls(**data)
            cov = obj.field_coverage()
            logger.info(f"Markdown兜底解析成功: {cov['filled']}/{cov['total']} fields")
            return obj
        except Exception as e:
            logger.warning(f"Markdown兜底解析也失败: {e}", exc_info=True)
            return None

    def to_markdown(self) -> str:
        """渲染为严格对齐赛题12字段编号的Markdown文档"""
        refs = "\n".join(f"{i+1}. {r}" for i, r in enumerate(self.references)) \
               if self.references else "_暂无参考文献_"
        parts = [
            f"# {self.paper_title or '（未生成标题）'}\n",
            f"## 1. 待研究问题（Problem Statement）\n{self.problem_statement or '（未生成）'}\n",
            f"## 2. 解决思路（Rationale）\n{self.rationale or '（未生成）'}\n",
            f"## 3. 必要的技术手段（Technical Details）\n{self.technical_details or '（未生成）'}\n",
            f"## 4. 数据集（Datasets）\n{self.datasets or '（未生成）'}\n",
            f"## 5. Source\n{self.datasets_source or '（未生成）'}\n",
            f"## 6. Target\n{self.datasets_target or '（未生成）'}\n",
            f"## 7. 标题（Paper Title）\n{self.paper_title or '（未生成）'}\n",
            f"## 8. 摘要（Paper Abstract）\n{self.paper_abstract or '（未生成）'}\n",
            f"## 9. 方法论（Methods）\n{self.methods or '（未生成）'}\n",
            f"## 10. 实验设计（Experiments）\n{self.experiments or '（未生成）'}\n",
            f"## 11. 实验结果（Results）\n{self.results or '（未生成）'}\n",
            f"## 12. 参考论文（References）\n{refs}\n",
        ]
        if self.ethics_statement:
            parts.append(f"## 伦理合规声明\n{self.ethics_statement}\n")
        if self.system_architecture:
            parts.append(f"## AI Scientist 系统架构与技术方案\n{self.system_architecture}\n")
        parts.append(
            f"\n---\n*Iteration: v{self.iteration_version} | "
            f"Coverage: {self.field_coverage()['filled']}/{self.field_coverage()['total']} | "
            f"Closure Maturity: {self.closure_maturity:.0f}%*"
        )
        return "\n".join(parts)

    def field_coverage(self) -> dict:
        """返回12+2字段覆盖率统计"""
        core_fields = [
            "paper_title", "paper_abstract", "problem_statement", "rationale",
            "technical_details", "datasets", "datasets_source", "datasets_target",
            "methods", "experiments", "results", "references",
        ]
        ext_fields = ["ethics_statement", "system_architecture"]
        all_fields = core_fields + ext_fields
        filled_core = sum(1 for f in core_fields if getattr(self, f, None))
        filled_ext = sum(1 for f in ext_fields if getattr(self, f, None))
        total = len(all_fields)
        filled = filled_core + filled_ext
        return {
            "filled": filled, "total": total,
            "core_filled": filled_core, "core_total": len(core_fields),
            "rate": filled / total if total > 0 else 0.0,
        }


class BatchRunResult(BaseModel):
    """125题批量运行单题结果"""
    question_id: str = Field(..., description="问题编号，如 Q001")
    question_text: str = Field(..., description="科学问题原文")
    output: ResearchOutput
    status: str = Field("completed", description="completed / failed / skipped")
    error_message: Optional[str] = None
    tokens_used: int = 0
    cost_yuan: float = 0.0
    duration_seconds: float = 0.0
