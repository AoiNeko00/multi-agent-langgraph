"""통합 테스트(integration tests) — Mock 기반 워크플로우 전체 실행 검증.

LLM 호출 없이 워크플로우의 노드 간 데이터 흐름과
조건부 분기(conditional edge) 로직을 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ── 헬퍼(helper) ──────────────────────────────────────────────


def _mock_llm_response(content: str) -> MagicMock:
    """ChatGroq.invoke가 반환할 mock 응답 객체를 생성한다."""
    resp = MagicMock()
    resp.content = content
    resp.tool_calls = []
    return resp


# ── a. Plan 워크플로우 end-to-end ─────────────────────────────


@patch("src.agents.reporter.save_report")
@patch("src.agents.reporter.ChatGroq")
@patch("src.agents.critic.ChatGroq")
@patch("src.agents.executor.ChatGroq")
@patch("src.agents.planner.ChatGroq")
@patch("src.agents.planner.get_recent_reports", return_value="")
def test_plan_workflow_end_to_end(
    mock_recent,
    mock_planner_llm,
    mock_executor_llm,
    mock_critic_llm,
    mock_reporter_llm,
    mock_save_report,
    tmp_path,
):
    """계획(plan) 워크플로우가 planner→executor→critic(PASS)→reporter 순으로 실행되는지 확인한다."""
    # Planner 응답
    mock_planner_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 목표\n테스트 목표\n### 실행 계획\n#### 단계 1: 테스트\n- 설명: 테스트"
    )

    # Executor 응답
    mock_executor_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 단계 1: 테스트\n**산출물:** 결과물"
    )

    # Critic 응답 — PASS 판정
    mock_critic_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 판정\nVERDICT: PASS\nFEEDBACK: 없음"
    )

    # Reporter 응답
    mock_reporter_llm.return_value.invoke.return_value = _mock_llm_response(
        "# 리포트\n## 개요\n테스트 리포트 내용"
    )

    # save_report mock — 파일 저장 스킵(skip)
    mock_save_report.invoke.return_value = f"리포트 저장 완료: {tmp_path / 'test.md'}"

    from src.graph.workflow import create_app

    app = create_app()
    result = app.invoke({
        "messages": [],
        "task": "테스트 작업",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "context": "",
        "report_path": "",
        "status": "",
    })

    # 검증: 계획이 생성됨
    assert result["plan"] != ""

    # 검증: 결과가 생성됨
    assert result["result"] != ""

    # 검증: 리포트 경로가 설정됨
    assert result["report_path"] != ""

    # 검증: 상태가 reporting (reporter가 마지막이므로)
    assert result["status"] == "reporting"


# ── b. Critic이 거부 후 재시도하여 통과 ─────────────────────────


@patch("src.agents.reporter.save_report")
@patch("src.agents.reporter.ChatGroq")
@patch("src.agents.critic.ChatGroq")
@patch("src.agents.executor.ChatGroq")
@patch("src.agents.planner.ChatGroq")
@patch("src.agents.planner.get_recent_reports", return_value="")
def test_critic_rejects_and_loops(
    mock_recent,
    mock_planner_llm,
    mock_executor_llm,
    mock_critic_llm,
    mock_reporter_llm,
    mock_save_report,
    tmp_path,
):
    """Critic이 처음 FAIL을 반환하면 planner로 루프하고, 두 번째에 PASS하는지 확인한다."""
    # Planner — 두 번 호출됨 (초기 + 피드백 반영)
    mock_planner_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 목표\n개선된 계획\n### 실행 계획\n#### 단계 1: 개선\n- 설명: 개선 내용"
    )

    # Executor — 두 번 호출됨
    mock_executor_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 단계 1: 개선\n**산출물:** 개선된 결과물"
    )

    # Critic — 첫 번째 FAIL, 두 번째 PASS
    fail_resp = _mock_llm_response(
        "### 판정\nVERDICT: FAIL\nFEEDBACK: 구체성이 부족합니다. 코드를 추가하세요."
    )
    pass_resp = _mock_llm_response(
        "### 판정\nVERDICT: PASS\nFEEDBACK: 없음"
    )
    mock_critic_llm.return_value.invoke.side_effect = [fail_resp, pass_resp]

    # Reporter
    mock_reporter_llm.return_value.invoke.return_value = _mock_llm_response(
        "# 최종 리포트"
    )
    mock_save_report.invoke.return_value = f"리포트 저장 완료: {tmp_path / 'test.md'}"

    from src.graph.workflow import create_app

    app = create_app()
    result = app.invoke({
        "messages": [],
        "task": "루프 테스트 작업",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "context": "",
        "report_path": "",
        "status": "",
    })

    # 검증: iteration이 2 (FAIL 1회 + PASS 1회)
    assert result["iteration"] == 2

    # 검증: 피드백이 planner에 전달됨 (planner가 2번 호출됨)
    assert mock_planner_llm.return_value.invoke.call_count == 2

    # 검증: 최종 상태는 reporting
    assert result["status"] == "reporting"


# ── c. Research 워크플로우 Mock 검색 ──────────────────────────


@patch("src.agents.reporter.save_report")
@patch("src.agents.reporter.ChatGroq")
@patch("src.agents.critic.ChatGroq")
@patch("src.agents.researcher.web_search")
@patch("src.agents.researcher.ChatGroq")
def test_research_workflow_with_mock_search(
    mock_researcher_llm,
    mock_web_search,
    mock_critic_llm,
    mock_reporter_llm,
    mock_save_report,
    tmp_path,
):
    """리서치 워크플로우에서 검색 결과가 reporter 입력에 포함되는지 확인한다."""
    # Researcher LLM — tool_calls 없는 응답 (자동 쿼리(auto query) 모드 활성화)
    researcher_resp = MagicMock()
    researcher_resp.content = "검색 결과 요약"
    researcher_resp.tool_calls = []
    mock_researcher_llm.return_value.bind_tools.return_value.invoke.return_value = (
        researcher_resp
    )

    # web_search mock — 자동 쿼리에서 호출됨
    mock_web_search.invoke.return_value = (
        "[1] Mock 결과 제목\n    URL: https://example.com\n    Mock 검색 내용"
    )

    # Critic — PASS
    mock_critic_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 판정\nVERDICT: PASS\nFEEDBACK: 없음"
    )

    # Reporter
    mock_reporter_llm.return_value.invoke.return_value = _mock_llm_response(
        "# 리서치 리포트\n## 개요\n검색 기반 리포트"
    )
    mock_save_report.invoke.return_value = f"리포트 저장 완료: {tmp_path / 'r.md'}"

    from src.graph.research_workflow import create_research_app

    app = create_research_app()
    result = app.invoke({
        "messages": [],
        "task": "LangGraph 최신 동향",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "context": "",
        "report_path": "",
        "status": "",
    })

    # 검증: web_search가 호출됨 (자동 쿼리)
    assert mock_web_search.invoke.call_count >= 1

    # 검증: 결과에 검색 내용이 포함됨
    assert result["result"] != ""

    # 검증: 리포트가 저장됨
    assert result["report_path"] != ""


# ── d. Enhance 워크플로우 — applier가 write_pending_action 호출 ──


@patch("src.graph.enhance_workflow.write_pending_action")
@patch("src.agents.reporter.save_report")
@patch("src.agents.reporter.ChatGroq")
@patch("src.agents.critic.ChatGroq")
@patch("src.agents.planner.ChatGroq")
@patch("src.agents.planner.get_recent_reports", return_value="")
@patch("src.agents.enhancer.load_pending_actions")
@patch("src.agents.enhancer.load_analyses")
@patch("src.agents.enhancer.ChatGroq")
def test_enhance_workflow_writes_pending(
    mock_enhancer_llm,
    mock_load_analyses,
    mock_load_pending,
    mock_recent,
    mock_planner_llm,
    mock_critic_llm,
    mock_reporter_llm,
    mock_save_report,
    mock_write_pending,
    tmp_path,
):
    """강화 워크플로우에서 applier_node가 write_pending_action을 호출하는지 확인한다."""
    # threadloom 로더(loader) mock
    mock_load_analyses.invoke.return_value = "## 분석 결과\n테스트 분석 데이터"
    mock_load_pending.invoke.return_value = "대기 항목 없음"

    # Enhancer — 유효한 제안 형식의 응답
    mock_enhancer_llm.return_value.invoke.return_value = _mock_llm_response(
        "## 강화 제안\n\n"
        "### 제안 1: skill — code_review\n"
        "- 근거: 분석 데이터에서 코드 리뷰 패턴 발견\n"
        "- 설명: PR 코드 리뷰 자동화\n"
        "- 구현 사양: 트리거, 입력, 출력\n\n"
    )

    # Planner
    mock_planner_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 목표\n강화 실행 계획"
    )

    # Critic — PASS
    mock_critic_llm.return_value.invoke.return_value = _mock_llm_response(
        "### 판정\nVERDICT: PASS\nFEEDBACK: 없음"
    )

    # Reporter
    mock_reporter_llm.return_value.invoke.return_value = _mock_llm_response(
        "# 강화 리포트"
    )
    mock_save_report.invoke.return_value = f"리포트 저장 완료: {tmp_path / 'e.md'}"

    # write_pending_action mock
    mock_write_pending.invoke.return_value = "강화 항목 저장 완료: test.md"

    from src.graph.enhance_workflow import create_enhance_app

    app = create_enhance_app()
    result = app.invoke({
        "messages": [],
        "task": "시스템 강화 제안",
        "plan": "",
        "result": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": 3,
        "context": "",
        "report_path": "",
        "status": "",
    })

    # 검증: write_pending_action이 호출됨 (applier_node에서 제안을 파싱하여 호출)
    assert mock_write_pending.invoke.call_count >= 1

    # 검증: reporter가 최종 result를 덮어쓰므로 리포트 내용이 들어 있음
    assert result["result"] != ""

    # 검증: 리포트 경로가 설정됨
    assert result["report_path"] != ""
