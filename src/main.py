"""멀티에이전트 오케스트레이터 진입점."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.config import init_config

from src.agents.memory import save_execution
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

    # threadloom 관련 작업이면 프로젝트 컨텍스트(context) 자동 주입
    context = ""
    threadloom_keywords = ["threadloom", "4-phase", "4phase", "자기강화"]
    if any(kw in task.lower() for kw in threadloom_keywords):
        context = load_project_summary()
        console.print("[dim]threadloom 컨텍스트 주입됨[/dim]")

    initial_state = {
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

    label = MODE_LABELS.get(mode, mode)
    console.print(f"\n{label} 모드 실행 중...", style="bold")

    final_state = app.invoke(initial_state)

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

    args = parser.parse_args()

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
