"""快速 / 专家模式的生成策略

单一策略源：集中定义「模式 -> 模型档位 / 内容深度 / 篇幅规模」的映射，
供课件工坊、AI 通识课、课程 AI 大纲三处生成入口复用，避免各写一套、口径不一。

设计原则：
1. 模式只提供「默认」。用户在模型下拉里显式选了模型，以用户为准（不改他的选择）；
2. 两档都必须图文并茂（版式硬约束不下放），差异体现在：模型档位、内容深度指令、
   章节/页数规模、每页/每节篇幅与图解密度。
"""
from typing import Optional

from app.config import settings

QUICK = "quick"
EXPERT = "expert"

# 模式 -> 模型档位（成本优先：默认 quick 走本地免费 DeepSeek，仅 expert 才上云端 qwen-max）
# 注：deepseek-r1:7b 需本机 Ollama 已 pull 且后端重启后才会被路由到本地；未就绪时会回退到云端默认档
MODE_MODEL = {QUICK: "deepseek-r1:7b", EXPERT: "qwen-max"}
# 专家档遇到超长素材时升长上下文模型
LONGCONTEXT_MODEL = "qwen-max-longcontext"

# 注入 system prompt 的深度指令（两档都保留图文并茂，只是密度不同）
DEPTH_DIRECTIVE = {
    QUICK: "【精简档】抓重点、把结论说清楚即可，每个要点 1 句话、少铺细节；"
           "图解 1-2 个够用就好，不要为凑数硬加。整体宁短勿长。",
    EXPERT: "【详尽档】讲透原理、给出真实数据 / 案例 / 反例，结论逐条列出；"
            "图解 2-3 个，把关键机制、对比、流程都画出来，信息密度要高、内容要扎实。",
}

# 通识课规模默认：章节数 / 正文字数区间 / 要点类图解块数 / 单节输出 token
GENERAL = {
    QUICK: {"chapter_count": 4, "content_chars": "500-700", "figures": 1, "max_tokens": 2600},
    EXPERT: {"chapter_count": 8, "content_chars": "900-1200", "figures": 2, "max_tokens": 4200},
}

# 课件工坊规模默认：章节数 / 每章页数 / 每页 detail 字数区间 / 大纲与逐章 token 预算
COURSEWARE = {
    QUICK: {"chapter_count": 4, "slides_per_chapter": 4, "detail": "60-90",
            "outline_tokens": 1400, "chapter_base_tokens": 1200},
    EXPERT: {"chapter_count": 8, "slides_per_chapter": 6, "detail": "120-200",
             "outline_tokens": 1600, "chapter_base_tokens": 1600},
}


def normalize(mode: Optional[str]) -> str:
    """把任意输入收敛成 QUICK / EXPERT，默认快速档（更省、更快、更安全）"""
    return EXPERT if (mode or "").strip().lower() == EXPERT else QUICK


def resolve_model(mode: Optional[str], explicit_model: Optional[str] = None) -> str:
    """模型优先级：用户显式选择 > 模式档位 > settings 默认"""
    m = (explicit_model or "").strip()
    if m:
        return m
    return MODE_MODEL.get(normalize(mode), settings.QWEN_MODEL_NAME)


def apply_mode(mode: Optional[str], explicit_model: Optional[str] = None,
               long_text: str = "") -> dict:
    """返回某次生成要用的完整策略。

    参数：
      mode           前端传来的 'quick' / 'expert'（缺省按 quick）
      explicit_model 用户在下拉里显式选的模型（有则优先，不被模式覆盖）
      long_text      参考资料 / 大纲原文；专家档且超长时升 longcontext

    返回 dict：mode / model / directive / courseware / general
    """
    norm = normalize(mode)
    model = resolve_model(norm, explicit_model)
    if norm == EXPERT and model == MODE_MODEL[EXPERT] and len(long_text or "") > 4000:
        model = LONGCONTEXT_MODEL
    return {
        "mode": norm,
        "model": model,
        "directive": DEPTH_DIRECTIVE[norm],
        "courseware": COURSEWARE[norm],
        "general": GENERAL[norm],
    }
