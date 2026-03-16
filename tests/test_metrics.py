"""성과 지표(metrics) 모듈 테스트."""

import json
import time

from rich.console import Console

from src.metrics import (
    WorkflowMetrics,
    create_metrics,
    print_metrics,
    save_metrics,
)


def _make_final_state(msg_count: int = 4) -> dict:
    """테스트용 최종 상태(final state)를 생성한다."""
    return {
        "messages": [f"msg_{i}" for i in range(msg_count)],
        "task": "테스트 작업",
        "iteration": 2,
        "report_path": "data/reports/test.md",
    }


def test_create_metrics():
    """create_metrics가 올바른 지표를 생성하는지 확인한다."""
    start = time.time() - 5.0
    metrics = create_metrics(start, _make_final_state(), "plan")

    assert metrics.mode == "plan"
    assert metrics.total_llm_calls == 4
    assert metrics.iterations == 2
    assert metrics.duration_seconds >= 4.0
    assert metrics.task == "테스트 작업"


def test_save_metrics_creates_file(tmp_path, monkeypatch):
    """지표가 JSON 파일에 저장되는지 확인한다."""
    metrics_file = tmp_path / "metrics.json"
    monkeypatch.setattr("src.metrics.METRICS_PATH", metrics_file)

    metrics = WorkflowMetrics(
        start_time=1.0,
        end_time=2.0,
        duration_seconds=1.0,
        total_llm_calls=3,
        iterations=1,
        mode="research",
        task="test",
        report_path="",
    )
    save_metrics(metrics)

    data = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["mode"] == "research"


def test_save_metrics_appends(tmp_path, monkeypatch):
    """기존 파일에 지표가 추가(append)되는지 확인한다."""
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("src.metrics.METRICS_PATH", metrics_file)

    metrics = WorkflowMetrics(
        start_time=0, end_time=1, duration_seconds=1.0,
        total_llm_calls=1, iterations=1,
        mode="plan", task="t", report_path="",
    )
    save_metrics(metrics)
    save_metrics(metrics)

    data = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert len(data) == 2


def test_print_metrics_no_error():
    """print_metrics가 예외 없이 실행되는지 확인한다."""
    console = Console(file=None, force_terminal=False)
    metrics = WorkflowMetrics(
        start_time=0, end_time=1, duration_seconds=1.23,
        total_llm_calls=5, iterations=2,
        mode="enhance", task="demo", report_path="",
    )
    # 예외(exception)가 발생하지 않으면 통과
    print_metrics(metrics, console)
