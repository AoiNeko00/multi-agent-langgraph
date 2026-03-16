"""리포트 생성(report generation) 에이전트.

수집된 정보를 구조화된 리포트로 작성한다.
"""

from __future__ import annotations

import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState
from src.tools.file_io import save_report


SYSTEM_PROMPT = """당신은 리포트 작성 전문가입니다.
수집된 정보를 바탕으로 구조화된 리포트를 작성하세요.

리포트 형식:
# [주제]

## 개요
[1-2문장 요약]

## 주요 발견
- [핵심 포인트 1]
- [핵심 포인트 2]
- ...

## 상세 분석
[분석 내용]

## 결론
[핵심 요약 및 시사점]

## 출처
[참고 자료 목록]"""


def create_reporter(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Reporter LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.5)


def report(state: AgentState) -> dict:
    """수집된 정보를 리포트로 작성한다."""
    llm = create_reporter()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"주제: {state['task']}\n\n"
        f"수집된 정보:\n{state.get('result', '')}\n\n"
        f"위 정보를 바탕으로 구조화된 리포트를 작성하세요."
    )

    messages.append(HumanMessage(content=prompt))
    response = llm.invoke(messages)

    # 파일명 생성: 작업 요약 + 타임스탬프(timestamp)
    slug = re.sub(r"[^\w가-힣]", "_", state["task"])[:40].strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{slug}_{timestamp}.md"

    save_result = save_report.invoke({
        "filename": filename,
        "content": response.content,
    })

    return {
        "result": response.content,
        "report_path": save_result,
        "status": "reporting",
        "messages": state.get("messages", []) + [response],
    }
