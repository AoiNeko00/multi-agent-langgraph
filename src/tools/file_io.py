"""파일 입출력(file I/O) 도구.

리포트 저장 및 읽기를 수행한다.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

REPORTS_DIR = Path("data/reports")


@tool
def save_report(filename: str, content: str) -> str:
    """리포트를 파일로 저장한다.

    Args:
        filename: 파일명 (확장자 포함)
        content: 저장할 내용

    Returns:
        저장 결과 메시지
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = REPORTS_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return f"리포트 저장 완료: {filepath}"


@tool
def read_report(filename: str) -> str:
    """저장된 리포트를 읽는다.

    Args:
        filename: 파일명

    Returns:
        파일 내용 또는 에러 메시지
    """
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        return f"파일을 찾을 수 없습니다: {filepath}"
    return filepath.read_text(encoding="utf-8")
