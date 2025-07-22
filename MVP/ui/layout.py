# ui/layout.py (깔끔하게 정리)
import streamlit as st
import datetime

def render_header():
    """메인 헤더 렌더링"""
    st.markdown("""
    <div class="main-header">
        <h1>💼 청구 Copilot - 이상 감지 + 요약 분석</h1>
        <p style="margin: 0; opacity: 0.9;">AI 기반 청구 데이터 분석 및 이상 패턴 탐지 시스템</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(session_mgr, chat_mgr):
    """사이드바 렌더링"""
    with st.sidebar:
        st.markdown("### 💬 채팅 메뉴")
        
        # 새 채팅 버튼
        if st.button("🆕 새 채팅 시작", key="new_chat", help="새로운 채팅을 시작합니다"):
            session_mgr.start_new_chat()
            st.rerun()

        # 이전 대화 기록
        render_chat_history(chat_mgr)
        
        # 사이드바 정보 섹션 (간단하게)
        render_sidebar_info()

def render_chat_history(chat_mgr):
    """채팅 히스토리 렌더링"""
    if st.session_state.chat_sessions:
        st.markdown("### 📁 이전 대화 기록")
        for sid, session in sorted(st.session_state.chat_sessions.items(), 
                                 key=lambda x: x[1]['timestamp'], reverse=True):
            timestamp = session['timestamp'].strftime("%m/%d %H:%M")
            file_name = session.get('file', 'No File')
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📂 {timestamp}", key=f"load_{sid}", help=f"파일: {file_name}"):
                    chat_mgr.load_session(sid, session)
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{sid}", help="삭제"):
                    del st.session_state.chat_sessions[sid]
                    st.rerun()

def render_sidebar_info():
    """사이드바 정보 섹션 (간단하게)"""
    st.markdown("---")
    st.markdown("### 📊 분석 정보")
    
    if st.session_state.last_dataframe is not None:
        df_info = st.session_state.last_dataframe
        st.metric("총 데이터 수", len(df_info))
        st.metric("컬럼 수", len(df_info.columns))
        if st.session_state.last_file:
            st.info(f"📄 현재 파일: {st.session_state.last_file}")
    else:
        st.info("📂 데이터를 업로드해주세요")
    
    # 영업일 정보 (간단하게)
    render_business_day_summary()
    
    # 도움말 (간단하게)
    st.markdown("---")
    st.markdown("### ❓ 사용법")
    with st.expander("💡 도움말"):
        st.markdown("""
        1. **CSV 업로드** → 청구 데이터 파일 선택
        2. **AI 요약 생성** → 영업일 고려 분석
        3. **채팅** → 궁금한 점 질문
        """)

def render_business_day_summary():
    """영업일 요약 정보 (간단하게)"""
    detailed_biz_days = st.session_state.get('detailed_biz_days', {})
    
    if detailed_biz_days:
        st.markdown("---")
        st.markdown("### 📅 이번 달 영업일")
        
        # 최신 월 정보만 간단히 표시
        latest_month = max(detailed_biz_days.keys()) if detailed_biz_days else None
        
        if latest_month:
            info = detailed_biz_days[latest_month]
            
            st.metric(
                label=f"{latest_month}",
                value=f"{info['business_days']}일",
                help=f"총 {info['total_days']}일 중 영업일"
            )
            
            # 공휴일이 있으면 표시
            if info['holiday_list']:
                st.caption("🎌 " + ", ".join([h['name'] for h in info['holiday_list']]))

def render_footer():
    """푸터 렌더링"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #666; font-size: 0.9em;">
        💼 청구 Copilot | AI 기반 청구 데이터 분석 시스템
    </div>
    """, unsafe_allow_html=True)