"""멀티에이전트 오케스트레이터 진입점."""

from __future__ import annotations

import argparse

from src.config import init_config

from src.agents.memory import save_execution
from src.graph.enhance_workflow import create_enhance_app
from src.graph.research_workflow import create_research_app
from src.graph.workflow import create_app


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

    initial_state = {
        "messages": [],
        "task": task,
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "report_path": "",
        "status": "planning",
    }

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
    result = run(args.task, args.max_iterations, args.mode)

    print("\n=== 최종 결과 ===")
    print(f"모드: {args.mode}")
    print(f"상태: {result['status']}")
    print(f"반복 횟수: {result['iteration']}")

    if result.get("plan"):
        print(f"\n계획:\n{result['plan']}")

    print(f"\n결과:\n{result['result']}")

    if result.get("report_path"):
        print(f"\n리포트: {result['report_path']}")

    if result.get("feedback"):
        print(f"\n피드백:\n{result['feedback']}")


if __name__ == "__main__":
    main()
