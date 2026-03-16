"""성과 지표(performance metrics) 모듈.

워크플로우 실행 시간, 토큰 사용량, LLM 호출 수를 추적한다.
Groq API response의 usage 데이터를 기반으로 실제 토큰 수를 측정한다.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from langchain_core.messages import AIMessage
from rich.console import Console
from rich.panel import Panel

METRICS_PATH = Path("data/metrics.json")


@dataclass
class WorkflowMetrics:
    """워크플로우 실행 지표(metrics) 데이터."""

    start_time: float
    end_time: float
    duration_seconds: float
    llm_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    iterations: int
    mode: str
    task: str
    report_path: str


def _extract_token_usage(messages: list) -> dict:
    """AI 메시지에서 토큰 사용량(token usage)을 추출한다.

    Groq API 응답의 response_metadata.token_usage에서
    실제 입력/출력 토큰 수를 가져온다.
    """
    llm_calls = 0
    input_tokens = 0
    output_tokens = 0

    for msg in messages:
        if not isinstance(msg, AIMessage):
            continue
        llm_calls += 1
        usage = getattr(msg, "response_metadata", {}).get("token_usage", {})
        input_tokens += usage.get("prompt_tokens", 0)
        output_tokens += usage.get("completion_tokens", 0)

    return {
        "llm_calls": llm_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def create_metrics(
    start: float,
    final_state: dict,
    mode: str,
) -> WorkflowMetrics:
    """최종 상태(final state)에서 지표를 생성한다."""
    end = time.time()
    usage = _extract_token_usage(final_state.get("messages", []))

    return WorkflowMetrics(
        start_time=start,
        end_time=end,
        duration_seconds=round(end - start, 2),
        llm_calls=usage["llm_calls"],
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        iterations=final_state.get("iteration", 0),
        mode=mode,
        task=final_state.get("task", "")[:100],
        report_path=final_state.get("report_path", ""),
    )


def save_metrics(metrics: WorkflowMetrics) -> None:
    """지표를 JSON 파일에 추가(append) 저장한다."""
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    history: list[dict] = []
    if METRICS_PATH.exists():
        try:
            history = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            history = []

    history.append(asdict(metrics))
    METRICS_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def print_metrics(metrics: WorkflowMetrics, console: Console) -> None:
    """지표를 rich 패널(panel)로 출력한다."""
    content = (
        f"처리 시간: {metrics.duration_seconds}초\n"
        f"LLM 호출: {metrics.llm_calls}회\n"
        f"토큰: {metrics.input_tokens:,} 입력 + "
        f"{metrics.output_tokens:,} 출력 = "
        f"{metrics.total_tokens:,} 총\n"
        f"반복 횟수: {metrics.iterations}"
    )
    console.print(Panel(
        content,
        title="성과 지표",
        border_style="cyan",
    ))
