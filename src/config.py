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
MODEL_STRONG = "qwen/qwen3-32b"
MODEL_REASONING = "llama-3.3-70b-versatile"

# 모델별 최대 출력 토큰(max completion tokens)
MAX_TOKENS_STRONG = 40_960      # qwen3-32b
MAX_TOKENS_REASONING = 32_768   # llama-3.3-70b
