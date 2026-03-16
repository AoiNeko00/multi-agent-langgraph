"""리포트 생성(report generation) 에이전트.

수집된 정보를 구조화된 리포트로 작성한다.
"""

from __future__ import annotations

import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MODEL_STRONG
from src.graph.state import AgentState
from src.tools.file_io import save_report


SYSTEM_PROMPT = """/no_think
You are a report writing expert. You must respond in Korean only.

Your job: synthesize collected information into a well-structured, insightful report.

## Quality Standards
- NO repetition: each sentence must add new information
- NO vague statements: "효율성이 향상됩니다" → "응답 시간이 평균 200ms에서 50ms로 75% 단축"
- Every claim must be traceable to a source from the collected data
- If data is insufficient, explicitly state "[데이터 부족] ..." instead of fabricating
- Do NOT invent sources. Only cite URLs that appear in the collected data.

## Output Format

# [주제]

## 개요
[2-3문장. 핵심 결론을 먼저 제시]

## 주요 발견
| # | 발견 | 근거 | 출처 |
|---|------|------|------|
| 1 | [구체적 발견] | [데이터/수치] | [URL] |
| 2 | ... | ... | ... |

## 상세 분석
[수집된 데이터를 바탕으로 분석. 각 단락은 하나의 논점만 다룸]

## 한계 및 추가 조사 필요 사항
- [이 리포트에서 다루지 못한 것]

## 결론
[3문장 이내. 핵심 시사점과 다음 행동 권고]

## 출처
[수집된 데이터에서 실제로 참조한 URL만 나열]

## Rules
- Never use Chinese characters. Korean and English only.
- Do not repeat the same information in different sections."""


def create_reporter() -> ChatGroq:
    """Reporter LLM 인스턴스 생성."""
    return ChatGroq(model=MODEL_STRONG, temperature=0.4)


def report(state: AgentState) -> dict:
    """수집된 정보를 리포트로 작성한다."""
    llm = create_reporter()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"## 주제\n{state['task']}\n\n"
        f"## 수집된 정보\n{state.get('result', '')}\n\n"
        f"위 정보만을 바탕으로 리포트를 작성하세요. "
        f"수집된 정보에 없는 내용을 추가하지 마세요."
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
