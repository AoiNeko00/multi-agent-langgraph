# 기술 의사결정 기록 (Architecture Decision Records)

개발 과정에서 마주친 기술적 문제와 해결 과정을 기록합니다.

---

## ADR-1: 왜 Groq 무료 티어인가?

**상황**: 멀티에이전트 시스템은 에이전트 수 x 반복 횟수만큼 LLM을 호출합니다. 3개 워크플로우 x 평균 4개 에이전트 x 최대 3회 반복 = 요청당 최대 36회 호출. 상용 API를 사용하면 비용이 빠르게 증가합니다.

**결정**: Groq 무료 티어를 사용합니다.
- 크레딧카드 없이 가입 가능
- 분당 요청 제한만 있고, 토큰당 과금 없음
- qwen3-32b, llama-3.3-70b 등 고성능 모델 무료 사용 가능

**트레이드오프**:
- Rate limit으로 인해 3개 모드 병렬 실행 불가 (순차 실행 필요)
- 무료 티어 정책 변경 리스크 존재

---

## ADR-2: 왜 llama-3.1-8b에서 qwen3-32b로 모델을 변경했는가?

**상황**: 초기 8B 모델로 생성한 리포트에 심각한 품질 문제 발생.

**발견된 문제**:
1. **한자 혼입** — `Chain (链)` 처럼 중국어 문자가 한국어 응답에 섞임
2. **동어반복** — 개요/상세분석/결론이 같은 문장 복사
3. **정보량 부재** — LangGraph의 StateGraph, conditional edges 등 핵심 기능 언급 없음
4. **출처 날조** — "에이전트 skill 강화 계획 수립에 대한 논문 및 연구자료" (존재하지 않는 출처)

**결정**: 모델별 역할 분리.
- **qwen3-32b** → 분석/생성 (한국어 우수, 40,960 max tokens)
- **llama-3.3-70b** → 검증 (최고 추론 품질, 32,768 max tokens)

**결과**: 한자 혼입 0건, 동어반복 0건, 리포트 길이 20줄 → 70줄+

---

## ADR-3: DuckDuckGo에서 ddgs로 검색 엔진을 변경한 이유

**상황**: `duckduckgo-search` 패키지로 `region="us-en"` 설정해도 모든 검색 결과가 중국어 사이트(zhihu.com)만 반환됨.

**시도한 해결책**:
1. `region="us-en"` 파라미터 → 효과 없음
2. `-site:zhihu.com` 제외 연산자 → DuckDuckGo API가 무시
3. 후처리 필터링 (차단 도메인 리스트) → 전체 결과가 zhihu라서 필터 후 0건
4. `googlesearch-python` 패키지 → 네트워크 환경에서 0건 반환
5. **`ddgs` 패키지** (duckduckgo-search 후속) → 영어권 결과 정상 반환

**결정**: `duckduckgo-search` → `ddgs` 패키지로 교체.

**결과**: 출처가 zhihu.com 5개 → dev.to, medium.com, realpython.com 등 영어권 14개

---

## ADR-4: 출처 날조(Hallucination)를 어떻게 방지했는가?

**상황**: Reporter가 출처 섹션을 채우기 위해 존재하지 않는 URL이나 "~에 대한 논문"을 날조.

**근본 원인 분석**:
- Reporter 프롬프트에 `## 출처` 섹션이 필수 포맷으로 정의됨
- 실제 URL 데이터가 컨텍스트에 없으면 LLM이 채우려고 날조

**해결 3단계**:
1. **Reporter 프롬프트**: "URL 없으면 출처 섹션 자체를 생략하라" + 날조 금지 규칙 5개 추가
2. **Critic 프롬프트**: "가짜 출처 발견 시 FAIL" 평가 기준 추가
3. **enhance 워크플로우**: Reporter에 "이 데이터는 로컬 파일이므로 외부 URL 없음" 명시적 전달

**결과**: 출처 날조 0건. enhance 리포트는 출처 섹션 대신 "이 리포트는 수집된 정보에만 기반합니다" 표기.

---

## ADR-5: 로컬 프로젝트 리서치 시 "동명이인 문제"를 어떻게 해결했는가?

**상황**: "threadloom"을 웹 검색하면 동명의 SaaS 회사(포럼 데이터 분석)가 나옴. 실제 threadloom은 Threads 저장 포스트 기반 로컬 AI 자기강화 도구.

**발견 과정**:
- Research 모드로 "threadloom AI self-enhancement pipeline"을 검색
- LinkedIn의 Threadloom 회사 프로필이 반환됨 ("1,000개 포럼, 1억 명 사용자 매핑")
- 완전히 다른 프로젝트에 대한 리포트가 생성됨

**해결 2단계**:
1. **프로젝트 컨텍스트 자동 주입**: 작업에 "threadloom" 키워드 감지 시 `load_project_summary()`로 실제 아키텍처 요약을 모든 에이전트에 주입
2. **Researcher 검색 쿼리 변환**: 프로젝트명 대신 핵심 기술 키워드로 검색 ("AI self-improvement autonomous agent pipeline", "Playwright web scraping" 등)

**결과**: 리서치 리포트가 실제 threadloom의 4-Phase 파이프라인을 정확히 분석.

---

## ADR-6: Enhance 모드에서 threadloom에 실제 적용하는 순서를 왜 변경했는가?

**상황**: 초기 설계는 `reporter → applier` 순서. Applier가 Reporter의 리포트를 파싱하여 강화 항목을 추출하려 했으나, Reporter가 Enhancer의 원본 형식을 재작성하여 파싱 실패.

**문제**: Enhancer 출력: `### 제안 1: skill — code_audit` → Reporter가 `### 1. 코드 감사 필요성`으로 변환 → Applier가 유형(skill)을 추출 불가.

**결정**: 순서를 `critic → applier → reporter`로 변경.
- Applier가 Enhancer의 원본 제안(result)을 먼저 파싱
- 그 후 Reporter가 리포트를 생성

**결과**: 파싱 정확도 0% → 100%. threadloom pending에 3개 파일 자동 생성 확인.
