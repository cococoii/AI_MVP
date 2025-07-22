# ui/components.py (간단하게 수정)
import streamlit as st
import plotly.express as px
import pandas as pd

def render_welcome_message():
    """환영 메시지 렌더링"""
    st.markdown("""
    <div class="success-box">
        <h3>🎯 청구 Copilot에 오신 것을 환영합니다!</h3>
        <p>📂 CSV 파일을 업로드하여 청구 데이터 분석을 시작하세요.</p>
        <ul>
            <li>🔍 한국 공휴일 고려 이상 패턴 자동 탐지</li>
            <li>📈 영업일 수 변화 반영 시각화</li>
            <li>💬 AI 기반 요약 분석</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_upload_section(data_processor, session_mgr=None):
    """업로드 섹션 렌더링"""
    from config.settings import MIN_AMOUNT_DEFAULT, MIN_LINES_DEFAULT, CHANGE_THRESHOLD_DEFAULT
    
    with st.expander("📂 CSV 업로드 및 필터 설정", 
                     expanded=st.session_state.get('last_dataframe') is None):
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "CSV 파일을 업로드하세요", 
                type="csv",
                help="청구 데이터 CSV 파일을 선택해주세요"
            )
        
        with col2:
            st.markdown("### 📋 필터 설정")
        
        # 필터 설정
        col1, col2, col3 = st.columns(3)
        with col1:
            min_amount = st.number_input(
                "💰 요청 금액 임계값", 
                value=MIN_AMOUNT_DEFAULT, 
                format="%d",
                help="이 금액 이상인 경우만 분석"
            )
        with col2:
            min_lines = st.number_input(
                "📞 월 회선수 임계값", 
                value=MIN_LINES_DEFAULT, 
                format="%d",
                help="이 회선수 이상인 경우만 분석"
            )
        with col3:
            change_threshold = st.slider(
                "📊 변화율 임계값 (%)", 
                0, 100, CHANGE_THRESHOLD_DEFAULT,
                help="이상 패턴 감지 기준"
            )
        
        data_processor.update_thresholds(min_amount, min_lines, change_threshold)
    
    if uploaded_file:
        df = data_processor.process_uploaded_file(uploaded_file, session_mgr)
        return df
    
    return st.session_state.get('last_dataframe')

def render_data_analysis(df, data_processor, chat_mgr, session_mgr):
    """데이터 분석 섹션 렌더링 (간단하게)"""
    if df is None:
        st.warning("⚠️ 분석할 데이터가 없습니다.")
        return
        
    # 데이터 미리보기
    st.markdown("### 📄 데이터 미리보기")
    with st.container():
        st.dataframe(df.head(), use_container_width=True)
        
        # 데이터 기본 정보
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 총 행 수", len(df))
        with col2:
            st.metric("📋 총 열 수", len(df.columns))
        with col3:
            null_count = df.isnull().sum().sum()
            st.metric("❌ 결측값", null_count)
        with col4:
            duplicate_count = df.duplicated().sum()
            st.metric("🔄 중복값", duplicate_count)
    
    # 영업일 분석 (간단하게)
    render_business_days_analysis(df, data_processor)
    
    # 이상 탐지 결과 (간단하게)
    render_anomaly_detection(df, data_processor)
    
    # AI 요약 버튼만
    render_summary_section(df, chat_mgr, session_mgr)

def render_business_days_analysis(df, data_processor):
    """영업일 분석 렌더링 (간단하게)"""
    st.markdown("### 📅 월별 영업일 수 (한국 공휴일 반영)")
    
    biz_day_data = data_processor.calculate_business_days(df)
    
    if biz_day_data:
        # 간단한 메트릭만 표시
        cols = st.columns(len(biz_day_data))
        for i, data in enumerate(biz_day_data):
            with cols[i]:
                delta_text = data["전월 대비"] if data["전월 대비"] != "—" else None
                holiday_info = f" (공휴일 {data['공휴일']}일)" if data["공휴일"] > 0 else ""
                
                st.metric(
                    label=f"📅 {data['월']}{holiday_info}",
                    value=f"{data['영업일 수']}일",
                    delta=delta_text,
                    help=f"총 {data['총 일수']}일 중 주말 {data['주말']}일, 공휴일 {data['공휴일']}일 제외"
                )

def render_anomaly_detection(df, data_processor):
    """이상 탐지 결과 렌더링 (간단하게)"""
    st.markdown("### 🚨 이상 탐지 결과")
    
    df_flagged = data_processor.detect_anomalies(df)
    
    if len(df_flagged) > 0:
        st.markdown(f"""
        <div class="warning-box">
            <h4>⚠️ {len(df_flagged)}개의 이상 패턴이 발견되었습니다!</h4>
            <p>영업일 수 변화를 고려한 후에도 임계값을 초과하는 청구 항목들입니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 이상 데이터 표시 (간단하게)
        if '이상_유형' in df_flagged.columns:
            display_columns = ['이상_유형', '청구금액_변화율', '회선수_변화율'] + [col for col in df_flagged.columns if col not in ['이상_유형', '청구금액_변화율', '회선수_변화율']]
            st.dataframe(df_flagged[display_columns].head(10), use_container_width=True)
        else:
            st.dataframe(df_flagged.head(10), use_container_width=True)
        
        # 간단한 통계
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔍 탐지된 이상 항목", len(df_flagged))
        with col2:
            if '청구금액_변화율' in df_flagged.columns:
                avg_change = df_flagged['청구금액_변화율'].mean()
                st.metric("📊 평균 청구금액 변화율", f"{avg_change:.1f}%")
        with col3:
            if 'm1요청금액' in df_flagged.columns:
                max_amount = df_flagged['m1요청금액'].max()
                st.metric("💰 최고 요청금액", f"{max_amount:,.0f}원")
    else:
        st.markdown("""
        <div class="success-box">
            <h4>✅ 영업일 변화를 고려한 결과, 이상 패턴이 발견되지 않았습니다!</h4>
            <p>모든 청구 항목이 영업일 수 변화 대비 정상 범위 내에 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)

def render_summary_section(df, chat_mgr, session_mgr):
    """AI 요약 섹션 (간단하게 - 버튼만)"""
    st.markdown("### 🤖 AI 분석 요약")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        is_processing = st.session_state.get('is_processing', False)
        if st.button("📋 AI 요약 생성", disabled=is_processing, key="ai_summary_btn"):
            if chat_mgr:
                chat_mgr.generate_summary(df, session_mgr)
                st.rerun()
            else:
                st.error("AI 채팅 매니저를 사용할 수 없습니다.")
    
    with col2:
        st.info("💡 AI 요약: 영업일 변화와 이상 데이터를 포함한 종합 분석 제공")

def render_chat_interface(chat_mgr, session_mgr):
    """채팅 인터페이스 렌더링 (추천 질문 제거)"""
    st.markdown("### 💬 AI와 대화하기")
    
    # 기존 메시지 표시
    messages = st.session_state.get('messages', [])
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 사용자 입력 처리 (추천 질문 제거)
    is_processing = st.session_state.get('is_processing', False)
    if not is_processing:
        user_question = st.chat_input("💬 궁금한 점을 물어보세요!")
        
        if user_question:
            if chat_mgr:
                chat_mgr.handle_user_question(user_question, session_mgr)
            else:
                st.error("AI 채팅 매니저를 사용할 수 없습니다.")
    else:
        st.info("🤖 AI가 이전 질문을 처리하고 있습니다. 잠시만 기다려주세요...")

def render_chart_visualization(df, keyword):
    """차트 시각화 렌더링"""
    try:
        if df is None or len(df) == 0:
            st.warning("시각화할 데이터가 없습니다.")
            return
            
        target_df = df[df[df.columns[0]].astype(str).str.contains(keyword, na=False, case=False)]
        if not target_df.empty:
            st.markdown("### 📊 관련 시각화")
            
            col1, col2 = st.columns(2)
            with col1:
                if 'm1월회선수' in target_df.columns:
                    fig1 = px.line(
                        target_df, 
                        x="기준월", 
                        y="m1월회선수", 
                        title=f"📈 {keyword} - M1 월 회선수 추이",
                        color_discrete_sequence=['#667eea']
                    )
                    fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                if 'm1청구금액' in target_df.columns:
                    fig2 = px.line(
                        target_df, 
                        x="기준월", 
                        y="m1청구금액", 
                        title=f"💰 {keyword} - M1 청구금액 추이",
                        color_discrete_sequence=['#764ba2']
                    )
                    fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig2, use_container_width=True)
                    
    except Exception as e:
        st.warning(f"시각화 생성 중 오류: {str(e)}")

def render_loading_spinner(message="처리 중..."):
    """로딩 스피너 렌더링"""
    with st.spinner(f"🤖 {message}"):
        import time
        time.sleep(0.1)