"""멀티에이전트 오케스트레이터 진입점."""

from __future__ import annotations

import argparse
import time
import uuid

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.config import init_config

from src.agents.memory import save_execution
from src.metrics import create_metrics, print_metrics, save_metrics
from src.graph.enhance_workflow import create_enhance_app
from src.graph.research_workflow import create_research_app
from src.graph.workflow import create_app
from src.tools.threadloom import load_project_summary

console = Console()

MODE_LABELS = {
    "plan": "[blue]Plan[/blue]",
    "research": "[green]Research[/green]",
    "enhance": "[magenta]Enhance[/magenta]",
}


def _build_initial_state(task: str, max_iterations: int, context: str) -> dict:
    """워크플로우 초기 상태를 생성한다."""
    return {
        "messages": [],
        "task": task,
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "context": context,
        "report_path": "",
        "status": "planning",
    }


def _load_context(task: str) -> str:
    """threadloom 관련 작업이면 프로젝트 컨텍스트(context)를 로드한다."""
    threadloom_keywords = ["threadloom", "4-phase", "4phase", "자기강화"]
    if any(kw in task.lower() for kw in threadloom_keywords):
        console.print("[dim]threadloom 컨텍스트 주입됨[/dim]")
        return load_project_summary()
    return ""


def run(task: str, max_iterations: int = 3, mode: str = "plan") -> dict:
    """워크플로우를 실행하고 최종 상태를 반환한다.

    Args:
        task: 실행할 작업 설명
        max_iterations: 최대 반복 횟수
        mode: 워크플로우 모드 ("plan", "research", "enhance")
    """
    apps = {
        "research": create_research_app,
        "enhance": create_enhance_app,
    }
    app = apps.get(mode, create_app)()

    context = _load_context(task)
    initial_state = _build_initial_state(task, max_iterations, context)

    label = MODE_LABELS.get(mode, mode)
    console.print(f"\n{label} 모드 실행 중...", style="bold")

    # 실행 시간(timing) 측정 시작
    start = time.time()
    final_state = app.invoke(initial_state)

    # 성과 지표(metrics) 수집 및 저장
    metrics = create_metrics(start, final_state, mode)
    save_metrics(metrics)
    print_metrics(metrics, console)

    save_execution(
        task=final_state["task"],
        plan=final_state.get("plan", ""),
        result=final_state["result"],
        iterations=final_state["iteration"],
    )

    return final_state


def run_with_approval(task: str, max_iterations: int = 3) -> dict:
    """Human-in-the-loop(HITL) 승인 모드로 enhance 워크플로우를 실행한다.

    applier 노드에서 interrupt가 발생하면 사용자에게 승인을 요청한다.
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    checkpointer = MemorySaver()
    app = create_enhance_app(checkpointer=checkpointer)

    context = _load_context(task)
    initial_state = _build_initial_state(task, max_iterations, context)

    thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    console.print(
        "\n[magenta]Enhance[/magenta] 모드 (승인 필요) 실행 중...",
        style="bold",
    )

    # 첫 실행 — applier에서 interrupt 발생 가능
    start = time.time()
    final_state = app.invoke(initial_state, config=thread_config)

    # interrupt 상태 확인(interrupt check)
    graph_state = app.get_state(thread_config)
    if graph_state.next:
        interrupt_data = graph_state.tasks[0].interrupts[0].value
        console.print(Panel(
            f"적용 대상 파일 ({interrupt_data['count']}개):\n"
            f"{interrupt_data['files_to_create']}",
            title="승인 요청",
            border_style="yellow",
        ))

        answer = input("적용하시겠습니까? (y/n): ").strip().lower()
        final_state = app.invoke(
            Command(resume=(answer == "y")),
            config=thread_config,
        )

    # 성과 지표(metrics) 수집 및 저장
    metrics = create_metrics(start, final_state, "enhance")
    save_metrics(metrics)
    print_metrics(metrics, console)

    save_execution(
        task=final_state["task"],
        plan=final_state.get("plan", ""),
        result=final_state["result"],
        iterations=final_state["iteration"],
    )

    return final_state


def main() -> None:
    """CLI 진입점."""
    init_config()

    parser = argparse.ArgumentParser(
        description="멀티에이전트 오케스트레이터",
    )
    parser.add_argument("task", help="실행할 작업 설명")
    parser.add_argument(
        "--mode",
        choices=["plan", "research", "enhance"],
        default="plan",
        help="워크플로우 모드 (기본: plan)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="최대 반복 횟수 (기본: 3)",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="enhance 모드에서 적용 전 승인 요청 (Human-in-the-loop)",
    )

    args = parser.parse_args()

    # --approve 플래그(flag)는 enhance 모드에서만 유효
    if args.approve and args.mode == "enhance":
        result = run_with_approval(args.task, args.max_iterations)
    else:
        with console.status("[bold]에이전트 실행 중..."):
            result = run(args.task, args.max_iterations, args.mode)

    # 결과 출력
    label = MODE_LABELS.get(args.mode, args.mode)
    console.print(Panel(
        f"모드: {label}\n"
        f"상태: [green]{result['status']}[/green]\n"
        f"반복 횟수: {result['iteration']}",
        title="실행 완료",
        border_style="green",
    ))

    if result.get("report_path"):
        console.print(f"\n[bold]리포트:[/bold] {result['report_path']}")

    if result.get("feedback"):
        console.print(Panel(
            result["feedback"][:500],
            title="Critic 피드백",
            border_style="yellow",
        ))


if __name__ == "__main__":
    main()
