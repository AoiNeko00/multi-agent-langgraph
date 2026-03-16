"""리포트 생성(report generation) 에이전트.

수집된 정보를 구조화된 리포트로 작성한다.
"""

from __future__ import annotations

import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MAX_TOKENS_STRONG, MODEL_STRONG
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
| # | 발견 | 근거 |
|---|------|------|
| 1 | [구체적 발견] | [데이터/수치로 뒷받침] |
| 2 | ... | ... |

## 상세 분석
[수집된 데이터를 바탕으로 깊이 있는 분석. 각 단락은 하나의 논점만 다루되,
 그 논점을 충분히 설명. 최소 3-5개 논점을 다룰 것.
 각 논점마다 데이터에서 도출한 근거를 명시.]

## 비교 분석 (해당 시)
[대안, 경쟁 기술, 다른 접근법과의 비교표 포함]

## 한계 및 추가 조사 필요 사항
- [이 리포트에서 다루지 못한 것 — 구체적으로]
- [추가 조사가 필요한 질문들]

## 결론 및 권고
[핵심 시사점 요약 + 구체적인 다음 행동 3가지 권고]

## 출처
[수집된 데이터에 실제 URL이 있는 경우에만 이 섹션을 포함하고 해당 URL을 나열.
 URL이 없으면 이 섹션 자체를 생략할 것.]

## Critical Rules
- NEVER invent, fabricate, or hallucinate sources. If no URL exists in the data, omit the 출처 section entirely.
- NEVER cite URLs you haven't seen in the collected data.
- NEVER add claims like "~에 대한 논문 및 연구자료" without an actual URL.
- If you cannot verify a source, write "[출처 미확인]" instead of making one up.
- Never use Chinese characters. Korean and English only.
- Do not repeat the same information in different sections.
- Write as much detail as possible. Use the full output capacity.
- Aim for a comprehensive, publication-quality report."""


def create_reporter() -> ChatGroq:
    """Reporter LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_STRONG,
        temperature=0.4,
        max_tokens=MAX_TOKENS_STRONG,
    )


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
