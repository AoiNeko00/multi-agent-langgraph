"""실행(execution) 에이전트.

threadloom Phase 3(강화 생성)에 대응하며,
Planner의 계획을 받아 실제 결과물을 생성한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MODEL_STRONG
from src.graph.state import AgentState


SYSTEM_PROMPT = """/no_think
You are an execution expert. You must respond in Korean only.

Your job: execute each step of the given plan and produce concrete deliverables.

## Rules
- Address every step in the plan. Do not skip any.
- For each step, provide the actual deliverable (code, config, text, etc.)
- Mark uncertain parts with "[불확실] 이유: ..."
- Use specific names, values, and examples. Never be vague.
- If the plan mentions code, write actual runnable code, not pseudocode.
- Never use Chinese characters. Korean and English only.

## Output Format

### 단계 1: [단계명]
**산출물:**
[구체적인 결과물]

### 단계 2: [단계명]
**산출물:**
[구체적인 결과물]

..."""


def create_executor() -> ChatGroq:
    """Executor LLM 인스턴스 생성."""
    return ChatGroq(model=MODEL_STRONG, temperature=0.4)


def execute(state: AgentState) -> dict:
    """계획을 실행하고 결과물을 생성한다."""
    llm = create_executor()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"## 원래 작업\n{state['task']}\n\n"
        f"## 실행할 계획\n{state['plan']}\n\n"
        f"위 계획의 각 단계를 실행하고 구체적인 결과물을 생성하세요."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    return {
        "result": response.content,
        "status": "executing",
        "messages": state.get("messages", []) + [response],
    }
