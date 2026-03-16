# 시스템 아키텍처

## 개요

threadloom의 4-Phase 자기강화 파이프라인과 연동하는 LangGraph 기반 멀티에이전트 시스템.
threadloom이 수집·분석한 인사이트를 받아 "계획, 조사, 자기강화 제안"을 수행하는 두뇌 역할.

## 3가지 워크플로우

### 1. Plan 모드 (기본)

```
Planner → Executor → Critic ──→ Reporter → 리포트.md
   ↑                    │
   └── FAIL ────────────┘
```

### 2. Research 모드

```
Researcher → Reporter → Critic ──→ 리포트.md
    ↑                       │
    └── FAIL ───────────────┘
```

### 3. Enhance 모드 (threadloom 연동)

```
Enhancer → Planner → Critic ──→ Applier → Reporter → 리포트.md
    ↑                   │          │
    └── FAIL ───────────┘          └→ threadloom/data/pending/
```

## 에이전트 상세

| 에이전트 | 모델 | temperature | max_tokens | 역할 |
|---------|------|-------------|------------|------|
| Planner | qwen3-32b | 0.3 | 40,960 | 작업 분해 + 리스크 분석 + 대안 계획 |
| Executor | qwen3-32b | 0.4 | 40,960 | 계획 실행 + 결과물 생성 |
| Critic | llama-3.3-70b | 0.1 | 32,768 | 4항목 점수제 검증 + hallucination 탐지 |
| Researcher | qwen3-32b | 0.3 | 40,960 | 영어 쿼리 자동 변환 + 다각도 검색 |
| Reporter | qwen3-32b | 0.4 | 40,960 | 리포트 생성 + think 태그 제거 + md 저장 |
| Enhancer | qwen3-32b | 0.3 | 40,960 | threadloom 분석 데이터 → 3개 강화 제안 |
| Applier | - | - | - | 제안 파싱 → threadloom pending 파일 생성 |

## 상태 관리 (AgentState)

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]  # 에이전트 간 메시지 히스토리
    task: str                    # 사용자 입력 작업
    plan: str                    # Planner 출력
    result: str                  # Executor/Researcher 출력
    feedback: str                # Critic 피드백
    iteration: int               # 현재 반복 횟수
    max_iterations: int          # 최대 반복 횟수 (기본 3)
    context: str                 # 프로젝트 컨텍스트 (자동 주입)
    report_path: str             # 저장된 리포트 경로
    status: str                  # planning|executing|reviewing|done|failed
```

## 도구

| 도구 | 파일 | 설명 |
|------|------|------|
| `web_search` | tools/search.py | ddgs 기반 웹 검색 (영어권 우선) |
| `save_report` | tools/file_io.py | data/reports/에 리포트 저장 |
| `load_analyses` | tools/threadloom.py | threadloom 분석 데이터 로드 |
| `load_pending_actions` | tools/threadloom.py | threadloom pending 항목 로드 |
| `load_project_summary` | tools/threadloom.py | 프로젝트 아키텍처 요약 반환 |
| `write_pending_action` | tools/threadloom_writer.py | threadloom pending에 파일 생성 |
| `search_past_reports` | tools/report_history.py | 과거 리포트 키워드 검색 (RAG) |
| `get_recent_reports` | tools/report_history.py | 최근 리포트 요약 반환 |

## 설계 결정

상세: [decisions.md](decisions.md)

1. **Groq 무료 티어**: 비용 $0, 고성능 모델 접근 가능
2. **모델 역할 분리**: 생성(qwen3-32b) / 검증(llama-3.3-70b) 분리
3. **조건부 루프**: Critic FAIL 시 이전 에이전트로 피드백 전달
4. **최대 반복 제한**: 무한 루프 방지 (기본 3회, 도달 시 강제 통과)
5. **컨텍스트 자동 주입**: threadloom 키워드 감지 시 프로젝트 요약 주입
6. **RAG**: Planner가 최근 리포트를 참조하여 중복 방지
7. **출처 신뢰성**: 날조 방지 3단계 방어 (Reporter + Critic + 워크플로우)
