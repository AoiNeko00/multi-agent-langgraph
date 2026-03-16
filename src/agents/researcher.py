"""리서치(research) 에이전트.

웹 검색 도구를 활용하여 정보를 수집하고 요약한다.
검색 → 요약 → 리포트 생성 파이프라인의 핵심 에이전트.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.graph.state import AgentState
from src.tools.search import web_search


SYSTEM_PROMPT = """당신은 리서치 전문가입니다.
주어진 주제에 대해 웹 검색 도구를 사용하여 정보를 수집하고 분석하세요.

사용 가능한 도구:
- web_search: 웹에서 정보를 검색합니다

규칙:
- 핵심 정보를 빠짐없이 수집하세요
- 출처를 명시하세요
- 사실과 의견을 구분하세요"""


def create_researcher(model_name: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Researcher LLM 인스턴스 생성."""
    return ChatGroq(model=model_name, temperature=0.3)


def research(state: AgentState) -> dict:
    """웹 검색을 수행하고 수집된 정보를 반환한다."""
    llm = create_researcher()
    llm_with_tools = llm.bind_tools([web_search])

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = f"다음 주제를 조사하세요: {state['task']}"
    messages.append(HumanMessage(content=prompt))

    response = llm_with_tools.invoke(messages)

    # 도구 호출(tool call)이 있으면 실행
    search_results = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                search_results = web_search.invoke(tool_call["args"])

    # 검색 결과를 상태에 저장
    combined = f"## 검색 결과\n\n{search_results}" if search_results else ""

    return {
        "result": combined,
        "status": "executing",
        "messages": state.get("messages", []) + [response],
    }
