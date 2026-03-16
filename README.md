# multi-agent-langgraph

<!-- CI 배지(badge): GitHub username 확정 후 아래 주석을 해제하고 username을 교체하세요 -->
<!-- ![CI](https://github.com/<username>/multi-agent-langgraph/actions/workflows/ci.yml/badge.svg) -->

> LangGraph 기반 LLM 오케스트레이션 + 프롬프트 엔지니어링 + 품질 관리 시스템

## 왜 만들었는가?

[threadloom](https://github.com/) 프로젝트는 Threads 저장 포스트에서 유용한 패턴을 자동 발견하고, AI CLI를 호출하여 skills/agents/rules를 자동 생성·적용하는 4단계 자기강화 파이프라인입니다. 수집부터 적용까지 전 과정이 이미 자동화되어 있습니다.

이 프로젝트는 threadloom의 **자기강화 개념을 LangGraph 멀티에이전트 아키텍처로 재설계**한 것입니다.

| | threadloom | 이 프로젝트 |
|--|-----------|------------|
| 실행 방식 | 순차 파이프라인 (Phase 1→2→3→4) | 그래프 기반 오케스트레이션 (조건부 루프) |
| AI 호출 | subprocess CLI 호출 (2회 고정) | LangGraph + Groq API 직접 호출 (동적) |
| 품질 관리 | Python 규칙 기반 필터 | Critic 에이전트 4항목 점수제 + 자동 재실행 |
| 적용 범위 | Threads 수집 전용 | 범용 (plan/research/enhance) |
| 피드백 루프 | 없음 (단방향) | Critic FAIL → 이전 에이전트로 피드백 전달 |

threadloom의 분석 데이터를 입력으로 받아 **추가 강화 제안을 생성하고, threadloom에 다시 주입**하는 양방향 연동을 지원합니다.

```
threadloom (자기강화 파이프라인)          이 프로젝트 (멀티에이전트 오케스트레이터)
  수집 → 분석 → 생성 → 적용               plan: 작업 계획 수립
  data/analysis/ 출력    ─────→           enhance: 추가 강화 제안 생성
                         ←─────           data/pending/에 강화 항목 저장
                                          research: 관련 기술 조사
```

**비용: $0** (Groq 무료 티어)

---

## 데모: 실제 실행 결과

### Enhance 모드 — threadloom 자기강화

```bash
$ python -m src.main --mode enhance "threadloom 분석 기반 자기강화"
```

```
threadloom 컨텍스트 주입됨
Enhance 모드 실행 중...
╭──────────────── 실행 완료 ────────────────╮
│ 모드: Enhance                              │
│ 상태: done                                 │
│ 반복 횟수: 1                               │
╰────────────────────────────────────────────╯
리포트: data/reports/threadloom_분석_기반_자기강화_20260316_220953.md
```

**실제 결과**: threadloom의 `data/pending/`에 3개 강화 항목 자동 생성됨:

```
data/pending/
├── create_skill_code_governance_heuristic_audit.md   ← NEW
├── add_rule_token_budget_for_skill_descriptions.md   ← NEW
├── create_agent_code_compact_instruction_agent.md    ← NEW
├── (기존 7개 파일...)
```

### Research 모드 — 기술 조사

```bash
$ python -m src.main --mode research "LangGraph 최신 기능과 아키텍처"
```

생성된 리포트에서 발췌:

```markdown
## 주요 발견
| # | 발견 | 근거 |
|---|------|------|
| 1 | LangGraph는 템플릿 기반 AI 애플리케이션 개발 지원 | geeky-gadgets.com |
| 2 | LangChain V2 고급 기능과 통합 | geeky-gadgets.com |
| 3 | Thoughtworks가 가벼운 설계와 모듈성 평가 | thoughtworks.com |

## 출처
1. https://www.geeky-gadgets.com/langgraph-templates/
2. https://www.thoughtworks.com/en-th/radar/languages-and-frameworks/langgraph
3. https://blog.langchain.com/langchain-langgraph-1dot0/
(... 14개 영어권 소스)
```

---

## 기술적 도전과 해결 과정

이 프로젝트를 만들면서 해결한 5가지 핵심 문제입니다.
상세 기록: [docs/decisions.md](docs/decisions.md)

### 1. LLM 출력 품질 문제 → 모델 역할 분리

**문제**: 8B 모델(llama-3.1-8b)로 생성한 리포트에 한자 혼입, 동어반복, 출처 날조 발생.

**해결**: 모델별 역할 분리 + 프롬프트 전면 강화.
- 분석/생성: `qwen3-32b` (한국어 우수)
- 검증: `llama-3.3-70b` (추론 강화)
- 영어 시스템 프롬프트 + `/no_think` + 구조화된 출력 포맷

### 2. 출처 날조 (Hallucination) → 3단계 방어

**문제**: Reporter가 URL 없는 컨텍스트에서 "~에 대한 논문 및 연구자료" 같은 가짜 출처 생성.

**해결**:
1. Reporter: "URL 없으면 출처 섹션 생략" + 날조 금지 규칙 8개
2. Critic: "가짜 출처 → FAIL" 평가 기준 추가
3. enhance 워크플로우: "외부 URL 없음" 명시적 전달

### 3. 검색 결과 중국어만 반환 → 검색 엔진 교체

**문제**: `duckduckgo-search` 패키지가 `region="us-en"`을 무시하고 zhihu.com만 반환.

**시도**: region 파라미터 → 제외 연산자 → 도메인 필터링 → googlesearch-python → 모두 실패.

**해결**: `ddgs` 패키지(후속 버전)로 교체 → 영어권 결과 정상 반환.

### 4. 로컬 프로젝트 "동명이인" 문제 → 컨텍스트 주입

**문제**: "threadloom"을 웹 검색하면 동명의 SaaS 회사가 나옴. 우리 프로젝트와 무관한 리포트 생성.

**해결**: 프로젝트 컨텍스트 자동 주입 + 검색 쿼리를 핵심 기술 키워드로 변환.

### 5. 강화 제안 파싱 실패 → 워크플로우 순서 변경

**문제**: `reporter → applier` 순서에서 Reporter가 Enhancer의 원본 형식을 재작성하여 파싱 불가.

**해결**: `critic → applier → reporter`로 순서 변경. Applier가 원본 제안을 먼저 파싱.

---

## Before / After

### 리포트 품질 비교

| 항목 | Before (8B, 초기) | After (32B/70B, 최종) |
|------|-------------------|----------------------|
| 한자 혼입 | `Chain (链)` 반복 출현 | 0건 |
| 동어반복 | 4개 섹션이 같은 문장 | 각 섹션 독립적 내용 |
| 리포트 길이 | ~20줄 | 70줄+ |
| 출처 | zhihu.com 5개 (중국어) | 14개 영어권 소스 |
| 출처 날조 | "~에 대한 논문 및 연구자료" | 0건 |
| 구체성 | "효율성이 향상" 반복 | "리뷰 시간 30% 절약, 토큰 15% 감소" |
| Critic 평가 | PASS/FAIL만 | 4항목 점수제 + 실행 가능한 피드백 |
| threadloom 인식 | 동명 SaaS 회사를 분석 | 실제 프로젝트 4-Phase 정확 분석 |

### threadloom 적용 비교

| 항목 | Before | After |
|------|--------|-------|
| 결과물 | 터미널 출력만 | `data/reports/`에 마크다운 저장 |
| threadloom 연동 | 없음 | `data/pending/`에 강화 항목 자동 생성 |
| 컨텍스트 | 없음 | 프로젝트 아키텍처 자동 주입 |
| 과거 참조 | 없음 | RAG로 최근 리포트 참조 |

---

## 아키텍처

```
사용자 입력
    │
    ├─ plan ──→ Planner → Executor → Critic ──→ Reporter → 리포트.md
    │              ↑                    │
    │              └── FAIL ────────────┘
    │
    ├─ research → Researcher → Reporter → Critic ──→ 리포트.md
    │                ↑                       │
    │                └── FAIL ───────────────┘
    │
    └─ enhance ─→ Enhancer → Planner → Critic ──→ Applier → Reporter → 리포트.md
                      ↑                   │          │
                      └── FAIL ───────────┘          └→ threadloom/data/pending/
```

### 에이전트 구성

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| **Planner** | qwen3-32b | 작업 → 단계별 계획 분해 + 리스크 분석 |
| **Executor** | qwen3-32b | 계획 → 구체적 결과물 생성 |
| **Critic** | llama-3.3-70b | 4항목 점수제 검증 (완전성/구체성/정확성/명확성) |
| **Researcher** | qwen3-32b | 웹 검색 → 정보 수집 (영어 쿼리 자동 변환) |
| **Reporter** | qwen3-32b | 구조화된 리포트 작성 → Markdown 저장 |
| **Enhancer** | qwen3-32b | threadloom 데이터 → 강화 제안 생성 |
| **Applier** | - | 강화 제안 → threadloom pending 파일 생성 |

---

## 빠른 시작

```bash
# 환경 설정
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# .env 파일 생성 (Groq API 키 필수, https://console.groq.com/keys)
cp .env.example .env

# 실행
python -m src.main "Python FastAPI 인증 시스템 설계"                    # plan
python -m src.main --mode research "LangGraph 최신 기능"                # research
python -m src.main --mode enhance "threadloom 기반 강화 계획"           # enhance
python -m src.main --mode enhance --approve "threadloom 강화"           # enhance + 승인 흐름

# 결과 확인
ls data/reports/
cat data/metrics.json  # 성과 지표 누적 기록

# 웹 UI 실행
streamlit run app.py
```

## LangGraph 고급 기능 활용

### Send API 병렬 검색
```python
# src/graph/parallel_research.py
def fan_out_search(state):
    """3개 검색 쿼리를 병렬로 실행 (fan-out/fan-in 패턴)"""
    return [Send("search_worker", {"query": q}) for q in state["queries"]]
```
`query_generator` → `search_worker` x N (병렬) → `collector` → `reporter` → `critic`

### Human-in-the-Loop (승인 흐름)
```bash
$ python -m src.main --mode enhance --approve "threadloom 강화"
# Applier가 적용 전 interrupt → 사용자 승인/거부 → 승인 시 적용
```

### 성과 측정
```
╭──────────── 성과 지표 ────────────╮
│ 처리 시간: 12.3초                  │
│ LLM 호출: 4회                      │
│ 반복 횟수: 1                       │
╰────────────────────────────────────╯
```
모든 실행 결과가 `data/metrics.json`에 누적 기록됩니다.

---

## 프로젝트 구조

```
src/
├── agents/          # 7개 에이전트 (planner, executor, critic, researcher, reporter, enhancer, memory)
├── graph/           # 4개 워크플로우 (plan, research, enhance, parallel_research)
├── tools/           # 검색, 파일 I/O, threadloom 로더/라이터, 코드 분석, 리포트 이력
├── config.py        # 모델/토큰 설정
├── metrics.py       # 성과 지표 수집/저장
└── main.py          # CLI 진입점 (rich UI + 성과 패널)
tests/               # 54개 테스트 (단위 + 통합 + 파서 + 도구)
docs/
├── architecture.md  # 시스템 설계 문서
└── decisions.md     # 기술 의사결정 기록 (ADR 6개)
```

## 기술 스택

| 항목 | 기술 | 선택 이유 |
|------|------|----------|
| Orchestration | LangGraph | StateGraph + conditional edges + Send API + interrupt |
| LLM | Groq 무료 티어 | 비용 $0, 고성능 모델 접근 가능 |
| 검색 | ddgs (DuckDuckGo) | 무료, API 키 불필요 |
| 코드 분석 | ast (stdlib) | Python 소스 구조 분석, 복잡도 판별 |
| CLI | rich | 실행 상태 + 결과 + 성과 지표 패널 |
| 관찰성 | LangSmith (선택) | 워크플로우 트레이싱 |
| 테스트 | pytest (54개) | 단위 + Mock 통합 + 파서 edge case |

## 이 프로젝트의 범위

**이 프로젝트가 보여주는 것:**
- LangGraph를 활용한 멀티에이전트 워크플로우 설계 (조건부 루프, Send API, interrupt)
- LLM 출력 품질 관리 (hallucination 방지, 모델 역할 분리, 프롬프트 엔지니어링)
- 실제 문제 해결 과정의 기록 (ADR 6개)
- 두 프로젝트 간 데이터 연동 (threadloom ↔ enhance)

**이 프로젝트가 아닌 것:**
- 프로덕션 배포용 시스템이 아닙니다 (단일 사용자 CLI 도구)
- 분산 처리/대규모 데이터 파이프라인이 아닙니다
- 에이전트가 자율적으로 코드를 실행하거나 외부 시스템을 변경하지 않습니다

## 라이선스

MIT
