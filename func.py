import re

def is_emoji_only(s: str) -> bool:
    if not s:
        return False
    text = s.strip()
    return not re.search(r"[A-Za-zА-Яа-я0-9]", text)

def sanitize_text(text: str) -> str:
    return re.sub(r"[*_`#]+", "", text)

def split_message(text: str, max_length: int = 4096) -> list[str]:
    parts = []
    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        parts.append(text)
    return parts

