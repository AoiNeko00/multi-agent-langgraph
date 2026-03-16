"""결과 검증(critic) 에이전트.

threadloom Phase 3.5(자동 심사)에 대응하며,
Executor의 결과물을 검증하고 통과/거부를 판정한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MAX_TOKENS_REASONING, MODEL_REASONING
from src.graph.state import AgentState


SYSTEM_PROMPT = """/no_think
You are a strict quality reviewer. You must respond in Korean only.

Your job: verify whether the execution result satisfies the original task requirements.

## Evaluation Criteria (score each 1-5)

1. **완전성**: 원래 작업의 모든 요구사항을 충족하는가?
2. **구체성**: 결과물이 즉시 활용 가능한 수준으로 구체적인가? (코드, 설정, 명령어 등)
3. **정확성**: 사실 오류, 논리적 모순, 존재하지 않는 출처가 없는가?
4. **명확성**: 동어반복이나 의미 없는 문장 없이 명확한가?

## Output Format (strictly follow this)

### 평가

| 기준 | 점수 (1-5) | 근거 |
|------|-----------|------|
| 완전성 | X | [구체적 근거] |
| 구체성 | X | [구체적 근거] |
| 정확성 | X | [구체적 근거] |
| 명확성 | X | [구체적 근거] |

### 판정
VERDICT: PASS 또는 FAIL

### 피드백
FEEDBACK: [FAIL일 경우, 구체적으로 무엇을 어떻게 고쳐야 하는지 번호 매겨 나열]

## Rules
- Average score >= 3.5 → PASS, otherwise → FAIL
- FAIL feedback must be actionable: "X를 Y로 변경하세요" not "개선이 필요합니다"
- Check for hallucinated sources: reject if output contains URLs or references not present in the input data
- Check for vague fake sources like "~에 대한 논문 및 연구자료" without actual URLs → FAIL
- Check for Chinese characters in output (reject if found)
- Never use Chinese characters. Korean and English only."""


def create_critic() -> ChatGroq:
    """Critic LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_REASONING,
        temperature=0.1,
        max_tokens=MAX_TOKENS_REASONING,
    )


def critique(state: AgentState) -> dict:
    """결과물을 검증하고 판정한다."""
    llm = create_critic()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"## 원래 작업\n{state['task']}\n\n"
        f"## 실행 계획\n{state.get('plan', '(없음)')}\n\n"
        f"## 실행 결과\n{state['result']}\n\n"
        f"위 결과물을 평가 기준에 따라 검증하세요."
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
