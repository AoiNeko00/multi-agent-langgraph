"""강화 계획(enhancement planning) 워크플로우.

threadloom 분석 데이터 → 강화 제안 → 실행 계획 → 검증 파이프라인.

워크플로우:
  [threadloom data] → enhancer → planner → critic → {pass → [출력], fail → enhancer}
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.critic import critique
from src.agents.enhancer import enhance
from src.agents.planner import plan
from src.agents.reporter import report
from src.graph.state import AgentState


def enhancer_node(state: AgentState) -> dict:
    """Enhancer 에이전트 노드: threadloom 데이터로 강화 제안 생성."""
    return enhance(state)


def planner_node(state: AgentState) -> dict:
    """Planner 에이전트 노드: 강화 제안을 실행 계획으로 변환.

    enhancer의 result를 plan 입력의 task 컨텍스트로 활용한다.
    """
    # enhancer 결과를 planner의 컨텍스트에 주입
    enhanced_state = {
        **state,
        "task": (
            f"{state['task']}\n\n"
            f"## 강화 제안 (Enhancer 출력)\n{state.get('result', '')}"
        ),
    }
    return plan(enhanced_state)


def reporter_node(state: AgentState) -> dict:
    """Reporter 에이전트 노드: 최종 강화 계획을 리포트로 저장."""
    # 출처 안내(source guidance)를 명시적으로 포함
    report_state = {
        **state,
        "result": (
            f"## 강화 제안\n{state.get('result', '')}\n\n"
            f"## 실행 계획\n{state.get('plan', '')}\n\n"
            f"## 출처 안내\n"
            f"이 데이터는 threadloom 프로젝트의 로컬 분석 파일에서 가져온 것입니다.\n"
            f"외부 URL 출처가 없으므로 출처 섹션을 생략하세요."
        ),
    }
    return report(report_state)


def critic_node(state: AgentState) -> dict:
    """Critic 에이전트 노드."""
    return critique(state)


def should_continue(state: AgentState) -> str:
    """Critic 판정에 따라 분기하는 조건부 엣지(conditional edge)."""
    if state.get("status") == "done":
        return "reporter"
    return "enhancer"


def build_enhance_workflow() -> StateGraph:
    """강화 계획 워크플로우 그래프를 구성한다."""
    workflow = StateGraph(AgentState)

    workflow.add_node("enhancer", enhancer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("reporter", reporter_node)

    workflow.set_entry_point("enhancer")
    workflow.add_edge("enhancer", "planner")
    workflow.add_edge("planner", "critic")

    # Critic 통과 시 reporter로, 실패 시 enhancer로 루프
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "reporter": "reporter",
            "enhancer": "enhancer",
        },
    )

    workflow.add_edge("reporter", END)

    return workflow


def create_enhance_app():
    """컴파일된 강화 계획 워크플로우 앱을 반환한다."""
    workflow = build_enhance_workflow()
    return workflow.compile()
