import re
from typing import Optional

MAX_FIELD_LENGTH = 1024

_html_tag_re = re.compile(r"<[^>]+>")
_script_re = re.compile(r"<\s*script[\s\S]*?>[\s\S]*?<\s*/\s*script\s*>", re.IGNORECASE)


def sanitize_text(value: Optional[str], max_length: int = MAX_FIELD_LENGTH) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    # remove script blocks first
    value = _script_re.sub("", value)
    # strip any remaining tags
    value = _html_tag_re.sub("", value)
    # trim whitespace and limit length
    value = value.strip()
    if len(value) > max_length:
        value = value[:max_length]
    return value


def looks_malicious(value: str) -> bool:
    if not value:
        return False
    patterns = [r"<script", r"onerror=", r"onload=", r"\bselect\b", r"\binsert\b", r"\bdelete\b", r"\bdrop\b"]
    for p in patterns:
        if re.search(p, value, re.IGNORECASE):
            return True
    return False
