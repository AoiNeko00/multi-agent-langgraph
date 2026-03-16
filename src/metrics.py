"""성과 지표(performance metrics) 모듈.

워크플로우 실행 시간, LLM 호출 수 등을 추적한다.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

METRICS_PATH = Path("data/metrics.json")


@dataclass
class WorkflowMetrics:
    """워크플로우 실행 지표(metrics) 데이터."""

    start_time: float
    end_time: float
    duration_seconds: float
    total_llm_calls: int
    iterations: int
    mode: str
    task: str
    report_path: str


def create_metrics(
    start: float,
    final_state: dict,
    mode: str,
) -> WorkflowMetrics:
    """최종 상태(final state)에서 지표를 생성한다."""
    end = time.time()
    return WorkflowMetrics(
        start_time=start,
        end_time=end,
        duration_seconds=round(end - start, 2),
        total_llm_calls=len(final_state.get("messages", [])),
        iterations=final_state.get("iteration", 0),
        mode=mode,
        task=final_state.get("task", ""),
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
        f"처리 시간: {metrics.duration_seconds}s\n"
        f"LLM 호출: {metrics.total_llm_calls}회\n"
        f"반복 횟수: {metrics.iterations}"
    )
    console.print(Panel(
        content,
        title="성과 지표",
        border_style="cyan",
    ))
