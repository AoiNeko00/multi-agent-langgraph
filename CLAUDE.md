# multi-agent-langgraph

## 프로젝트 개요

threadloom의 4-Phase 자기강화 파이프라인을 LangGraph 기반 멀티에이전트 시스템으로 재설계한 프로젝트.
Groq 무료 티어 LLM을 활용하여 비용 $0으로 운영.

## 아키텍처

### 에이전트 구성

```
Planner → Executor → Critic → (조건부 루프)
    ↑                    │
    └────────────────────┘  (Critic 거부 시 재실행)
```

| 에이전트 | 역할 | threadloom 매핑 |
|---------|------|----------------|
| Planner | 목표 분해, 작업 계획 수립 | Phase 2 (분석) |
| Executor | 계획 실행, 결과물 생성 | Phase 3 (강화 생성) |
| Critic | 결과 검증, 품질 게이트 | Phase 3.5 (자동 심사) |
| Enhancer | threadloom 데이터 → 강화 제안 | Phase 3 (강화 생성) |
| Researcher | 웹 검색 정보 수집 | Phase 1 (수집) |
| Reporter | 구조화된 리포트 생성 + 저장 | Phase 4 (적용) |
| Memory | 컨텍스트 관리, 이력 추적 | 전 Phase 공유 상태 |

### LangGraph 워크플로우

```
[입력] → planner → executor → critic → {pass → [출력], fail → planner}
```

- **State**: `AgentState` TypedDict로 전 노드 간 상태 공유
- **Conditional Edge**: Critic 판정에 따라 루프 또는 완료
- **Checkpointing**: LangGraph 내장 체크포인트로 중단/재개 지원

### 디렉토리 구조

```
src/
├── agents/
│   ├── planner.py       # 목표 분해 에이전트
│   ├── executor.py      # 실행 에이전트
│   ├── critic.py        # 결과 검증 에이전트
│   ├── researcher.py    # 웹 검색 리서치 에이전트
│   ├── reporter.py      # 리포트 생성 + md 파일 저장
│   ├── enhancer.py      # threadloom 데이터 기반 강화 제안
│   └── memory.py        # 컨텍스트 관리
├── graph/
│   ├── state.py         # AgentState 정의
│   ├── workflow.py      # 기본 워크플로우 (Planner→Executor→Critic)
│   ├── research_workflow.py  # 리서치 워크플로우 (Researcher→Reporter→Critic)
│   ├── enhance_workflow.py   # 강화 워크플로우 (Enhancer→Planner→Critic→Reporter)
│   └── nodes.py         # 노드 함수 정의
├── tools/
│   ├── search.py        # DuckDuckGo 웹 검색 도구
│   ├── file_io.py       # 리포트 파일 I/O 도구
│   └── threadloom.py    # threadloom 데이터 로더
└── main.py              # 진입점
tests/
docs/
    └── architecture.md  # 시스템 설계 문서
```

## 기술 스택

- **Runtime**: Python 3.11+
- **Orchestration**: LangGraph
- **LLM Provider**: Groq (무료 티어)
  - 모델: `llama-3.1-8b-instant`, `mixtral-8x7b`
  - Rate limit: 분당 30 요청 / 일 14,400 요청
- **Observability**: LangSmith (선택)
- **의존성**: `langgraph`, `langchain-groq`, `langsmith`

## 개발 명령어

```bash
# 환경 설정
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 실행 (기본: 계획 모드)
python -m src.main "작업 설명"

# 실행 (리서치 모드)
python -m src.main --mode research "조사할 주제"

# 실행 (강화 모드 — threadloom 연동)
python -m src.main --mode enhance "강화 주제"

# 테스트
pytest tests/ -v

# 타입 체크
mypy src/

# 린트
ruff check src/
```

## 환경 변수

```
GROQ_API_KEY=         # Groq API 키 (필수)
LANGSMITH_API_KEY=    # LangSmith 키 (선택)
LANGSMITH_PROJECT=    # LangSmith 프로젝트명 (선택)
```

## 코딩 규칙

- 글로벌 CLAUDE.md 규칙 준수
- Python 컨벤션: `snake_case` 함수/변수, `PascalCase` 클래스
- 타입 힌트 필수
- 주석: 한국어 + 영어 용어 병기 (첫 등장 시)
- 함수: 20줄 이하, 매개변수 3개 이하
