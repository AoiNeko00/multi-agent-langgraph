"""AgentState 정의 테스트."""

from src.graph.state import AgentState


def test_agent_state_keys():
    """AgentState에 필수 키가 존재하는지 확인한다."""
    state: AgentState = {
        "messages": [],
        "task": "테스트 작업",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "status": "planning",
    }

    assert state["task"] == "테스트 작업"
    assert state["iteration"] == 0
    assert state["max_iterations"] == 3
    assert state["status"] == "planning"
