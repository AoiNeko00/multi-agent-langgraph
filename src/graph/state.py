"""에이전트 공유 상태(state) 정의."""

from __future__ import annotations

from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage

Status = Literal[
    "planning", "executing", "reviewing",
    "enhancing", "reporting", "searching",
    "done", "failed",
]


class AgentState(TypedDict):
    """LangGraph 워크플로우 전체에서 공유되는 상태.

    Attributes:
        messages: 에이전트 간 메시지 히스토리
        task: 사용자 입력 작업
        plan: Planner가 생성한 실행 계획
        result: Executor가 생성한 결과물
        feedback: Critic이 생성한 피드백
        iteration: 현재 루프 반복 횟수
        max_iterations: 최대 루프 반복 횟수
        context: 프로젝트 컨텍스트 (로컬 프로젝트 정보 주입용)
        report_path: 저장된 리포트 파일 경로
        status: 워크플로우 상태
    """

    messages: list[BaseMessage]
    task: str
    plan: str
    result: str
    feedback: str
    iteration: int
    max_iterations: int
    context: str
    report_path: str
    status: Status
