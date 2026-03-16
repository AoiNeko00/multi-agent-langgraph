"""리서치 자동화 워크플로우.

검색 → 요약 → 리포트 파이프라인을 LangGraph로 정의한다.

워크플로우:
  [입력] → researcher → reporter → critic → {pass → [출력], fail → researcher}
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.critic import critique
from src.agents.reporter import report
from src.agents.researcher import research
from src.graph.state import AgentState


def researcher_node(state: AgentState) -> dict:
    """Researcher 에이전트 노드."""
    return research(state)


def reporter_node(state: AgentState) -> dict:
    """Reporter 에이전트 노드."""
    return report(state)


def critic_node(state: AgentState) -> dict:
    """Critic 에이전트 노드."""
    return critique(state)


def should_continue(state: AgentState) -> str:
    """Critic 판정에 따라 분기하는 조건부 엣지(conditional edge)."""
    if state.get("status") == "done":
        return "end"
    return "researcher"


def build_research_workflow() -> StateGraph:
    """리서치 자동화 워크플로우 그래프를 구성한다."""
    workflow = StateGraph(AgentState)

    workflow.add_node("researcher", researcher_node)
    workflow.add_node("reporter", reporter_node)
    workflow.add_node("critic", critic_node)

    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "reporter")
    workflow.add_edge("reporter", "critic")

    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "end": END,
            "researcher": "researcher",
        },
    )

    return workflow


def create_research_app():
    """컴파일된 리서치 워크플로우 앱을 반환한다."""
    workflow = build_research_workflow()
    return workflow.compile()
