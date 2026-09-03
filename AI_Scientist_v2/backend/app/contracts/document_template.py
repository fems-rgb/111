"""智研星瀚 - 文档模板契约（通用多模态文档生成）"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class SectionType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CODE = "code"
    REFERENCE = "reference"
    MIXED = "mixed"


class EvidenceStrength(str, Enum):
    EMPIRICAL = "empirical"       # ✅ 实证支持
    THEORETICAL = "theoretical"   # 📐 理论推导
    INFERENCE = "inference"       # ⚠️ 合理推断
    PENDING = "pending"           # 🔲 待补充


class SectionSpec(BaseModel):
    """单个章节规格"""
    section_id: str = Field(description="章节唯一标识，如 'problem_statement'")
    title_cn: str = Field(description="中文标题")
    title_en: str = Field(description="英文标题")
    section_type: SectionType = Field(default=SectionType.MIXED)
    min_words: int = Field(default=300, description="最小字数")
    max_words: int = Field(default=2000, description="最大字数")
    required_elements: List[str] = Field(default_factory=list, description="必须包含的元素列表")
    depends_on: List[str] = Field(default_factory=list, description="依赖的前序章节ID")
    multimodal_hints: List[str] = Field(default_factory=list, description="多模态生成提示，如 'mermaid_flowchart', 'latex_equation', 'data_table'")
    quality_criteria: List[str] = Field(default_factory=list, description="该章节的质量评判标准")
    template_instructions: str = Field(default="", description="该章节的详细写作指导")


class DocumentTemplate(BaseModel):
    """文档模板定义"""
    template_id: str = Field(description="模板ID，如 'nh_202619_track1'")
    template_name: str = Field(description="模板名称")
    description: str = Field(default="")
    total_min_words: int = Field(default=6000)
    total_max_words: int = Field(default=15000)
    sections: List[SectionSpec] = Field(description="有序章节列表")
    global_quality_rules: List[str] = Field(default_factory=list, description="全局质量红线")
    output_format: str = Field(default="markdown", description="输出格式: markdown / latex / html")
    citation_style: str = Field(default="APA", description="引用格式")
    language: str = Field(default="zh-CN", description="主语言")
    requires_bilingual: bool = Field(default=False, description="是否需要中英双语")


class QualityScore(BaseModel):
    """单章节质量评分"""
    section_id: str
    completeness: float = Field(ge=0, le=10, description="完整性")
    rigor: float = Field(ge=0, le=10, description="严谨性")
    clarity: float = Field(ge=0, le=10, description="清晰度")
    multimodal_richness: float = Field(ge=0, le=10, description="多模态丰富度")
    evidence_quality: float = Field(ge=0, le=10, description="证据质量")
    overall: float = Field(ge=0, le=10, description="综合分")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="修改建议")


class DocumentQualityReport(BaseModel):
    """整篇文档质量报告"""
    section_scores: List[QualityScore]
    overall_score: float
    passed: bool
    revision_priority: List[str] = Field(description="需要优先修订的章节ID列表")
    global_issues: List[str] = Field(default_factory=list)
    iteration: int = 1


# ===== 预置模板：NH-202619 赛道一 12字段 =====
NH_202619_TRACK1_TEMPLATE = DocumentTemplate(
    template_id="nh_202619_track1",
    template_name="科学假设与研究计划（12标准化字段）",
    description="XH-202619 赛道一·科学发现·方向1A 专用模板",
    total_min_words=8000,
    total_max_words=15000,
    requires_bilingual=True,
    citation_style="APA",
    global_quality_rules=[
        "必须且只能使用模板定义的章节标题，不得增减或改名",
        "总字数8000-15000字，低于6000字视为严重不达标",
        "每个章节必须有实质内容，禁止空章节或一句话带过",
        "所有假设必须可检验可证伪，禁止模糊表述",
        "参考文献严禁虚构，不确定标[需核实]",
        "严格区分✅实证/📐理论/⚠️推断三类证据",
        "信息不足标[待补充]而非编造数据",
        "统计表述必须具体（系数方向/显著性水平/效应量/置信区间）",
        "禁止期刊论文结构（引言/文献综述/讨论/结论等）",
    ],
    sections=[
        SectionSpec(
            section_id="problem_statement", title_cn="待研究问题", title_en="Problem Statement",
            section_type=SectionType.TEXT, min_words=800, max_words=1200,
            required_elements=["核心科学问题", "学科背景", "当前局限性≥3点", "可操作的待研究问题"],
            multimodal_hints=["mermaid_problem_tree"],
            quality_criteria=["问题陈述是否清晰具体", "局限性是否有文献支撑", "是否转化为可操作问题"],
            template_instructions="第一段(200-300字)直接陈述核心科学问题；第二段(200-300字)阐述学科背景与重要性；第三段(150-250字)指出当前研究具体局限性(至少3点)；第四段(100-200字)将局限性转化为可操作的待研究问题。"
        ),
        SectionSpec(
            section_id="rationale", title_cn="解决思路", title_en="Rationale",
            section_type=SectionType.MIXED, min_words=800, max_words=1200,
            required_elements=["逻辑推导链", "创新点≥2项", "突破点说明", "概念模型描述"],
            depends_on=["problem_statement"],
            multimodal_hints=["mermaid_conceptual_model"],
            quality_criteria=["逻辑链是否完整", "创新点是否有区分度", "概念模型是否清晰"],
            template_instructions="从'已知事实'到'知识缺口'再到'解决路径'的完整逻辑链。明确阐述创新点(理论/方法/数据，至少2项)。包含概念模型或理论框架的文字描述。"
        ),
        SectionSpec(
            section_id="technical_details", title_cn="必要的技术手段", title_en="Technical Details",
            section_type=SectionType.TABLE, min_words=800, max_words=1500,
            required_elements=["统计方法+公式", "ML/DL方法", "数据处理技术", "软件工具链+版本号", "计算资源需求"],
            depends_on=["rationale"],
            multimodal_hints=["data_table", "latex_equation"],
            quality_criteria=["技术选型是否有依据", "公式是否正确", "工具版本是否真实"],
            template_instructions="以表格形式呈现技术栈，附文字说明选择理由。包含具体模型名称、公式、适用条件。"
        ),
        SectionSpec(
            section_id="datasets", title_cn="数据集", title_en="Datasets",
            section_type=SectionType.TABLE, min_words=600, max_words=1000,
            required_elements=["数据集名称+来源", "样本量+时间范围", "关键字段说明", "数据质量评估", "伦理合规声明"],
            multimodal_hints=["data_table"],
            quality_criteria=["数据集是否真实存在", "字段说明是否完整", "合规声明是否充分"],
            template_instructions="以表格形式呈现。确保数据集来源合规真实。"
        ),
        SectionSpec(
            section_id="source", title_cn="Source", title_en="Source",
            section_type=SectionType.TABLE, min_words=600, max_words=1000,
            required_elements=["每条假设的证据来源", "已发表文献(作者/年份/核心发现)", "证据强度标注"],
            depends_on=["rationale"],
            multimodal_hints=["evidence_table"],
            quality_criteria=["每条假设≥2-3个Source", "证据强度标注是否正确", "文献是否真实"],
            template_instructions="以结构化列表呈现。区分✅实证支持/📐理论推导/⚠️合理推断。"
        ),
        SectionSpec(
            section_id="target", title_cn="Target", title_en="Target",
            section_type=SectionType.TABLE, min_words=600, max_words=1000,
            required_elements=["新数据采集方案", "数据加工方案", "预期数据特征", "统计功效分析"],
            depends_on=["source"],
            multimodal_hints=["data_table"],
            quality_criteria=["采集方案是否可行", "样本量是否满足功效要求"],
            template_instructions="以表格形式呈现，按假设编号对应。"
        ),
        SectionSpec(
            section_id="paper_title", title_cn="标题", title_en="Paper Title",
            section_type=SectionType.TEXT, min_words=100, max_words=200,
            required_elements=["中文标题(20-30字)", "英文标题"],
            quality_criteria=["标题是否准确反映研究内容", "是否包含核心变量关系"],
            template_instructions="中文标题20-30字，准确反映研究内容、方法、对象。英文标题与中文对应。"
        ),
        SectionSpec(
            section_id="paper_abstract", title_cn="摘要", title_en="Paper Abstract",
            section_type=SectionType.TEXT, min_words=600, max_words=1000,
            required_elements=["背景", "目的", "方法", "预期结果", "意义", "关键词3-5个"],
            quality_criteria=["结构化摘要是否完整", "中英双语是否齐全"],
            template_instructions="结构化摘要：【背景】【目的】【方法】【预期结果】【意义】。中英文双语摘要+关键词。"
        ),
        SectionSpec(
            section_id="methods", title_cn="方法论", title_en="Methods",
            section_type=SectionType.MIXED, min_words=1500, max_words=2500,
            required_elements=["研究设计类型", "变量操作化定义表", "计量模型设定(完整方程)", "识别策略", "稳健性检验≥3种", "分析流程图"],
            depends_on=["technical_details", "datasets"],
            multimodal_hints=["latex_equation", "mermaid_flowchart", "data_table"],
            quality_criteria=["模型方程是否完整", "识别策略是否有效", "稳健性检验是否充分"],
            template_instructions="最核心技术字段，必须详尽。包含完整回归方程(含所有下标和参数说明)、变量操作化定义表、识别策略、稳健性检验方案。"
        ),
        SectionSpec(
            section_id="experiments", title_cn="实验设计", title_en="Experiments",
            section_type=SectionType.TABLE, min_words=1000, max_words=1800,
            required_elements=["主实验设计", "基线模型≥2个", "评估指标+判定阈值", "统计功效分析", "多重比较校正"],
            depends_on=["methods"],
            multimodal_hints=["data_table", "latex_equation"],
            quality_criteria=["基线选择是否合理", "指标是否全面", "功效分析是否充分"],
            template_instructions="以表格形式呈现基线对比和评估指标。包含R²、调整R²、AIC/BIC、p值、效应量等。"
        ),
        SectionSpec(
            section_id="results", title_cn="实验结果", title_en="Results",
            section_type=SectionType.MIXED, min_words=1500, max_words=2500,
            required_elements=["描述性统计", "主回归结果", "假设验证结论(逐条)", "稳健性检验汇总", "结果可视化描述", "异常发现讨论"],
            depends_on=["experiments"],
            multimodal_hints=["data_table", "mermaid_chart", "latex_equation"],
            quality_criteria=["结果是否与假设对应", "统计表述是否具体", "异常发现是否有讨论"],
            template_instructions="逐条对照H1-Hn给出支持/削弱/否定及统计依据。如尚未实际执行，提供预期结果的公式推导和模拟分析。"
        ),
        SectionSpec(
            section_id="references", title_cn="参考论文", title_en="References",
            section_type=SectionType.REFERENCE, min_words=800, max_words=1500,
            required_elements=["APA/GB-T7714格式", "作者/年份/标题/期刊/DOI", "引用位置标注", "≥15篇且近5年≥50%"],
            quality_criteria=["文献是否真实", "格式是否规范", "数量是否达标"],
            template_instructions="严禁虚构！不确定标[需核实]。仅列出正文中实际引用的文献。标注每条文献在哪个字段中被引用。"
        ),
    ]
)

# 模板注册表
TEMPLATE_REGISTRY: Dict[str, DocumentTemplate] = {
    "nh_202619_track1": NH_202619_TRACK1_TEMPLATE,
}


def get_template(template_id: str) -> DocumentTemplate:
    if template_id not in TEMPLATE_REGISTRY:
        raise ValueError(f"未知模板: {template_id}，可用: {list(TEMPLATE_REGISTRY.keys())}")
    return TEMPLATE_REGISTRY[template_id]


def list_templates() -> list[dict]:
    """返回所有已注册模板的摘要列表"""
    return [
        {
            'template_id': tid,
            'template_name': tpl.template_name,
            'description': tpl.description,
            'total_min_words': tpl.total_min_words,
            'total_max_words': tpl.total_max_words,
            'section_count': len(tpl.sections),
        }
        for tid, tpl in TEMPLATE_REGISTRY.items()
    ]
