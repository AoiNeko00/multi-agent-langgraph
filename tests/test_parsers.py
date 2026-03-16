"""제안 파서(proposal parser) 에지 케이스 테스트.

enhance_workflow.py의 _parse_proposals 함수를 다양한 입력 형식으로 검증한다.
"""

from __future__ import annotations

import pytest

from src.agents.critic import parse_scores, judge_verdict
from src.graph.enhance_workflow import _parse_proposals


def test_parse_proposals_standard_format():
    """표준 형식(standard format) '### 제안 1: skill — name'을 파싱하는지 확인한다."""
    text = (
        "### 제안 1: skill — code_audit\n"
        "- 근거: 코드 분석 패턴 발견\n"
        "- 설명: 코드 감사 자동화\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 1
    assert result[0]["action_type"] == "create_skill"
    assert result[0]["name"] == "code_audit"
    assert "코드" in result[0]["content"]


def test_parse_proposals_numbered_format():
    """번호 형식(numbered format) '### 1. rule — name'을 파싱하는지 확인한다."""
    text = (
        "### 1. rule — max_lines\n"
        "- 내용: 함수 최대 20줄 제한\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 1
    assert result[0]["action_type"] == "add_rule"
    assert result[0]["name"] == "max_lines"


def test_parse_proposals_invalid_type_filtered():
    """유효하지 않은 유형(invalid type)은 필터링되는지 확인한다."""
    text = (
        "### 제안 1: 출처 — fake_source\n"
        "- 내용: 이것은 유효하지 않은 유형입니다\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 0


def test_parse_proposals_multiple():
    """여러 제안(multiple proposals)이 올바르게 파싱되는지 확인한다."""
    text = (
        "## 강화 제안\n\n"
        "### 제안 1: skill — code_review\n"
        "- 설명: PR 리뷰 자동화\n\n"
        "### 제안 2: agent — security_auditor\n"
        "- 설명: 보안 감사 에이전트\n\n"
        "### 제안 3: rule — naming_convention\n"
        "- 설명: 네이밍 규칙 강제\n\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 3
    assert result[0]["action_type"] == "create_skill"
    assert result[1]["action_type"] == "create_agent"
    assert result[2]["action_type"] == "add_rule"


def test_parse_proposals_empty():
    """제안이 없는 텍스트(empty)에서 빈 리스트를 반환하는지 확인한다."""
    text = "no proposals here\n별다른 제안 없음"
    result = _parse_proposals(text)

    assert len(result) == 0


def test_parse_proposals_bold_format():
    """볼드/백틱(bold/backtick) 형식도 파싱되는지 확인한다."""
    text = (
        "### 제안 1: **skill** — **auto_test**\n"
        "- 설명: 자동 테스트 생성\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 1
    assert result[0]["action_type"] == "create_skill"
    assert result[0]["name"] == "auto_test"


def test_parse_proposals_reasoning_rule_type():
    """reasoning_rule 유형이 add_rule로 매핑되는지 확인한다."""
    text = (
        "### 제안 1: reasoning_rule — think_before_code\n"
        "- 설명: 코딩 전 사고 규칙\n"
    )
    result = _parse_proposals(text)

    assert len(result) == 1
    assert result[0]["action_type"] == "add_rule"


def test_parse_proposals_max_five():
    """최대 5개까지만 파싱되는지 확인한다."""
    lines = []
    for i in range(8):
        lines.append(f"### 제안 {i + 1}: skill — skill_{i}\n- 설명: 설명 {i}\n\n")
    text = "".join(lines)

    result = _parse_proposals(text)

    assert len(result) == 5


# --- Critic 점수 파싱(score parsing) 테스트 ---


def test_parse_scores_standard():
    """표준 테이블 형식에서 점수를 파싱하는지 확인한다."""
    content = (
        "| 기준 | 점수 (1-5) | 근거 |\n"
        "|------|-----------|------|\n"
        "| 완전성 | 4 | 좋음 |\n"
        "| 구체성 | 3 | 보통 |\n"
        "| 정확성 | 5 | 우수 |\n"
        "| 명확성 | 4 | 좋음 |\n"
    )
    scores = parse_scores(content)
    assert scores == {"완전성": 4, "구체성": 3, "정확성": 5, "명확성": 4}


def test_parse_scores_missing_criterion():
    """누락된 기준은 기본값 3을 사용하는지 확인한다."""
    content = "| 완전성 | 5 | 우수 |\n| 구체성 | 4 | 좋음 |\n"
    scores = parse_scores(content)
    assert scores["완전성"] == 5
    assert scores["정확성"] == 3  # 기본값(default)


def test_judge_verdict_pass():
    """평균 3.5 이상이면 PASS인지 확인한다."""
    scores = {"완전성": 4, "구체성": 4, "정확성": 3, "명확성": 4}
    assert judge_verdict(scores) is True


def test_judge_verdict_fail():
    """평균 3.5 미만이면 FAIL인지 확인한다."""
    scores = {"완전성": 2, "구체성": 3, "정확성": 3, "명확성": 3}
    assert judge_verdict(scores) is False


def test_judge_verdict_boundary():
    """정확히 3.5일 때 PASS인지 확인한다."""
    scores = {"완전성": 3, "구체성": 4, "정확성": 3, "명확성": 4}
    assert judge_verdict(scores) is True
