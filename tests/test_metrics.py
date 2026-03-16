"""성과 지표(metrics) 모듈 테스트."""

import json
import time

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console

from src.metrics import (
    WorkflowMetrics,
    _extract_token_usage,
    create_metrics,
    print_metrics,
    save_metrics,
)


def _make_ai_message(prompt_tokens: int = 100, completion_tokens: int = 50):
    """토큰 사용량(token usage)이 포함된 AI 메시지를 생성한다."""
    return AIMessage(
        content="test response",
        response_metadata={
            "token_usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        },
    )


def _make_final_state(ai_msg_count: int = 2) -> dict:
    """테스트용 최종 상태(final state)를 생성한다."""
    messages = []
    for _ in range(ai_msg_count):
        messages.append(HumanMessage(content="test"))
        messages.append(_make_ai_message(100, 50))

    return {
        "messages": messages,
        "task": "테스트 작업",
        "iteration": 2,
        "report_path": "data/reports/test.md",
    }


def test_extract_token_usage():
    """AI 메시지에서 토큰 사용량을 정확히 추출하는지 확인한다."""
    messages = [
        HumanMessage(content="q1"),
        _make_ai_message(100, 50),
        HumanMessage(content="q2"),
        _make_ai_message(200, 80),
    ]
    usage = _extract_token_usage(messages)

    assert usage["llm_calls"] == 2
    assert usage["input_tokens"] == 300
    assert usage["output_tokens"] == 130
    assert usage["total_tokens"] == 430


def test_extract_token_usage_no_ai_messages():
    """AI 메시지가 없을 때 0을 반환하는지 확인한다."""
    messages = [HumanMessage(content="test")]
    usage = _extract_token_usage(messages)

    assert usage["llm_calls"] == 0
    assert usage["total_tokens"] == 0


def test_create_metrics():
    """create_metrics가 올바른 지표를 생성하는지 확인한다."""
    start = time.time() - 5.0
    metrics = create_metrics(start, _make_final_state(2), "plan")

    assert metrics.mode == "plan"
    assert metrics.llm_calls == 2
    assert metrics.input_tokens == 200
    assert metrics.output_tokens == 100
    assert metrics.total_tokens == 300
    assert metrics.iterations == 2
    assert metrics.duration_seconds >= 4.0


def test_save_metrics_creates_file(tmp_path, monkeypatch):
    """지표가 JSON 파일에 저장되는지 확인한다."""
    metrics_file = tmp_path / "metrics.json"
    monkeypatch.setattr("src.metrics.METRICS_PATH", metrics_file)

    metrics = WorkflowMetrics(
        start_time=1.0, end_time=2.0, duration_seconds=1.0,
        llm_calls=3, input_tokens=500, output_tokens=200,
        total_tokens=700, iterations=1,
        mode="research", task="test", report_path="",
    )
    save_metrics(metrics)

    data = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["mode"] == "research"
    assert data[0]["total_tokens"] == 700


def test_save_metrics_appends(tmp_path, monkeypatch):
    """기존 파일에 지표가 추가(append)되는지 확인한다."""
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("src.metrics.METRICS_PATH", metrics_file)

    metrics = WorkflowMetrics(
        start_time=0, end_time=1, duration_seconds=1.0,
        llm_calls=1, input_tokens=100, output_tokens=50,
        total_tokens=150, iterations=1,
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
        llm_calls=5, input_tokens=1000, output_tokens=500,
        total_tokens=1500, iterations=2,
        mode="enhance", task="demo", report_path="",
    )
    print_metrics(metrics, console)
