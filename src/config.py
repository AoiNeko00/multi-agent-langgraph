"""설정(configuration) 관리 모듈.

환경 변수 로드 및 LangSmith 트레이싱 설정을 관리한다.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


def init_config() -> None:
    """환경 변수를 로드하고 LangSmith 트레이싱을 설정한다."""
    load_dotenv()

    # LangSmith 트레이싱(tracing) 활성화
    if os.getenv("LANGSMITH_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault(
            "LANGCHAIN_PROJECT",
            os.getenv("LANGSMITH_PROJECT", "multi-agent-langgraph"),
        )


# Groq 모델(model) 설정
DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "mixtral-8x7b-32768"
MAX_ITERATIONS = 3
