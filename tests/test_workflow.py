"""워크플로우 그래프 구성 테스트."""

from langgraph.graph import END

from src.graph.nodes import should_continue
from src.graph.workflow import build_workflow, create_app
from src.graph.research_workflow import (
    build_research_workflow,
    create_research_app,
)


def test_build_workflow_has_nodes():
    """기본 워크플로우에 필수 노드가 등록되는지 확인한다."""
    workflow = build_workflow()
    node_names = set(workflow.nodes.keys())
    assert "planner" in node_names
    assert "executor" in node_names
    assert "critic" in node_names


def test_build_research_workflow_has_nodes():
    """리서치 워크플로우에 필수 노드가 등록되는지 확인한다."""
    workflow = build_research_workflow()
    node_names = set(workflow.nodes.keys())
    assert "researcher" in node_names
    assert "reporter" in node_names
    assert "critic" in node_names


def test_create_app_compiles():
    """기본 워크플로우가 정상 컴파일되는지 확인한다."""
    app = create_app()
    assert app is not None


def test_create_research_app_compiles():
    """리서치 워크플로우가 정상 컴파일되는지 확인한다."""
    app = create_research_app()
    assert app is not None


def test_should_continue_done():
    """status가 done이면 'end'를 반환하는지 확인한다."""
    state = {
        "messages": [],
        "task": "",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 1,
        "max_iterations": 3,
        "status": "done",
    }
    assert should_continue(state) == "end"


def test_should_continue_reviewing():
    """status가 reviewing이면 'planner'를 반환하는지 확인한다."""
    state = {
        "messages": [],
        "task": "",
        "plan": "",
        "result": "",
        "feedback": "개선 필요",
        "iteration": 1,
        "max_iterations": 3,
        "status": "reviewing",
    }
    assert should_continue(state) == "planner"
