"""threadloom 데이터 로더(loader) 도구.

threadloom 프로젝트의 분석 결과 및 대기 중인 강화 항목을 읽는다.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.tools import tool

# threadloom 프로젝트 경로 (config에서 오버라이드 가능)
THREADLOOM_PATH = Path.home() / "Documents" / "flutter" / "threadloom"


def _read_frontmatter_and_body(filepath: Path) -> dict:
    """YAML frontmatter와 본문을 분리하여 반환한다."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {"frontmatter": "", "body": text, "filename": filepath.name}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": "", "body": text, "filename": filepath.name}

    return {
        "frontmatter": parts[1].strip(),
        "body": parts[2].strip(),
        "filename": filepath.name,
    }


@tool
def load_analyses(limit: int = 3) -> str:
    """threadloom의 최신 분석 결과를 로드한다.

    Args:
        limit: 로드할 최대 파일 수 (기본: 3, 최신순)

    Returns:
        분석 결과 마크다운 문자열
    """
    analysis_dir = THREADLOOM_PATH / "data" / "analysis"
    if not analysis_dir.exists():
        return f"분석 디렉토리를 찾을 수 없습니다: {analysis_dir}"

    files = sorted(analysis_dir.glob("*.md"), reverse=True)[:limit]
    if not files:
        return "분석 파일이 없습니다."

    sections = []
    for f in files:
        parsed = _read_frontmatter_and_body(f)
        # Enhancement Proposal Summary 테이블만 추출하여 토큰 절약
        summary = _extract_summary(parsed["body"])
        sections.append(
            f"### {parsed['filename']}\n"
            f"{parsed['frontmatter']}\n\n"
            f"{summary}"
        )

    return f"## threadloom 분석 결과 ({len(files)}개)\n\n" + "\n\n---\n\n".join(sections)


def _extract_summary(body: str) -> str:
    """분석 본문에서 Enhancement Proposal Summary 섹션을 추출한다."""
    # "Enhancement Proposal Summary" 또는 유사 헤더 이후 내용 추출
    match = re.search(
        r"(##\s*Enhancement Proposal Summary.*?)(?=\n##\s|\Z)",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()[:1500]

    # fallback: 본문 앞부분만 반환
    return body[:800]


@tool
def load_pending_actions() -> str:
    """threadloom의 대기 중인 강화 항목을 로드한다.

    Returns:
        대기 중인 강화 항목 마크다운 문자열
    """
    pending_dir = THREADLOOM_PATH / "data" / "pending"
    if not pending_dir.exists():
        return f"pending 디렉토리를 찾을 수 없습니다: {pending_dir}"

    files = sorted(pending_dir.glob("*.md"))
    if not files:
        return "대기 중인 강화 항목이 없습니다."

    sections = []
    for f in files:
        parsed = _read_frontmatter_and_body(f)
        # frontmatter(메타데이터)만 추출하여 중복 확인용으로 제공
        sections.append(
            f"- **{parsed['filename']}**: {parsed['frontmatter']}"
        )

    return f"## 대기 중인 강화 항목 ({len(files)}개)\n\n" + "\n".join(sections)
