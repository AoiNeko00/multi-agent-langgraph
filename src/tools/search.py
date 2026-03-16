"""웹 검색(web search) 도구.

DuckDuckGo를 사용하여 무료로 웹 검색을 수행한다.
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """웹에서 정보를 검색한다. 검색어는 영어로 작성해야 좋은 결과를 얻는다.

    Args:
        query: 검색 쿼리(query) 문자열 (영어 권장)
        max_results: 최대 결과 수 (기본: 5)

    Returns:
        검색 결과를 포맷팅한 문자열
    """
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        # 영어권 결과 우선(region) 설정
        results = list(ddgs.text(
            query,
            region="us-en",
            max_results=max_results,
        ))

    if not results:
        return "검색 결과가 없습니다."

    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"[{i}] {r['title']}\n"
            f"    URL: {r['href']}\n"
            f"    {r['body']}"
        )

    return "\n\n".join(formatted)
