"""멀티에이전트 오케스트레이터 웹 UI."""

import streamlit as st
import json
import time
from pathlib import Path

st.set_page_config(page_title="Multi-Agent Orchestrator", layout="wide")
st.title("🤖 멀티에이전트 오케스트레이터")
st.caption("LangGraph 기반 LLM 오케스트레이션 시스템")

# 사이드바(sidebar) - 모드 선택
mode = st.sidebar.selectbox("워크플로우 모드", ["plan", "research", "enhance"])
max_iter = st.sidebar.slider("최대 반복 횟수", 1, 5, 2)

# 메인 입력(main input)
task = st.text_area("작업 설명", placeholder="예: Python FastAPI 인증 시스템 설계")

if st.button("실행", type="primary"):
    if not task:
        st.warning("작업 설명을 입력하세요.")
    else:
        with st.spinner(f"{mode} 모드 실행 중..."):
            from src.config import init_config
            init_config()
            from src.main import run
            result = run(task, max_iter, mode)

        # 결과(results) 표시
        col1, col2, col3 = st.columns(3)
        col1.metric("상태", result.get("status", ""))
        col2.metric("반복 횟수", result.get("iteration", 0))
        col3.metric("리포트", "저장됨" if result.get("report_path") else "없음")

        if result.get("report_path"):
            st.success(result["report_path"])

        # 탭(tabs)으로 결과 표시
        tab1, tab2, tab3 = st.tabs(["결과", "계획", "피드백"])
        with tab1:
            st.markdown(result.get("result", ""))
        with tab2:
            st.markdown(result.get("plan", "") or "_계획 없음_")
        with tab3:
            st.markdown(result.get("feedback", "") or "_피드백 없음_")

# 성과 지표(metrics) 뷰어
st.sidebar.divider()
st.sidebar.subheader("성과 지표")
metrics_path = Path("data/metrics.json")
if metrics_path.exists():
    metrics = json.loads(metrics_path.read_text())
    if metrics:
        latest = metrics[-1]
        st.sidebar.metric("최근 처리 시간", f"{latest.get('duration_seconds', 0)}초")
        st.sidebar.metric("최근 토큰 사용", f"{latest.get('total_tokens', 0):,}")
        st.sidebar.metric("총 실행 횟수", len(metrics))
else:
    st.sidebar.info("아직 실행 기록이 없습니다")

# 리포트(reports) 뷰어
st.sidebar.divider()
st.sidebar.subheader("생성된 리포트")
reports_dir = Path("data/reports")
if reports_dir.exists():
    reports = sorted(reports_dir.glob("*.md"), reverse=True)[:5]
    for r in reports:
        if st.sidebar.button(r.name, key=r.name):
            st.markdown(r.read_text(encoding="utf-8"))
