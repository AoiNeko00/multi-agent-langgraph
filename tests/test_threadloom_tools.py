"""threadloom 도구 테스트."""

from pathlib import Path

from src.tools.threadloom import (
    _read_frontmatter_and_body,
    load_analyses,
    load_pending_actions,
)


def test_read_frontmatter_and_body(tmp_path):
    """frontmatter + body 파싱이 정상 동작하는지 확인한다."""
    md_file = tmp_path / "test.md"
    md_file.write_text(
        "---\ntitle: test\nscore: 0.8\n---\n# 본문\n내용입니다.",
        encoding="utf-8",
    )

    result = _read_frontmatter_and_body(md_file)
    assert "title: test" in result["frontmatter"]
    assert "# 본문" in result["body"]
    assert result["filename"] == "test.md"


def test_read_no_frontmatter(tmp_path):
    """frontmatter 없는 파일도 정상 파싱되는지 확인한다."""
    md_file = tmp_path / "plain.md"
    md_file.write_text("# 제목\n내용", encoding="utf-8")

    result = _read_frontmatter_and_body(md_file)
    assert result["frontmatter"] == ""
    assert "# 제목" in result["body"]


def test_load_analyses_missing_dir(monkeypatch):
    """분석 디렉토리 없을 때 에러 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr(
        "src.tools.threadloom.THREADLOOM_PATH",
        Path("/nonexistent/path"),
    )
    result = load_analyses.invoke({"limit": 3})
    assert "찾을 수 없습니다" in result


def test_load_pending_missing_dir(monkeypatch):
    """pending 디렉토리 없을 때 에러 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr(
        "src.tools.threadloom.THREADLOOM_PATH",
        Path("/nonexistent/path"),
    )
    result = load_pending_actions.invoke({})
    assert "찾을 수 없습니다" in result


def test_load_analyses_with_files(tmp_path, monkeypatch):
    """분석 파일이 있을 때 정상 로드되는지 확인한다."""
    monkeypatch.setattr("src.tools.threadloom.THREADLOOM_PATH", tmp_path)

    analysis_dir = tmp_path / "data" / "analysis"
    analysis_dir.mkdir(parents=True)
    (analysis_dir / "20260312_batch1.md").write_text(
        "---\ntotal: 10\n---\n# Analysis\n테스트 분석",
        encoding="utf-8",
    )

    result = load_analyses.invoke({"limit": 3})
    assert "1개" in result
    assert "테스트 분석" in result
