"""LangGraph 워크플로우 정의.

Planner → Executor → Critic → (조건부 루프) 그래프를 구성한다.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.graph.nodes import (
    critic_node,
    executor_node,
    planner_node,
    should_continue,
)
from src.graph.state import AgentState


def build_workflow() -> StateGraph:
    """멀티에이전트 워크플로우 그래프를 구성한다."""
    workflow = StateGraph(AgentState)

    # 노드 등록
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("critic", critic_node)

    # 엣지(edge) 정의
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "critic")

    # 조건부 엣지(conditional edge): Critic 판정에 따라 분기
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "end": END,
            "planner": "planner",
        },
    )

    return workflow


def create_app():
    """컴파일된 워크플로우 앱을 반환한다."""
    workflow = build_workflow()
    return workflow.compile()
