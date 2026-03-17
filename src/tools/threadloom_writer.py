"""threadloom 강화 항목 작성(writer) 도구.

enhance 모드에서 생성된 강화 제안을 threadloom의 data/pending/에 저장한다.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool

from src.tools.threadloom import THREADLOOM_PATH


def _slugify(text: str) -> str:
    """텍스트를 파일명용 slug로 변환한다."""
    slug = re.sub(r"[^\w]", "_", text.lower())
    return re.sub(r"_+", "_", slug).strip("_")[:50]


@tool
def write_pending_action(
    action_type: str,
    name: str,
    description: str,
    content: str,
) -> str:
    """threadloom의 data/pending/에 강화 항목을 마크다운 파일로 저장한다.

    Args:
        action_type: 강화 유형 (create_skill, create_agent, add_rule)
        name: 강화 항목 이름 (snake_case)
        description: 간단한 설명
        content: 마크다운 본문

    Returns:
        저장 결과 메시지
    """
    pending_dir = THREADLOOM_PATH / "data" / "pending"
    if not pending_dir.exists():
        return f"pending 디렉토리를 찾을 수 없습니다: {pending_dir}"

    slug = _slugify(name)
    filename = f"{action_type}_{slug}.md"
    filepath = pending_dir / filename

    # 이미 존재하면 덮어쓰지 않음(overwrite prevention) — 명시적 경고
    if filepath.exists():
        return f"[건너뜀] 이미 존재하는 파일입니다 (중복 방지): {filepath}"

    # YAML frontmatter + 본문 구성
    now = datetime.now().strftime("%Y-%m-%d")
    md_content = (
        f"---\n"
        f"action_type: {action_type}\n"
        f"name: {slug}\n"
        f"description: {description}\n"
        f"source: multi-agent-langgraph\n"
        f"created: {now}\n"
        f"---\n\n"
        f"# {name}\n\n"
        f"{content}\n"
    )

    filepath.write_text(md_content, encoding="utf-8")
    return f"강화 항목 저장 완료: {filepath}"
