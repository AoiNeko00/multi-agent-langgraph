"""목표 분해(goal decomposition) 에이전트.

threadloom Phase 2(분석)에 대응하며,
주어진 작업을 실행 가능한 단계별 계획으로 분해한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState


SYSTEM_PROMPT = """당신은 작업 계획 전문가입니다.
주어진 작업을 구체적이고 실행 가능한 단계별 계획으로 분해하세요.

규칙:
- 각 단계는 독립적으로 검증 가능해야 합니다
- 단계는 5개 이하로 유지하세요
- 이전 피드백이 있다면 반드시 반영하세요

출력 형식:
1. [단계] - [검증 방법]
2. [단계] - [검증 방법]
..."""


def create_planner(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Planner LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.3)


def plan(state: AgentState) -> dict:
    """작업을 분석하고 실행 계획을 생성한다."""
    llm = create_planner()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # 피드백(feedback)이 있으면 개선 요청으로 변환
    if state.get("feedback"):
        prompt = (
            f"작업: {state['task']}\n\n"
            f"이전 계획: {state.get('plan', '')}\n\n"
            f"피드백: {state['feedback']}\n\n"
            f"피드백을 반영하여 계획을 수정하세요."
        )
    else:
        prompt = f"작업: {state['task']}\n\n단계별 실행 계획을 작성하세요."

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    return {
        "plan": response.content,
        "status": "planning",
        "messages": state.get("messages", []) + [response],
    }
