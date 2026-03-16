"""실행(execution) 에이전트.

threadloom Phase 3(강화 생성)에 대응하며,
Planner의 계획을 받아 실제 결과물을 생성한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState


SYSTEM_PROMPT = """당신은 실행 전문가입니다.
주어진 계획을 단계별로 수행하고 구체적인 결과물을 생성하세요.

규칙:
- 계획의 각 단계를 빠짐없이 수행하세요
- 결과물은 구체적이고 즉시 활용 가능해야 합니다
- 불확실한 부분은 명시적으로 표기하세요"""


def create_executor(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Executor LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.5)


def execute(state: AgentState) -> dict:
    """계획을 실행하고 결과물을 생성한다."""
    llm = create_executor()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"작업: {state['task']}\n\n"
        f"실행 계획:\n{state['plan']}\n\n"
        f"위 계획을 실행하고 결과물을 생성하세요."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    return {
        "result": response.content,
        "status": "executing",
        "messages": state.get("messages", []) + [response],
    }
