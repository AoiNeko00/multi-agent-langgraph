"""threadloom 데이터 로더(loader) 도구.

threadloom 프로젝트의 분석 결과 및 대기 중인 강화 항목을 읽는다.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from langchain_core.tools import tool

# threadloom 프로젝트 경로 — 환경 변수(THREADLOOM_PATH)로 오버라이드 가능
THREADLOOM_PATH = Path(
    os.getenv("THREADLOOM_PATH", Path.home() / "Documents" / "flutter" / "threadloom")
)


def _read_frontmatter_and_body(filepath: Path) -> dict:
    """YAML frontmatter와 본문을 분리하여 반환한다."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {"frontmatter": "", "body": text, "filename": filepath.name}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": "", "body": text, "filename": filepath.name}

    return {
        "frontmatter": parts[1].strip(),
        "body": parts[2].strip(),
        "filename": filepath.name,
    }


_PROJECT_SUMMARY = """## threadloom 프로젝트 요약

threadloom은 Threads 저장 포스트에서 유용한 패턴을 자동 발견하고,
AI가 스스로 자신의 skills, agents, rules를 생성·수정하는 자기강화 도구이다.

### 4-Phase 파이프라인 (AI 호출 총 2회)
- **Phase 1 (수집)**: Python + Playwright 헤드리스 브라우저로 Threads.com 저장 포스트 스크래핑. 본문 + self-reply 병합, 외부 링크 크롤링, checkpoint 기반 중단/재개.
- **Phase 2 (분석)**: AI CLI 1회 호출. 전체 배치를 한번에 분석 — 분류, 태그, 요약, 유용성 점수(0.0~1.0), 강화 유형(skill/agent/rule/none) 판정.
- **Phase 3 (강화 생성)**: AI CLI 1회 호출. skill/agent/rule 초안을 마크다운으로 생성. 기존 파일과 의미적 중복 검사.
- **Phase 3.5 (자동 심사)**: Python 규칙 기반 필터. 기술 스택 관련성, 유용성 점수 임계값(0.7), 중복 검사. 거부 항목은 data/rejected/로 이동.
- **Phase 4 (적용)**: 승인 또는 자동 적용. 백업 생성 → 파일 생성/수정 → CLAUDE.md 규칙 추가. 이력 기록.

### 기술 스택
- Python, Playwright (수집), subprocess AI CLI 호출 (Claude/Codex/Gemini)
- 마크다운 기반 중간 결과 저장 (data/raw/, data/analysis/, data/pending/)
- YAML frontmatter로 메타데이터 관리

### 에러 처리
- Phase 2 실패: _fallback_analysis() → 모든 포스트를 기타로 처리
- Phase 3 실패: raw_fallback 파일로 저장 → 수동 검토
- Rate limit: exponential backoff (10, 20, 40초) 자동 재시도
- 동시 실행 방지: data/.lock 파일 기반 실행 잠금
- checkpoint 저장: 수집 중 비정상 종료 시 이어 재개

### 핵심 엔티티
- ThreadPost: post_id, author, text, url, saved_at, media_urls, replies, link_contents
- PendingAction: action_type(create_skill/create_agent/add_rule), name, target, content, source_posts
"""


def load_project_summary() -> str:
    """threadloom 프로젝트의 아키텍처 요약을 반환한다."""
    return _PROJECT_SUMMARY


@tool
def load_analyses(limit: int = 3) -> str:
    """threadloom의 최신 분석 결과를 로드한다.

    Args:
        limit: 로드할 최대 파일 수 (기본: 3, 최신순)

    Returns:
        분석 결과 마크다운 문자열
    """
    analysis_dir = THREADLOOM_PATH / "data" / "analysis"
    if not analysis_dir.exists():
        return f"분석 디렉토리를 찾을 수 없습니다: {analysis_dir}"

    files = sorted(analysis_dir.glob("*.md"), reverse=True)[:limit]
    if not files:
        return "분석 파일이 없습니다."

    sections = []
    for f in files:
        parsed = _read_frontmatter_and_body(f)
        # Enhancement Proposal Summary 테이블만 추출하여 토큰 절약
        summary = _extract_summary(parsed["body"])
        sections.append(
            f"### {parsed['filename']}\n"
            f"{parsed['frontmatter']}\n\n"
            f"{summary}"
        )

    return f"## threadloom 분석 결과 ({len(files)}개)\n\n" + "\n\n---\n\n".join(sections)


def _extract_summary(body: str) -> str:
    """분석 본문에서 Enhancement Proposal Summary 섹션을 추출한다."""
    # "Enhancement Proposal Summary" 또는 유사 헤더 이후 내용 추출
    match = re.search(
        r"(##\s*Enhancement Proposal Summary.*?)(?=\n##\s|\Z)",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()[:1500]

    # fallback: 본문 앞부분만 반환
    return body[:800]


@tool
def load_pending_actions() -> str:
    """threadloom의 대기 중인 강화 항목을 로드한다.

    Returns:
        대기 중인 강화 항목 마크다운 문자열
    """
    pending_dir = THREADLOOM_PATH / "data" / "pending"
    if not pending_dir.exists():
        return f"pending 디렉토리를 찾을 수 없습니다: {pending_dir}"

    files = sorted(pending_dir.glob("*.md"))
    if not files:
        return "대기 중인 강화 항목이 없습니다."

    sections = []
    for f in files:
        parsed = _read_frontmatter_and_body(f)
        # frontmatter(메타데이터)만 추출하여 중복 확인용으로 제공
        sections.append(
            f"- **{parsed['filename']}**: {parsed['frontmatter']}"
        )

    return f"## 대기 중인 강화 항목 ({len(files)}개)\n\n" + "\n".join(sections)
