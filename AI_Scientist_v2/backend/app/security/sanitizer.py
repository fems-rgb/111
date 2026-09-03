"""智研星枢 - 输入净化（XSS/注入防护）"""
import re
import html

DANGEROUS_TAGS = re.compile(
    r'<(script|iframe|object|embed|form|input|button|textarea|select|style|link|meta|base|applet)[^>]*>',
    re.IGNORECASE
)
DANGEROUS_ATTRS = re.compile(r'\s(on\w+|formaction|dynsrc|lowsrc)\s*=', re.IGNORECASE)
JS_PROTOCOL = re.compile(r'(javascript|vbscript|data)\s*:', re.IGNORECASE)


def sanitize_input(text: str, max_length: int = 50000) -> str:
    if not text:
        return ""
    text = text[:max_length]
    text = DANGEROUS_TAGS.sub('', text)
    text = DANGEROUS_ATTRS.sub('', text)
    text = JS_PROTOCOL.sub('', text)
    text = text.replace('\x00', '')
    text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


def sanitize_html(text: str) -> str:
    return html.escape(text) if text else ""


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[/\\:*?"<>|]', '', filename)
    return filename[:200]

# ══════════════════════════════════════
#  文件内容安全扫描
# ══════════════════════════════════════

DANGEROUS_PATTERNS = [
    r'(?i)(system\s*prompt|ignore\s*previous|forget\s*instructions)',
    r'(?i)(sudo|rm\s+-rf|chmod\s+777|eval\s*\(|exec\s*\()',
    r'(?i)(<script|javascript:|on\w+\s*=)',
    r'(?i)(password|secret|api[_-]?key|token)\s*[:=]',
]


def scan_file_content(content: str, filename: str = "") -> tuple[bool, str]:
    """扫描文件内容中的危险模式
    Returns: (is_safe, reason)
    """
    if not content:
        return True, ""

    # 仅扫描前50KB
    sample = content[:50000]

    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, sample)
        if match:
            matched_text = match.group(0)[:50]
            return False, f"文件 {filename} 包含可疑内容: '{matched_text}'"

    return True, ""


# ══════════════════════════════════════
#  文件内容安全扫描
# ══════════════════════════════════════

DANGEROUS_PATTERNS = [
    r'(?i)(system\s*prompt|ignore\s*previous|forget\s*instructions)',
    r'(?i)(sudo|rm\s+-rf|chmod\s+777|eval\s*\(|exec\s*\()',
    r'(?i)(<script|javascript:|on\w+\s*=)',
    r'(?i)(password|secret|api[_-]?key|token)\s*[:=]',
]


def scan_file_content(content: str, filename: str = "") -> tuple[bool, str]:
    """扫描文件内容中的危险模式
    Returns: (is_safe, reason)
    """
    if not content:
        return True, ""

    # 仅扫描前50KB
    sample = content[:50000]

    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, sample)
        if match:
            matched_text = match.group(0)[:50]
            return False, f"文件 {filename} 包含可疑内容: '{matched_text}'"

    return True, ""
