"""병렬 리서치(parallel research) 워크플로우 테스트."""

from src.graph.parallel_research import (
    ParallelResearchState,
    build_parallel_research_workflow,
    create_parallel_research_app,
    fan_out_searches,
)


def test_build_parallel_research_workflow_has_nodes():
    """병렬 리서치 워크플로우에 필수 노드가 등록되는지 확인한다."""
    workflow = build_parallel_research_workflow()
    node_names = set(workflow.nodes.keys())
    assert "query_generator" in node_names
    assert "search_worker" in node_names
    assert "collector" in node_names
    assert "reporter" in node_names
    assert "critic" in node_names


def test_create_parallel_research_app_compiles():
    """병렬 리서치 워크플로우가 정상 컴파일되는지 확인한다."""
    app = create_parallel_research_app()
    assert app is not None


def test_fan_out_generates_send_objects():
    """fan_out_searches가 쿼리 수만큼 Send 객체를 생성하는지 확인한다."""
    state: ParallelResearchState = {
        "messages": [],
        "task": "테스트 작업",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "context": "",
        "report_path": "",
        "status": "searching",
        "queries": ["query A", "query B", "query C"],
        "search_results": [],
    }
    sends = fan_out_searches(state)
    assert len(sends) == 3
    assert sends[0].node == "search_worker"


def test_parallel_research_state_has_context():
    """ParallelResearchState에 context 필드가 존재하는지 확인한다."""
    annotations = ParallelResearchState.__annotations__
    assert "context" in annotations
