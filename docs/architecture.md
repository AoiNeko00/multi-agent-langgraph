# 시스템 아키텍처

## 개요

threadloom의 4-Phase 자기강화 파이프라인을 LangGraph 기반 멀티에이전트 시스템으로 재설계.

## threadloom → LangGraph 매핑

| threadloom Phase | LangGraph 에이전트 | 설명 |
|-----------------|-------------------|------|
| Phase 1: 수집 | (외부 입력) | 사용자가 직접 작업을 입력 |
| Phase 2: 분석 | Planner | 작업을 단계별 계획으로 분해 |
| Phase 3: 강화 생성 | Executor | 계획을 실행하여 결과물 생성 |
| Phase 3.5: 자동 심사 | Critic | 결과물 품질 검증 및 판정 |
| Phase 4: 적용 | Memory | 실행 이력 저장 및 컨텍스트 관리 |

## 워크플로우

```
[사용자 입력]
     │
     ▼
┌─────────┐
│ Planner │ ← 작업 분해 + 피드백 반영
└────┬────┘
     │
     ▼
┌──────────┐
│ Executor │ ← 계획 실행 + 결과 생성
└────┬─────┘
     │
     ▼
┌────────┐     FAIL (iteration < max)
│ Critic │ ──────────────────────────→ Planner
└────┬───┘
     │ PASS
     ▼
┌────────┐
│ Memory │ ← 이력 저장
└────┬───┘
     │
     ▼
  [출력]
```

## 상태 관리

`AgentState` TypedDict로 모든 노드 간 상태 공유:

- `task`: 원본 작업
- `plan`: Planner 출력
- `result`: Executor 출력
- `feedback`: Critic 피드백 (루프 시 Planner에 전달)
- `iteration`: 현재 반복 횟수
- `status`: 워크플로우 상태

## 리서치 워크플로우

계획 모드 외에 리서치 자동화 모드를 지원한다.

```
[사용자 입력]
     │
     ▼
┌────────────┐
│ Researcher │ ← DuckDuckGo 웹 검색
└─────┬──────┘
      │
      ▼
┌──────────┐
│ Reporter │ ← 구조화된 리포트 생성
└─────┬────┘
      │
      ▼
┌────────┐     FAIL (iteration < max)
│ Critic │ ──────────────────────────→ Researcher
└────┬───┘
     │ PASS
     ▼
  [리포트 출력]
```

## 도구

| 도구 | 설명 |
|------|------|
| `web_search` | DuckDuckGo 기반 무료 웹 검색 |
| `save_report` | 리포트를 `data/reports/`에 저장 |
| `read_report` | 저장된 리포트 읽기 |

## 설계 결정

1. **Groq 무료 티어 활용**: 비용 $0, 포트폴리오 용도로 충분
2. **조건부 루프**: Critic이 거부하면 Planner/Researcher로 되돌아가 재실행
3. **최대 반복 제한**: 무한 루프 방지 (기본 3회)
4. **실행 이력 저장**: JSON 파일 기반, 향후 벡터 DB 확장 가능
5. **듀얼 워크플로우**: 계획 모드(`plan`)와 리서치 모드(`research`) 지원
6. **LangSmith 트레이싱**: `LANGSMITH_API_KEY` 설정 시 자동 활성화
