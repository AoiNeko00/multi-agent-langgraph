"""도구(tools) 고급 테스트 — 코드 분석, 리포트 검색, 중복 방지.

tmp_path 픽스처(fixture)를 사용하여 파일 시스템 격리 환경에서 테스트한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.code_analysis import analyze_python_file
from src.tools.report_history import search_past_reports
from src.tools.threadloom_writer import write_pending_action


# ── a. 코드 분석(code analysis) 도구 ──────────────────────────


def test_code_analysis_tool(tmp_path):
    """Python 파일의 구조 정보(라인 수, 함수명)를 정확히 분석하는지 확인한다."""
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        '"""모듈 독스트링."""\n'
        "\n"
        "# 상수(constant) 정의\n"
        "MAX_COUNT = 10\n"
        "\n"
        "\n"
        "def greet(name: str) -> str:\n"
        '    """인사(greeting) 함수."""\n'
        '    return f"안녕하세요, {name}!"\n'
        "\n"
        "\n"
        "def add(a: int, b: int) -> int:\n"
        '    """덧셈(addition) 함수."""\n'
        "    return a + b\n",
        encoding="utf-8",
    )

    result = analyze_python_file.invoke({"file_path": str(py_file)})

    # 라인 통계(line statistics) 검증
    assert "총 라인: 14" in result
    assert "함수 수: 2" in result
    assert "greet" in result
    assert "add" in result
    assert "주석 라인: 1" in result


def test_code_analysis_nonexistent_file():
    """존재하지 않는 파일에 대해 에러 메시지를 반환하는지 확인한다."""
    result = analyze_python_file.invoke({"file_path": "/nonexistent/file.py"})
    assert "찾을 수 없습니다" in result


def test_code_analysis_non_python_file(tmp_path):
    """Python이 아닌 파일에 대해 에러 메시지를 반환하는지 확인한다."""
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("text content", encoding="utf-8")

    result = analyze_python_file.invoke({"file_path": str(txt_file)})
    assert "Python 파일이 아닙니다" in result


def test_code_analysis_syntax_error(tmp_path):
    """구문 오류(syntax error)가 있는 파일에서 적절한 메시지를 반환하는지 확인한다."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(\n", encoding="utf-8")

    result = analyze_python_file.invoke({"file_path": str(bad_file)})
    assert "구문 오류" in result


# ── b. 리포트 검색(report search) 도구 ────────────────────────


def test_search_past_reports(tmp_path, monkeypatch):
    """키워드(keyword)로 리포트를 검색하여 매칭 결과를 반환하는지 확인한다."""
    monkeypatch.setattr("src.tools.report_history.REPORTS_DIR", tmp_path)

    # 테스트 리포트 파일 생성
    (tmp_path / "langgraph_report_20260315.md").write_text(
        "# LangGraph 분석 리포트\n## 개요\nLangGraph는 멀티에이전트 프레임워크입니다.",
        encoding="utf-8",
    )
    (tmp_path / "flask_report_20260314.md").write_text(
        "# Flask 분석 리포트\n## 개요\nFlask는 웹 프레임워크입니다.",
        encoding="utf-8",
    )
    (tmp_path / "rust_report_20260313.md").write_text(
        "# Rust 분석 리포트\n## 개요\nRust는 시스템 프로그래밍 언어입니다.",
        encoding="utf-8",
    )

    # "LangGraph" 검색
    result = search_past_reports.invoke({"keyword": "LangGraph"})
    assert "검색 결과" in result
    assert "LangGraph" in result

    # "Flask" 검색
    result = search_past_reports.invoke({"keyword": "Flask"})
    assert "Flask" in result

    # 존재하지 않는 키워드 검색
    result = search_past_reports.invoke({"keyword": "존재하지않는키워드"})
    assert "일치하는 리포트가 없습니다" in result


def test_search_past_reports_empty_dir(tmp_path, monkeypatch):
    """빈 디렉토리에서 적절한 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr("src.tools.report_history.REPORTS_DIR", tmp_path)

    result = search_past_reports.invoke({"keyword": "test"})
    assert "저장된 리포트가 없습니다" in result


def test_search_past_reports_no_dir(monkeypatch):
    """디렉토리가 없을 때 적절한 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr(
        "src.tools.report_history.REPORTS_DIR",
        Path("/nonexistent/reports"),
    )

    result = search_past_reports.invoke({"keyword": "test"})
    assert "디렉토리가 없습니다" in result


def test_search_past_reports_max_results(tmp_path, monkeypatch):
    """max_results 파라미터가 결과 수를 제한하는지 확인한다."""
    monkeypatch.setattr("src.tools.report_history.REPORTS_DIR", tmp_path)

    for i in range(5):
        (tmp_path / f"report_{i}.md").write_text(
            f"# 리포트 {i}\n공통 키워드 포함",
            encoding="utf-8",
        )

    result = search_past_reports.invoke({"keyword": "공통", "max_results": 2})
    assert "2건" in result


# ── c. threadloom writer 중복 방지(duplicate prevention) ──────


def test_threadloom_writer_duplicate_prevention(tmp_path, monkeypatch):
    """동일 이름의 파일을 다시 작성 시 '이미 존재' 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr("src.tools.threadloom_writer.THREADLOOM_PATH", tmp_path)

    # pending 디렉토리 생성
    pending_dir = tmp_path / "data" / "pending"
    pending_dir.mkdir(parents=True)

    params = {
        "action_type": "create_skill",
        "name": "code_review",
        "description": "코드 리뷰 자동화",
        "content": "PR diff를 분석하여 리뷰 제공",
    }

    # 첫 번째 작성 — 성공
    result1 = write_pending_action.invoke(params)
    assert "저장 완료" in result1

    # 두 번째 작성 — 중복 방지
    result2 = write_pending_action.invoke(params)
    assert "이미 존재" in result2


def test_threadloom_writer_missing_dir(monkeypatch):
    """pending 디렉토리가 없을 때 에러 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr(
        "src.tools.threadloom_writer.THREADLOOM_PATH",
        Path("/nonexistent/path"),
    )

    result = write_pending_action.invoke({
        "action_type": "add_rule",
        "name": "test_rule",
        "description": "테스트 규칙",
        "content": "내용",
    })
    assert "찾을 수 없습니다" in result


def test_threadloom_writer_creates_frontmatter(tmp_path, monkeypatch):
    """저장된 파일에 YAML frontmatter가 포함되는지 확인한다."""
    monkeypatch.setattr("src.tools.threadloom_writer.THREADLOOM_PATH", tmp_path)

    pending_dir = tmp_path / "data" / "pending"
    pending_dir.mkdir(parents=True)

    write_pending_action.invoke({
        "action_type": "create_agent",
        "name": "security_auditor",
        "description": "보안 감사 에이전트",
        "content": "OWASP Top 10 기반 감사",
    })

    files = list(pending_dir.glob("*.md"))
    assert len(files) == 1

    content = files[0].read_text(encoding="utf-8")
    assert "---" in content
    assert "action_type: create_agent" in content
    assert "source: multi-agent-langgraph" in content
