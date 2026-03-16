"""LangGraph 워크플로우 정의.

Planner → Executor → Critic → (조건부 루프) → Reporter 그래프를 구성한다.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.critic import critique
from src.agents.executor import execute
from src.agents.planner import plan
from src.agents.reporter import report
from src.graph.state import AgentState


def planner_node(state: AgentState) -> dict:
    """Planner 에이전트 노드."""
    return plan(state)


def executor_node(state: AgentState) -> dict:
    """Executor 에이전트 노드."""
    return execute(state)


def critic_node(state: AgentState) -> dict:
    """Critic 에이전트 노드."""
    return critique(state)


def reporter_node(state: AgentState) -> dict:
    """Reporter 에이전트 노드: 계획 + 실행 결과를 리포트로 저장."""
    report_state = {
        **state,
        "result": (
            f"## 실행 계획\n{state.get('plan', '')}\n\n"
            f"## 실행 결과\n{state.get('result', '')}"
        ),
    }
    return report(report_state)


def should_continue(state: AgentState) -> str:
    """Critic 판정에 따라 다음 노드를 결정하는 조건부 엣지(conditional edge)."""
    if state.get("status") == "done":
        return "reporter"
    return "planner"


def build_workflow() -> StateGraph:
    """멀티에이전트 워크플로우 그래프를 구성한다."""
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("reporter", reporter_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "critic")

    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "reporter": "reporter",
            "planner": "planner",
        },
    )

    workflow.add_edge("reporter", END)

    return workflow


def create_app():
    """컴파일된 워크플로우 앱을 반환한다."""
    workflow = build_workflow()
    return workflow.compile()
