"""강화 계획(enhancement planning) 워크플로우.

threadloom 분석 데이터 → 강화 제안 → 실행 계획 → 검증 → 리포트 → 적용.

워크플로우:
  [threadloom data] → enhancer → planner → critic
    → {pass → reporter → applier → END, fail → enhancer}
"""

from __future__ import annotations

import re

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from src.agents.critic import critique
from src.agents.enhancer import enhance
from src.agents.planner import plan
from src.agents.reporter import report
from src.graph.state import AgentState
from src.tools.threadloom_writer import write_pending_action


def enhancer_node(state: AgentState) -> dict:
    """Enhancer 에이전트 노드: threadloom 데이터로 강화 제안 생성."""
    return enhance(state)


def planner_node(state: AgentState) -> dict:
    """Planner 에이전트 노드: 강화 제안을 실행 계획으로 변환."""
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


def _has_checkpointer() -> bool:
    """현재 실행 중인 그래프에 체크포인터(checkpointer)가 있는지 확인한다."""
    from langgraph.config import get_config

    cfg = get_config()
    configurable = cfg.get("configurable", {})
    return configurable.get("__pregel_checkpointer") is not None


def applier_node(state: AgentState) -> dict:
    """Applier 노드: 강화 제안을 threadloom data/pending/에 저장한다.

    Human-in-the-loop(HITL) 모드에서는 적용 전 interrupt로 승인을 요청한다.
    """
    result = state.get("result", "")
    proposals = _parse_proposals(result)

    if not proposals:
        return {
            "result": f"{result}\n\n## 적용 결과\n적용할 강화 항목이 없습니다.",
            "status": "done",
        }

    # 체크포인터(checkpointer) 유무로 HITL 모드 판별
    if _has_checkpointer():
        file_list = "\n".join(
            f"  - {p['action_type']}: {p['name']}" for p in proposals
        )
        interrupt({"files_to_create": file_list, "count": len(proposals)})

    # interrupt 통과 후 실제 적용(apply)
    applied = _apply_proposals(proposals)
    applied_summary = "\n".join(applied)

    return {
        "result": f"{result}\n\n## 적용 결과\n{applied_summary}",
        "status": "done",
    }


def _apply_proposals(proposals: list[dict]) -> list[str]:
    """파싱된 제안 목록을 pending 파일로 저장한다."""
    applied = []
    for prop in proposals:
        msg = write_pending_action.invoke(prop)
        applied.append(msg)
    return applied


_TYPE_MAP = {
    "skill": "create_skill",
    "agent": "create_agent",
    "rule": "add_rule",
    "reasoning_rule": "add_rule",
}
_VALID_TYPES = set(_TYPE_MAP)


def _parse_proposals(text: str) -> list[dict]:
    """강화 제안 텍스트에서 개별 제안을 파싱한다.

    유효한 유형(skill/agent/rule)만 추출하고,
    출처/비교 등 무관한 섹션은 무시한다.
    """
    proposals = []

    # 다양한 형식 지원(format support):
    #   "### 제안 1: skill — name"
    #   "### 1. skill — name"
    #   "### 제안 1: **skill** — **name**"
    pattern = re.compile(
        r"###?\s*(?:제안\s*)?\d+[.:]\s*"
        r"[*`]*(\w+)[*`]*\s*[-—]+\s*[*`]*([^\n*`]+)[*`]*",
    )

    matches = pattern.findall(text)
    for action_type_raw, name_raw in matches:
        action_type_raw = action_type_raw.strip().lower()
        name_raw = name_raw.strip().strip("`").strip("*")

        # 유효한 유형만 통과(validation)
        if action_type_raw not in _VALID_TYPES:
            continue

        action_type = _TYPE_MAP[action_type_raw]

        # 해당 제안의 본문 추출 (다음 제안 또는 ## 섹션까지)
        name_escaped = re.escape(name_raw)
        body_match = re.search(
            rf"{name_escaped}[*`]*\n(.*?)(?=(?:###?\s*(?:제안\s*)?\d|##\s)|\Z)",
            text,
            re.DOTALL,
        )
        body = body_match.group(1).strip()[:2000] if body_match else ""

        proposals.append({
            "action_type": action_type,
            "name": name_raw,
            "description": name_raw[:100],
            "content": body,
        })

    return proposals[:5]


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
    workflow.add_node("applier", applier_node)

    workflow.set_entry_point("enhancer")
    workflow.add_edge("enhancer", "planner")
    workflow.add_edge("planner", "critic")

    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "reporter": "applier",
            "enhancer": "enhancer",
        },
    )

    # Critic 통과 → applier (원본 제안 파싱) → reporter (리포트 저장)
    workflow.add_edge("applier", "reporter")
    workflow.add_edge("reporter", END)

    return workflow


def create_enhance_app(checkpointer=None):
    """컴파일된 강화 계획 워크플로우 앱을 반환한다.

    Args:
        checkpointer: Human-in-the-loop 사용 시 MemorySaver 전달
    """
    workflow = build_enhance_workflow()
    return workflow.compile(checkpointer=checkpointer)
