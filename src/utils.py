"""공통 유틸리티(utility) 함수."""

from __future__ import annotations

import re


def strip_think_tags(text: str) -> str:
    """Qwen3 /no_think 사용 시 남는 <think> 태그를 제거한다."""
    return re.sub(r"<think>[\s\S]*?</think>\s*", "", text).strip()
