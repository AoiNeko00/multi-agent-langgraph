"""목표 분해(goal decomposition) 에이전트.

threadloom Phase 2(분석)에 대응하며,
주어진 작업을 실행 가능한 단계별 계획으로 분해한다.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MAX_TOKENS_STRONG, MODEL_STRONG
from src.graph.state import AgentState
from src.tools.report_history import get_recent_reports


SYSTEM_PROMPT = """/no_think
You are a task planning expert. You must respond in Korean only.

Your job: decompose a given task into a concrete, actionable step-by-step plan.

## Output Format (strictly follow this)

### 목표
[한 문장으로 최종 목표 정의]

### 전제 조건
- [이 계획이 전제하는 가정 1]
- [가정 2]

### 실행 계획

For each step, provide ALL of the following in detail:

#### 단계 1: [구체적 행동]
- **설명**: [이 단계에서 정확히 무엇을 하는지 3-5문장으로 상세히 설명]
- **산출물**: [만들어지는 구체적 파일, 코드, 문서 등]
- **검증 방법**: [완료 확인 방법 — 실행 명령어, 테스트 케이스 등]
- **예상 소요 시간**: [시간 단위]
- **의존성**: [이전 단계 중 선행되어야 하는 것]

#### 단계 2: ...
(repeat for all steps)

### 리스크 분석

| # | 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|---|--------|----------|--------|----------|
| 1 | [구체적 리스크] | 높음/중간/낮음 | 높음/중간/낮음 | [구체적 대응] |

### 대안 계획
[주 계획 실패 시 대안 접근법 1-2가지 제시]

## Rules
- Maximum 7 steps
- Each step must produce a verifiable output
- Write as much detail as possible. Use the full output capacity.
- If previous feedback exists, address every point explicitly
- Be specific: "Flask로 /users GET 엔드포인트 구현" not "API 구현"
- Never use Chinese characters. Korean and English only."""


def create_planner() -> ChatGroq:
    """Planner LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_STRONG,
        temperature=0.3,
        max_tokens=MAX_TOKENS_STRONG,
    )


def plan(state: AgentState) -> dict:
    """작업을 분석하고 실행 계획을 생성한다."""
    llm = create_planner()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # 과거 리포트 참조(RAG) 주입
    history_block = ""
    recent = get_recent_reports(limit=2)
    if recent:
        history_block = (
            f"## 과거 리포트 (중복 방지 및 연속성 참고용)\n{recent}\n\n"
        )

    # 프로젝트 컨텍스트(context)가 있으면 주입
    context_block = ""
    if state.get("context"):
        context_block = (
            f"## 프로젝트 컨텍스트 (반드시 이 정보를 기반으로 계획을 수립할 것)\n"
            f"{state.get('context', '')}\n\n"
        )

    # 피드백(feedback)이 있으면 개선 요청으로 변환
    if state.get("feedback"):
        prompt = (
            f"{history_block}{context_block}"
            f"## 작업\n{state.get('task', '')}\n\n"
            f"## 이전 계획\n{state.get('plan', '')}\n\n"
            f"## Critic 피드백 (반드시 모두 반영할 것)\n{state.get('feedback', '')}\n\n"
            f"피드백의 각 지적사항을 하나씩 해결하여 계획을 수정하세요."
        )
    else:
        prompt = (
            f"{history_block}{context_block}"
            f"## 작업\n{state.get('task', '')}\n\n위 작업에 대한 실행 계획을 작성하세요."
        )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    return {
        "plan": response.content,
        "status": "planning",
        "messages": state.get("messages", []) + [response],
    }
