# multi-agent-langgraph

LangGraph 기반 멀티에이전트 오케스트레이션 시스템.
threadloom의 4-Phase 자기강화 파이프라인을 멀티에이전트 아키텍처로 재설계했습니다.

## 아키텍처

```
사용자 입력
    │
    ├─ plan ──→ [Planner] → [Executor] → [Critic] ─→ [Reporter] → 리포트.md
    │                ↑                        │
    │                └── FAIL: 피드백 반영 ────┘
    │
    ├─ research → [Researcher] → [Reporter] → [Critic] ─→ 리포트.md
    │                  ↑                          │
    │                  └── FAIL: 재검색 ──────────┘
    │
    └─ enhance ─→ [Enhancer] → [Planner] → [Critic] ─→ [Reporter] → 리포트.md
                       ↑                       │
                       └── FAIL: 재제안 ────────┘
```

### threadloom과의 관계

```
threadloom (눈과 귀)                multi-agent-langgraph (두뇌)
  Threads 포스트 수집    ─────→     enhance: 분석 데이터 → 강화 제안
  패턴 발견·분석                     plan: 마이그레이션 계획 수립
  data/analysis/ 출력               research: 관련 기술 조사
                         ←─────     강화 제안을 data/pending/에 저장
```

## 에이전트 구성

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| **Planner** | qwen3-32b | 작업 → 단계별 계획 분해 |
| **Executor** | qwen3-32b | 계획 → 구체적 결과물 생성 |
| **Critic** | llama-3.3-70b | 4항목 점수제 품질 검증 (완전성/구체성/정확성/명확성) |
| **Researcher** | qwen3-32b | DuckDuckGo 웹 검색 → 정보 수집 |
| **Reporter** | qwen3-32b | 구조화된 리포트 작성 → Markdown 저장 |
| **Enhancer** | qwen3-32b | threadloom 데이터 → 강화 제안 생성 |
| **Memory** | - | 실행 이력 JSON 저장 |

## 빠른 시작

```bash
# 환경 설정
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# .env 파일 생성 (Groq API 키 필수)
cp .env.example .env
# GROQ_API_KEY=gsk_... 입력

# 실행
python -m src.main "Python FastAPI 인증 시스템 설계"                    # plan 모드
python -m src.main --mode research "LangGraph 최신 기능"                # research 모드
python -m src.main --mode enhance "threadloom 기반 강화 계획"           # enhance 모드

# 결과 확인
ls data/reports/
```

## 주요 기능

### Critic 기반 품질 루프
Critic이 결과물을 4가지 기준으로 평가하고, 기준 미달 시 구체적 피드백과 함께 이전 에이전트로 되돌려 보냅니다. 최대 반복 횟수(기본 3회)까지 자동 개선됩니다.

### 프로젝트 컨텍스트 자동 주입
작업 설명에 "threadloom" 등 키워드가 포함되면, threadloom 프로젝트의 아키텍처 요약이 모든 에이전트에 자동 주입됩니다. 로컬 프로젝트에 대한 정확한 분석이 가능합니다.

### 출처 신뢰성
- 출처 날조(hallucination) 방지 규칙 5개 적용
- 검색 결과에 없는 URL 인용 시 FAIL 판정
- 로컬 데이터 기반 리포트는 출처 섹션 자동 생략

## 기술 스택

- **Orchestration**: LangGraph (StateGraph, conditional edges)
- **LLM**: Groq 무료 티어 (비용 $0)
- **Search**: DuckDuckGo (ddgs, 무료)
- **Observability**: LangSmith (선택)
- **Test**: pytest (18개 테스트)

## 프로젝트 구조

```
src/
├── agents/          # 7개 에이전트
├── graph/           # 3개 워크플로우 (plan, research, enhance)
├── tools/           # 검색, 파일 I/O, threadloom 로더
├── config.py        # 모델/토큰 설정
└── main.py          # CLI 진입점
tests/               # 18개 테스트
docs/
└── architecture.md  # 시스템 설계 문서
data/
├── reports/         # 생성된 리포트 저장소
└── execution_history.json
```

## 라이선스

MIT
