"""智研星枢 - 提示注入检测与防护（10+模式，中英文）"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    (r"(?i)(ignore|forget|disregard|override)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?|context)", "role_override"),
    (r"(?i)you\s+are\s+now\s+(a|an)\s+", "identity_swap"),
    (r"(?i)act\s+as\s+(a|an)\s+(unrestricted|uncensored|jailbroken)", "uncensored_request"),
    (r"(?i)new\s+(system\s+)?instructions?\s*:", "new_instruction"),
    (r"(?i)system\s*:\s*(you|your)\s+", "system_mimic"),
    (r"(?i)(do\s+anything\s+now|DAN\s+mode|jailbreak|developer\s+mode)", "jailbreak"),
    (r"(?i)(show|reveal|display|print|repeat|output)\s+(your|the|my)\s+(system\s+prompt|instructions?|rules?)", "prompt_leak"),
    (r"(?i)\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>", "separator_inject"),
    (r"忽略(之前|上面|以上|前面|原来)(的|所有)?(指令|提示|规则|设定|限制)", "cn_ignore"),
    (r"你现在(是|扮演|变成|作为|充当)", "cn_identity"),
    (r"新的(指令|设定|规则|提示)\s*[:：]", "cn_new_inst"),
    (r"(显示|输出|告诉我|打印|重复)(你的|系统|原始)(提示|指令|设定|prompt)", "cn_leak"),
    (r"(无视|解除|取消|去除)(所有限制|安全限制|内容过滤|安全策略)", "cn_jailbreak"),
]


class PromptGuard:
    def __init__(self):
        self.patterns = [(re.compile(p, re.IGNORECASE), name) for p, name in INJECTION_PATTERNS]
        self.blocked_count = 0

    def check(self, text: str) -> Tuple[bool, str]:
        if not text:
            return True, ""
        for pattern, name in self.patterns:
            match = pattern.search(text)
            if match:
                self.blocked_count += 1
                reason = f"疑似提示注入 [{name}]: {match.group()[:40]}"
                logger.warning(f"PromptGuard拦截: {reason}")
                return False, reason
        return True, ""

    def sanitize_for_llm(self, text: str) -> str:
        return f"---用户输入开始---\n{text}\n---用户输入结束---"

    def get_stats(self) -> dict:
        return {"blocked_count": self.blocked_count, "pattern_count": len(self.patterns)}


prompt_guard = PromptGuard()
# ===== 科研场景专用防护规则 =====
RESEARCH_GUARD_PATTERNS = [
    r"(?i)(delete|drop|truncate)\s+(table|database|experiment)",  # 防数据破坏
    r"(?i)(rm\s+-rf|format|mkfs)",                               # 防系统命令注入
    r"(?i)(api[_-]?key|secret|password)\s*[:=]",                  # 防凭证泄露
    r"(?i)(eval|exec|__import__)\s*\(",                          # 防代码执行
]

def validate_research_prompt(prompt: str) -> tuple[bool, str]:
    """科研场景专用Prompt校验"""
    import re
    for pattern in RESEARCH_GUARD_PATTERNS:
        if re.search(pattern, prompt):
            return False, f"检测到高风险操作模式，已拦截。请检查输入内容。"
    return True, "OK"
