"""강화 제안(enhancement proposal) 에이전트.

threadloom의 분석 데이터를 읽고, 시스템 자기강화 계획을 제안한다.
threadloom Phase 3(강화 생성)의 LangGraph 재설계 버전.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState
from src.tools.threadloom import load_analyses, load_pending_actions


SYSTEM_PROMPT = """당신은 AI 시스템 자기강화 전문가입니다.
threadloom이 수집·분석한 인사이트를 바탕으로, AI 에이전트 시스템을 개선할 수 있는
구체적인 강화 제안을 작성하세요.

강화 유형:
- **skill**: 반복 가능한 단일 작업 패턴 (예: 코드 리뷰 체크리스트)
- **agent**: 다단계 전문 역할 정의 (예: 보안 감사 에이전트)
- **rule**: 코딩 규칙·컨벤션 (예: 함수 20줄 제한)

출력 형식:
## 강화 제안

### 제안 1: [유형] — [이름]
- **근거**: threadloom 분석에서 발견된 패턴
- **설명**: 무엇을 하는지
- **구현 방향**: 어떻게 구현할지
- **기대 효과**: 어떤 개선이 예상되는지

### 제안 2: ...

규칙:
- threadloom 분석 데이터의 실제 인사이트를 기반으로 하세요
- 기존 대기 중인 강화 항목과 중복되지 않게 하세요
- 3~5개의 제안을 작성하세요
- 각 제안은 독립적으로 구현 가능해야 합니다"""


def create_enhancer(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Enhancer LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.4)


def enhance(state: AgentState) -> dict:
    """threadloom 데이터를 분석하고 강화 제안을 생성한다."""
    # threadloom 데이터 로드
    analyses = load_analyses.invoke({"limit": 1})
    pending = load_pending_actions.invoke({})

    llm = create_enhancer()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"## 컨텍스트\n\n"
        f"사용자 요청: {state['task']}\n\n"
        f"{analyses}\n\n"
        f"{pending}\n\n"
        f"위 threadloom 데이터를 분석하여 강화 제안을 작성하세요.\n"
        f"기존 대기 항목과 중복되지 않는 새로운 제안만 포함하세요."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    return {
        "result": response.content,
        "status": "enhancing",
        "messages": state.get("messages", []) + [response],
    }
