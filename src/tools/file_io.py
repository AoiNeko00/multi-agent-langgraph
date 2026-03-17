"""파일 입출력(file I/O) 도구.

리포트 저장 및 읽기를 수행한다.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

REPORTS_DIR = Path("data/reports")


def _safe_path(base: Path, filename: str) -> Path:
    """경로 탈출(path traversal)을 방지하는 안전한 경로를 반환한다."""
    filepath = (base / filename).resolve()
    if not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"경로 탈출 시도 감지: {filename}")
    return filepath


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
    try:
        filepath = _safe_path(REPORTS_DIR, filename)
    except ValueError as e:
        return str(e)
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
    try:
        filepath = _safe_path(REPORTS_DIR, filename)
    except ValueError as e:
        return str(e)
    try:
        return filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"파일을 찾을 수 없습니다: {filepath}"
