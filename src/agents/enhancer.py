"""강화 제안(enhancement proposal) 에이전트.

threadloom의 분석 데이터를 읽고, 시스템 자기강화 계획을 제안한다.
threadloom Phase 3(강화 생성)의 LangGraph 재설계 버전.
"""

from __future__ import annotations

from difflib import SequenceMatcher

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MAX_TOKENS_STRONG, MODEL_STRONG
from src.graph.state import AgentState
from src.tools.threadloom import load_analyses, load_pending_actions


SYSTEM_PROMPT = """/no_think
You are an AI system self-enhancement expert. You must respond in Korean only.

Your job: analyze threadloom's collected insights and propose concrete enhancements
for the AI agent system.

## Enhancement Types
- **skill**: A reusable single-task pattern with clear trigger and steps
  Example: "코드 리뷰 skill — PR diff를 받아 보안/성능/가독성 3관점으로 체크리스트 실행"
- **agent**: A multi-step specialist role with defined authority and workflow
  Example: "보안 감사 에이전트 — OWASP Top 10 기준으로 코드베이스 스캔 후 리포트 생성"
- **rule**: A coding convention or behavioral constraint
  Example: "함수 20줄 제한 — 초과 시 헬퍼 추출 필수"

## Output Format (strictly follow)

## 강화 제안

### 제안 1: [유형] — [이름]
- **근거**: [threadloom 데이터의 어떤 포스트/패턴에서 도출했는지 구체적으로]
- **현재 문제**: [이 강화가 없으면 발생하는 구체적 문제]
- **설명**: [정확히 무엇을 하는지 2-3문장]
- **구현 사양**:
  - 트리거: [언제 실행되는지]
  - 입력: [무엇을 받는지]
  - 출력: [무엇을 내보내는지]
  - 단계: [1. ... 2. ... 3. ...]
- **기대 효과**: [정량적이거나 구체적인 개선 — "효율성 향상" 금지]

### 제안 2: ...

## Rules
- Propose exactly 3 enhancements (not more, not less)
- Each proposal must trace back to specific data in the threadloom analysis
- Do NOT duplicate items already in pending actions (check the list carefully)
- Do NOT use vague descriptions. Every sentence must be specific and actionable.
- Never fabricate threadloom data that doesn't exist in the provided context.
- Never use Chinese characters. Korean and English only."""


def create_enhancer() -> ChatGroq:
    """Enhancer LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_STRONG,
        temperature=0.3,
        max_tokens=MAX_TOKENS_STRONG,
    )


def enhance(state: AgentState) -> dict:
    """threadloom 데이터를 분석하고 강화 제안을 생성한다."""
    # threadloom 데이터 로드
    analyses = load_analyses.invoke({"limit": 1})
    pending = load_pending_actions.invoke({})

    llm = create_enhancer()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"## 사용자 요청\n{state['task']}\n\n"
        f"## threadloom 분석 데이터\n{analyses}\n\n"
        f"## 이미 대기 중인 강화 항목 (중복 금지)\n{pending}\n\n"
        f"위 데이터를 분석하여 3개의 강화 제안을 작성하세요.\n"
        f"대기 항목에 이미 있는 것과 중복되지 않아야 합니다."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    # 의미적 유사도 검사(semantic similarity check)
    result_with_check = _check_similarity(response.content, pending)

    return {
        "result": result_with_check,
        "status": "enhancing",
        "messages": state.get("messages", []) + [response],
    }


def _check_similarity(proposals: str, pending: str) -> str:
    """제안과 기존 pending 항목의 유사도를 계산하여 경고를 추가한다.

    SequenceMatcher를 사용하여 텍스트 유사도를 측정하고,
    임계값(0.6) 이상이면 중복 경고를 삽입한다.
    """
    pending_names = _extract_pending_names(pending)
    if not pending_names:
        return proposals

    warnings = []
    for name in pending_names:
        # 제안 텍스트에서 유사한 이름이 있는지 검사
        ratio = SequenceMatcher(None, name.lower(), proposals.lower()).ratio()
        if ratio > 0.6:
            warnings.append(f"- [유사도 {ratio:.0%}] '{name}'과 중복 가능성")

    if warnings:
        warning_block = (
            "\n\n## 중복 경고 (자동 감지)\n"
            + "\n".join(warnings)
            + "\n위 항목과 차별화되는지 확인하세요.\n"
        )
        return proposals + warning_block

    return proposals


def _extract_pending_names(pending_text: str) -> list[str]:
    """pending 목록에서 파일명을 추출한다."""
    names = []
    for line in pending_text.split("\n"):
        if line.startswith("- **") and "**:" in line:
            name = line.split("**")[1].replace(".md", "")
            names.append(name)
    return names
