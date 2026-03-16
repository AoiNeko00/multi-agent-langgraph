"""Memory 모듈 테스트."""

import json
from pathlib import Path

from src.agents.memory import load_history, save_execution


def test_save_and_load_execution(tmp_path, monkeypatch):
    """실행 이력 저장 및 로드가 정상 동작하는지 확인한다."""
    # data 디렉토리를 임시 경로(tmp_path)로 교체
    monkeypatch.setattr("src.agents.memory.DATA_DIR", tmp_path)
    monkeypatch.setattr(
        "src.agents.memory.HISTORY_FILE",
        tmp_path / "execution_history.json",
    )

    save_execution(
        task="테스트 작업",
        plan="테스트 계획",
        result="테스트 결과",
        iterations=2,
    )

    history = load_history()
    assert len(history) == 1
    assert history[0]["task"] == "테스트 작업"
    assert history[0]["iterations"] == 2


def test_load_empty_history(tmp_path, monkeypatch):
    """이력 파일이 없을 때 빈 리스트를 반환하는지 확인한다."""
    monkeypatch.setattr("src.agents.memory.DATA_DIR", tmp_path)
    monkeypatch.setattr(
        "src.agents.memory.HISTORY_FILE",
        tmp_path / "nonexistent.json",
    )

    history = load_history()
    assert history == []
