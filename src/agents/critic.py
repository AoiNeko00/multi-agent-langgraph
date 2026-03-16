"""결과 검증(critic) 에이전트.

threadloom Phase 3.5(자동 심사)에 대응하며,
Executor의 결과물을 검증하고 통과/거부를 판정한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState


SYSTEM_PROMPT = """당신은 품질 검증 전문가입니다.
실행 결과물을 원래 작업 목표와 대조하여 검증하세요.

판정 기준:
- 원래 작업의 요구사항을 모두 충족하는가?
- 결과물이 구체적이고 활용 가능한가?
- 논리적 오류나 누락이 없는가?

반드시 다음 형식으로 응답하세요:
VERDICT: PASS 또는 FAIL
FEEDBACK: [구체적인 피드백]"""


def create_critic(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Critic LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.1)


def critique(state: AgentState) -> dict:
    """결과물을 검증하고 판정한다."""
    llm = create_critic()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"원래 작업: {state['task']}\n\n"
        f"실행 계획:\n{state['plan']}\n\n"
        f"실행 결과:\n{state['result']}\n\n"
        f"위 결과물을 검증하세요."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    content = response.content
    passed = "VERDICT: PASS" in content.upper()

    # 피드백 추출(feedback extraction)
    feedback = ""
    if "FEEDBACK:" in content:
        feedback = content.split("FEEDBACK:", 1)[1].strip()

    new_iteration = state.get("iteration", 0) + 1
    max_iter = state.get("max_iterations", 3)

    # 최대 반복 도달 시 강제 통과
    if new_iteration >= max_iter:
        passed = True
        feedback += "\n[최대 반복 횟수 도달로 강제 통과]"

    return {
        "feedback": feedback,
        "status": "done" if passed else "reviewing",
        "iteration": new_iteration,
        "messages": state.get("messages", []) + [response],
    }
