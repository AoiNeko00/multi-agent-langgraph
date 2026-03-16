"""리서치(research) 에이전트.

웹 검색 도구를 활용하여 정보를 수집하고 요약한다.
검색 → 요약 → 리포트 생성 파이프라인의 핵심 에이전트.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import MAX_TOKENS_STRONG, MODEL_STRONG
from src.graph.state import AgentState
from src.tools.search import web_search


SYSTEM_PROMPT = """/no_think
You are a research specialist. You must respond in Korean only.

Your job: search the web for information on the given topic and compile findings.

## Rules
- Use the web_search tool to find information
- IMPORTANT: Always write search queries in English for better results
  Example: topic "LangGraph 최신 기능" → search query "LangGraph latest features 2026"
- Collect information from at least 2-3 different search queries for comprehensive coverage
- Clearly distinguish facts from opinions
- Include source URLs for every claim
- Never use Chinese characters. Korean and English only.

## Output Format

### 검색 쿼리
1. "[사용한 영어 검색어]"
2. "[사용한 영어 검색어]"

### 수집된 정보

#### [주제 1]
- [사실/발견] (출처: URL)
- [사실/발견] (출처: URL)

#### [주제 2]
- ...

### 핵심 요약
[3-5문장으로 핵심 요약]"""


def create_researcher() -> ChatGroq:
    """Researcher LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_STRONG,
        temperature=0.3,
        max_tokens=MAX_TOKENS_STRONG,
    )


def research(state: AgentState) -> dict:
    """웹 검색을 수행하고 수집된 정보를 반환한다."""
    llm = create_researcher()
    llm_with_tools = llm.bind_tools([web_search])

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    prompt = (
        f"다음 주제를 조사하세요: {state['task']}\n\n"
        f"반드시 영어로 3개 이상의 검색 쿼리를 작성하고, "
        f"각각 web_search 도구를 호출하세요.\n"
        f"다양한 관점(개념, 비교, 실사례)에서 검색하세요."
    )
    messages.append(HumanMessage(content=prompt))

    response = llm_with_tools.invoke(messages)

    # 도구 호출(tool call)이 있으면 실행
    search_results = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                result = web_search.invoke(tool_call["args"])
                query = tool_call["args"].get("query", "")
                search_results.append(f"### Query: {query}\n\n{result}")

    # 검색 결과가 부족하면 다각도 영어 쿼리로 보충
    if len(search_results) < 2:
        task = state["task"]
        queries = [
            f"{task} overview features",
            f"{task} vs alternatives comparison 2026",
            f"{task} tutorial example",
        ]
        for q in queries:
            result = web_search.invoke({"query": q, "max_results": 5})
            search_results.append(f"### Auto Query: {q}\n\n{result}")

    combined = "## 검색 결과\n\n" + "\n\n---\n\n".join(search_results)

    return {
        "result": combined,
        "status": "executing",
        "messages": state.get("messages", []) + [response],
    }
