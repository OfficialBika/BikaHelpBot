from __future__ import annotations


def chunk_text(text: str, size: int = 3500) -> list[str]:
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    while text:
        parts.append(text[:size])
        text = text[size:]
    return parts
