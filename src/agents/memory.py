"""컨텍스트 관리(memory) 모듈.

에이전트 간 공유 컨텍스트와 실행 이력을 관리한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "execution_history.json"


def save_execution(task: str, plan: str, result: str, iterations: int) -> None:
    """실행 이력을 JSON 파일에 저장한다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "plan": plan,
        "result": result,
        "iterations": iterations,
    })

    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_history() -> list[dict]:
    """실행 이력을 로드한다."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
