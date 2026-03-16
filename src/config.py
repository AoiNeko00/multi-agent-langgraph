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
# 분석·생성: Qwen3 32B (한국어 우수, 662 TPS)
# 검증: Llama 3.3 70B (최고 추론 품질)
# 경량 작업: Llama 3.1 8B (빠른 속도)
MODEL_STRONG = "qwen/qwen3-32b"
MODEL_REASONING = "llama-3.3-70b-versatile"
MODEL_FAST = "llama-3.1-8b-instant"
MAX_ITERATIONS = 3
