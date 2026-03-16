"""도구(tools) 테스트."""

from src.tools.file_io import read_report, save_report


def test_save_and_read_report(tmp_path, monkeypatch):
    """리포트 저장 및 읽기가 정상 동작하는지 확인한다."""
    monkeypatch.setattr("src.tools.file_io.REPORTS_DIR", tmp_path)

    result = save_report.invoke({
        "filename": "test.md",
        "content": "# 테스트 리포트",
    })
    assert "저장 완료" in result

    content = read_report.invoke({"filename": "test.md"})
    assert content == "# 테스트 리포트"


def test_read_nonexistent_report(tmp_path, monkeypatch):
    """존재하지 않는 파일 읽기 시 에러 메시지를 반환하는지 확인한다."""
    monkeypatch.setattr("src.tools.file_io.REPORTS_DIR", tmp_path)

    content = read_report.invoke({"filename": "없는파일.md"})
    assert "찾을 수 없습니다" in content
