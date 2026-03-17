"""병렬 검색(parallel search) 워크플로우.

Send API를 활용하여 여러 검색 쿼리를 병렬로 팬아웃(fan-out) 실행한다.

워크플로우:
  [입력] → query_generator → Send(search_worker x3)
    → collector → reporter → critic → {pass → END, fail → query_generator}
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from src.utils import strip_think_tags

from src.agents.critic import critique
from src.agents.reporter import report
from src.config import MAX_TOKENS_STRONG, MODEL_STRONG


class ParallelResearchState(TypedDict):
    """병렬 리서치 워크플로우 상태(state).

    Attributes:
        messages: 에이전트 간 메시지 히스토리
        task: 사용자 입력 작업
        plan: 실행 계획
        result: 최종 결과물
        feedback: Critic 피드백(feedback)
        iteration: 현재 반복 횟수
        max_iterations: 최대 반복 횟수
        context: 프로젝트 컨텍스트(context)
        report_path: 저장된 리포트 파일 경로
        status: 워크플로우 상태
        queries: 생성된 검색 쿼리(query) 목록
        search_results: 병렬 검색 결과 (리듀서(reducer)로 병합)
    """

    messages: list[BaseMessage]
    task: str
    plan: str
    result: str
    feedback: str
    iteration: int
    max_iterations: int
    context: str
    report_path: str
    status: str
    queries: list[str]
    search_results: Annotated[list[str], operator.add]


# 검색 워커(search worker)가 받는 입력 상태
class SearchWorkerInput(TypedDict):
    """개별 검색 워커의 입력 상태."""

    query: str
    task: str
    context: str


QUERY_GEN_PROMPT = """/no_think
You are a search query specialist. Given a research topic, generate exactly 3 diverse
English search queries that cover different angles of the topic.

## Rules
- Write queries in English for best search results
- Each query should explore a different aspect (overview, comparison, practical usage)
- Output ONLY 3 queries, one per line, no numbering or bullets
- No explanation, just the queries"""


def _create_llm() -> ChatGroq:
    """LLM 인스턴스 생성."""
    return ChatGroq(
        model=MODEL_STRONG,
        temperature=0.3,
        max_tokens=MAX_TOKENS_STRONG,
    )


def query_generator_node(state: ParallelResearchState) -> dict:
    """검색 쿼리 생성 노드: 작업에서 3개의 검색 쿼리를 생성한다."""
    llm = _create_llm()
    messages = [
        SystemMessage(content=QUERY_GEN_PROMPT),
        HumanMessage(content=f"Research topic: {state['task']}"),
    ]
    response = llm.invoke(messages)

    # 응답에서 쿼리 파싱(parsing)
    content = strip_think_tags(response.content)
    lines = [ln.strip() for ln in content.strip().split("\n") if ln.strip()]
    queries = lines[:3]

    return {
        "queries": queries,
        "status": "searching",
        "messages": state.get("messages", []) + [response],
    }


def fan_out_searches(state: ParallelResearchState) -> list[Send]:
    """Send API로 검색 쿼리를 병렬 워커에 팬아웃(fan-out)한다."""
    return [
        Send("search_worker", {
            "query": query,
            "task": state["task"],
            "context": state.get("context", ""),
        })
        for query in state.get("queries", [])
    ]


def search_worker_node(state: SearchWorkerInput) -> dict:
    """개별 검색 워커 노드: 단일 쿼리로 웹 검색을 수행한다."""
    from src.tools.search import web_search

    query = state["query"]
    result = web_search.invoke({"query": query, "max_results": 5})
    formatted = f"### Query: {query}\n\n{result}"

    return {"search_results": [formatted]}


def collector_node(state: ParallelResearchState) -> dict:
    """수집기(collector) 노드: 병렬 검색 결과를 하나의 결과물로 통합한다."""
    results = state.get("search_results", [])
    combined = "## 병렬 검색 결과\n\n" + "\n\n---\n\n".join(results)

    # 컨텍스트가 있으면 포함
    if state.get("context"):
        combined = (
            f"## 프로젝트 내부 정보\n{state['context']}\n\n---\n\n"
            + combined
        )

    return {"result": combined, "status": "executing"}


def reporter_node(state: ParallelResearchState) -> dict:
    """Reporter 에이전트 노드."""
    return report(state)


def critic_node(state: ParallelResearchState) -> dict:
    """Critic 에이전트 노드."""
    return critique(state)


def should_continue(state: ParallelResearchState) -> str:
    """Critic 판정에 따라 분기하는 조건부 엣지(conditional edge)."""
    if state.get("status") == "done":
        return "end"
    return "query_generator"


def build_parallel_research_workflow() -> StateGraph:
    """병렬 리서치 워크플로우 그래프를 구성한다."""
    workflow = StateGraph(ParallelResearchState)

    workflow.add_node("query_generator", query_generator_node)
    workflow.add_node("search_worker", search_worker_node)
    workflow.add_node("collector", collector_node)
    workflow.add_node("reporter", reporter_node)
    workflow.add_node("critic", critic_node)

    workflow.set_entry_point("query_generator")

    # query_generator → 병렬 search_worker 팬아웃
    workflow.add_conditional_edges(
        "query_generator",
        fan_out_searches,
        ["search_worker"],
    )

    # 모든 search_worker 완료 → collector
    workflow.add_edge("search_worker", "collector")
    workflow.add_edge("collector", "reporter")
    workflow.add_edge("reporter", "critic")

    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "end": END,
            "query_generator": "query_generator",
        },
    )

    return workflow


def create_parallel_research_app():
    """컴파일된 병렬 리서치 워크플로우 앱을 반환한다."""
    workflow = build_parallel_research_workflow()
    return workflow.compile()
