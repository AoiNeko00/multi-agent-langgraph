"""강화 워크플로우 테스트."""

from src.graph.enhance_workflow import build_enhance_workflow, create_enhance_app


def test_build_enhance_workflow_has_nodes():
    """강화 워크플로우에 필수 노드가 등록되는지 확인한다."""
    workflow = build_enhance_workflow()
    node_names = set(workflow.nodes.keys())
    assert "enhancer" in node_names
    assert "planner" in node_names
    assert "critic" in node_names
    assert "reporter" in node_names


def test_create_enhance_app_compiles():
    """강화 워크플로우가 정상 컴파일되는지 확인한다."""
    app = create_enhance_app()
    assert app is not None
