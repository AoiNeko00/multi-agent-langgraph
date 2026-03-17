"""도구(tools) 테스트."""

from src.tools.code_analysis import analyze_python_file, analyze_source
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


def test_save_report_path_traversal(tmp_path, monkeypatch):
    """경로 탈출(path traversal) 시도를 차단하는지 확인한다."""
    monkeypatch.setattr("src.tools.file_io.REPORTS_DIR", tmp_path)

    result = save_report.invoke({
        "filename": "../../../tmp/evil.py",
        "content": "malicious",
    })
    assert "경로 탈출" in result


def test_read_report_path_traversal(tmp_path, monkeypatch):
    """읽기 시 경로 탈출(path traversal) 시도를 차단하는지 확인한다."""
    monkeypatch.setattr("src.tools.file_io.REPORTS_DIR", tmp_path)

    result = read_report.invoke({"filename": "../../etc/passwd"})
    assert "경로 탈출" in result


# --- 코드 분석(code analysis) 도구 테스트 ---


SAMPLE_SOURCE = '''\
"""샘플 모듈."""

import os
from pathlib import Path


class MyClass:
    """테스트 클래스."""

    def method(self):
        pass


def short_func():
    """짧은 함수."""
    return 1


def long_func():
    """긴 함수 (20줄 초과 시뮬레이션)."""
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    l = 12
    m = 13
    n = 14
    o = 15
    p = 16
    q = 17
    r = 18
    s = 19
    return s
'''


def test_analyze_source_line_counts():
    """소스 코드 라인 통계를 정확히 세는지 확인한다."""
    result = analyze_source(SAMPLE_SOURCE)
    assert "코드 분석 결과" in result
    assert "클래스 수: 1" in result
    assert "MyClass" in result
    assert "임포트 수: 2" in result


def test_analyze_source_functions():
    """함수(function) 추출 및 복잡도 판별을 확인한다."""
    result = analyze_source(SAMPLE_SOURCE)
    assert "short_func" in result
    assert "long_func" in result
    assert "[복잡]" in result


def test_analyze_python_file_real(tmp_path):
    """실제 파일 분석이 정상 동작하는지 확인한다."""
    py_file = tmp_path / "sample.py"
    py_file.write_text("def hello():\n    pass\n", encoding="utf-8")

    result = analyze_python_file.invoke({"file_path": str(py_file)})
    assert "hello" in result
    assert "함수 수: 1" in result


def test_analyze_python_file_not_found():
    """존재하지 않는 파일에 대해 에러 메시지를 반환하는지 확인한다."""
    result = analyze_python_file.invoke({"file_path": "/없는경로/x.py"})
    assert "찾을 수 없습니다" in result


def test_analyze_python_file_not_python(tmp_path):
    """Python 파일이 아닌 경우 에러 메시지를 반환하는지 확인한다."""
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("hello", encoding="utf-8")

    result = analyze_python_file.invoke({"file_path": str(txt_file)})
    assert "Python 파일이 아닙니다" in result
