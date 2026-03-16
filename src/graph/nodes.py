"""LangGraph 노드(node) 함수 정의.

각 노드는 AgentState를 받아 부분 상태를 반환한다.
"""

from __future__ import annotations

from src.agents.planner import plan
from src.agents.executor import execute
from src.agents.critic import critique
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


def should_continue(state: AgentState) -> str:
    """Critic 판정에 따라 다음 노드를 결정하는 조건부 엣지(conditional edge)."""
    if state.get("status") == "done":
        return "end"
    return "planner"
