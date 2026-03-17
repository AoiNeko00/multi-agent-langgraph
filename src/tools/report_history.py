"""리포트 이력 검색(report history search) 도구.

이전에 생성된 리포트를 키워드 기반으로 검색하여
에이전트가 과거 결과물을 참조할 수 있게 한다.
간이 RAG(Retrieval-Augmented Generation) 구현.
"""

from __future__ import annotations

from langchain_core.tools import tool

from src.tools.file_io import REPORTS_DIR


@tool
def search_past_reports(keyword: str, max_results: int = 3) -> str:
    """이전 리포트에서 키워드를 검색하여 관련 내용을 반환한다.

    Args:
        keyword: 검색할 키워드
        max_results: 최대 결과 수 (기본: 3)

    Returns:
        매칭된 리포트의 요약 문자열
    """
    if not REPORTS_DIR.exists():
        return "리포트 디렉토리가 없습니다."

    files = sorted(REPORTS_DIR.glob("*.md"), reverse=True)
    if not files:
        return "저장된 리포트가 없습니다."

    matches = []
    keyword_lower = keyword.lower()

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        if keyword_lower in content.lower():
            summary = content[:500].strip()
            matches.append(f"### {f.name}\n{summary}...")

        if len(matches) >= max_results:
            break

    if not matches:
        return f"'{keyword}' 키워드와 일치하는 리포트가 없습니다."

    return f"## 과거 리포트 검색 결과 ({len(matches)}건)\n\n" + "\n\n---\n\n".join(matches)


def get_recent_reports(limit: int = 3) -> str:
    """최근 생성된 리포트 목록을 반환한다."""
    if not REPORTS_DIR.exists():
        return ""

    files = sorted(REPORTS_DIR.glob("*.md"), reverse=True)[:limit]
    if not files:
        return ""

    lines = [f"## 최근 리포트 ({len(files)}건)"]
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        overview = _extract_overview(content)
        lines.append(f"- **{f.name}**: {overview}")

    return "\n".join(lines)


def _extract_overview(content: str) -> str:
    """리포트에서 개요 섹션의 첫 문장을 추출한다."""
    for line in content.split("\n"):
        line = line.strip()
        # 빈 줄, 헤더, think 태그 건너뛰기
        if not line or line.startswith("#") or line.startswith("<"):
            continue
        return line[:150]
    return "(개요 없음)"
