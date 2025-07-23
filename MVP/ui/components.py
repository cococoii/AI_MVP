# # ui/components.py (간단하게 수정)
# import streamlit as st
# import plotly.express as px
# import pandas as pd
# from utils.azure_helper import handle_azure_ai_query

# def render_welcome_message():
#     """환영 메시지 렌더링"""
#     st.markdown("""
#     <div class="success-box">
#         <h3>🎯 청구 이상감지 시스템에 오신 것을 환영합니다!</h3>
#         <p>📂 CSV 파일을 업로드하여 청구 데이터 분석을 시작하세요.</p>
#         <ul>
#             <li>🔍 한국 공휴일 고려 이상 패턴 자동 탐지</li>
#             <li>📈 영업일 수 변화 반영 시각화</li>
#             <li>💬 AI 기반 요약 분석</li>
#         </ul>
#     </div>
#     """, unsafe_allow_html=True)

# def render_upload_section(data_processor, session_mgr=None):
#     """업로드 섹션 렌더링"""
#     from config.settings import MIN_AMOUNT_DEFAULT, MIN_LINES_DEFAULT, CHANGE_THRESHOLD_DEFAULT
    
#     with st.expander("📂 CSV 업로드 및 필터 설정", 
#                      expanded=st.session_state.get('last_dataframe') is None):
#         col1, col_sep, col2 = st.columns([1, 0.02, 2])  # 중간에 얇은 구분선 공간
#         with col1:
#             st.caption("📂 CSV 파일을 업로드하세요")
#             file_upload_key = f"file_uploader_{st.session_state.current_session_id}"
#             uploaded_file = st.file_uploader(
#                     label="", 
#                     key=file_upload_key,
#                     label_visibility="collapsed",
#                     type="csv",
#                     help="청구 데이터 CSV 파일을 선택해주세요"
#                 )
#         with col_sep:
#             # 여기서 전체 배경을 회색으로
#             st.markdown("")
#         with col2:
#             st.caption("**📋 필터 설정**")
#             col1, col2,col3 =st.columns(3)
#             with col1:
#                 min_amount = st.number_input(
#                     "💰 요청 금액 임계값", 
#                     value=MIN_AMOUNT_DEFAULT, 
#                     format="%d",
#                     help="이 금액 이상인 경우만 분석"
#                 )
#             with col2:
#                 min_lines = st.number_input(
#                     "📞 월 회선수 임계값", 
#                     value=MIN_LINES_DEFAULT, 
#                     format="%d",
#                     help="이 회선수 이상인 경우만 분석"
#                 )
#             with col3:
#                 change_threshold = st.slider(
#                     "📊 변화율 임계값 (%)", 
#                     0, 100, CHANGE_THRESHOLD_DEFAULT,
#                     help="이상 패턴 감지 기준"
#                 )
#             data_processor.update_thresholds(min_amount, min_lines, change_threshold)
#         # 필터 설정
#         # st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
#         # st.caption("**📋 필터 설정**")
#         # col1, col2, col3 = st.columns(3)
#         # with col1:
#         #     min_amount = st.number_input(
#         #         "💰 요청 금액 임계값", 
#         #         value=MIN_AMOUNT_DEFAULT, 
#         #         format="%d",
#         #         help="이 금액 이상인 경우만 분석"
#         #     )
#         # with col2:
#         #     min_lines = st.number_input(
#         #         "📞 월 회선수 임계값", 
#         #         value=MIN_LINES_DEFAULT, 
#         #         format="%d",
#         #         help="이 회선수 이상인 경우만 분석"
#         #     )
#         # with col3:
#         #     change_threshold = st.slider(
#         #         "📊 변화율 임계값 (%)", 
#         #         0, 100, CHANGE_THRESHOLD_DEFAULT,
#         #         help="이상 패턴 감지 기준"
#         #     )
        
#         # data_processor.update_thresholds(min_amount, min_lines, change_threshold)
    
#     if uploaded_file:
#         df = data_processor.process_uploaded_file(uploaded_file, session_mgr)
#         return df
    
#     return st.session_state.get('last_dataframe')

# def render_data_analysis(df, data_processor, chat_mgr, session_mgr):
#     """데이터 분석 섹션 렌더링 (간단하게)"""
#     if df is None:
#         st.warning("⚠️ 분석할 데이터가 없습니다.")
#         return
        
#     # 데이터 미리보기
#     st.markdown("##### 📄 데이터 미리보기")
#     with st.container():
#         st.dataframe(df.head(), use_container_width=True)
#         total_rows = len(df)
#         total_cols = len(df.columns)
#         null_count = df.isnull().sum().sum()
#         duplicate_count = df.duplicated().sum()
#         html_table = f"""
#         <table style='width:100%; text-align:center; table-layout:fixed;'>
#         <tr>
#             <td>📊 총 행 수</td>
#             <td>📋 총 열 수</td>
#             <td>❌ 결측값</td>
#             <td>🔄 중복값</td>
#         </tr>
#         <tr>
#             <td><b>{total_rows:,}</b></td>
#             <td><b>{total_cols}</b></td>
#             <td><b>{null_count:,}</b></td>
#             <td><b>{duplicate_count:,}</b></td>
#         </tr>
#         </table>
#         """

#         st.markdown(html_table, unsafe_allow_html=True)
    
#     # 영업일 분석 (간단하게)
#     render_business_days_analysis(df, data_processor)
    
#     # 이상 탐지 결과 (간단하게)
#     render_anomaly_detection(df, data_processor)
    
#     # AI 요약 버튼만
#     render_summary_section(df, chat_mgr, session_mgr)

# def render_business_days_analysis(df, data_processor):
    
#     """영업일 분석 렌더링 (간단하게)"""
#     st.markdown("##### 📅 월별 영업일 수 (한국 공휴일 반영)")
    
#     biz_day_data = data_processor.calculate_business_days(df)

#     if biz_day_data:
#         html = '<table style="border-collapse: collapse; width: 100%; text-align: center;"><tr>'

#         for data in biz_day_data:
#             month = data["월"]
#             total_days = data["총 일수"]
#             weekends = data["주말"]
#             holidays = data["공휴일"]
#             biz_days = data["영업일 수"]
#             delta = data["전월 대비"]

#             # 전월대비 표시용
#             delta_html = ""
#             if delta != "—":
#                 delta_color = "green" if "-" not in delta else "red"
#                 delta_html = f'<div style="font-size:13px; color:{delta_color}; margin-top:2px;">{delta}</div>'
#             else:
#                 # delta 없을 때도 빈 공간을 줘서 높이 맞춤
#                 delta_html = '<div style="font-size:13px; color:transparent; margin-top:2px;">0</div>'

#             # 셀 하나
#             html += '<td style="border: 1px solid #ddd; padding: 10px; width: {}%;">'.format(int(100 / len(biz_day_data)))
#             html += f'<div style="font-size:13px; color:#666;" title="총 {total_days}일 중 주말 {weekends}일, 공휴일 {holidays}일 제외">'
#             html += f'📅 {month} (공휴일 {holidays}일)</div>'
#             html += f'<div style="font-size:24px; font-weight:bold; margin-top:4px;">{biz_days}일</div>'
#             html += delta_html
#             html += '</td>'

#         html += "</tr></table>"
        
#     st.markdown(html, unsafe_allow_html=True)
        
# # def render_anomaly_detection(df, data_processor):
# #     """이상 탐지 결과 렌더링 (간단하게)"""
# #     st.markdown("##### 🚨 이상 탐지 결과")
    
# #     df_flagged = data_processor.detect_anomalies(df)
    
# #     if len(df_flagged) > 0:
# #         st.markdown(f"""
# #         <div class="warning-box">
# #             <div><b>⚠️ {len(df_flagged)}개의 이상 패턴이 발견되었습니다!</b></div>
# #             <span style="font-size:13px">영업일 수 변화를 고려한 후에도 임계값을 초과하는 청구 항목들입니다.</span>
# #         </div>
# #         """, unsafe_allow_html=True)
        
# #         # 이상 데이터 표시 (간단하게)
# #         if '이상_유형' in df_flagged.columns:
# #             display_columns = ['이상_유형', '청구금액_변화율', '회선수_변화율'] + [col for col in df_flagged.columns if col not in ['이상_유형', '청구금액_변화율', '회선수_변화율']]
# #             st.dataframe(df_flagged[display_columns].head(10), use_container_width=True)
# #         else:
# #             st.dataframe(df_flagged.head(10), use_container_width=True)
        
# #         with st.container():
# #             avg_change = df_flagged['청구금액_변화율'].mean()
# #             max_amount = df_flagged['m1요청금액'].max()
# #             html_table = f"""
# #             <table style='width:100%; text-align:center; table-layout:fixed;'>
# #             <tr>
# #                 <td>🔍 탐지된 이상 항목</td>
# #                 <td>📊 평균 청구금액 변화율</td>
# #                 <td>💰 최고 요청금액</td>
# #             </tr>
# #             <tr>
# #                 <td><b>{len(df_flagged):,}</b></td>
# #                 <td><b>{avg_change:.1f}%</b></td>
# #                 <td><b>{max_amount:,.0f}</b></td>
# #             </tr>
# #             </table>
# #             """

# #             st.markdown(html_table, unsafe_allow_html=True)
# #     else:
# #         st.markdown("""
# #         <div class="success-box">
# #             <h4>✅ 영업일 변화를 고려한 결과, 이상 패턴이 발견되지 않았습니다!</h4>
# #             <p>모든 청구 항목이 영업일 수 변화 대비 정상 범위 내에 있습니다.</p>
# #         </div>
# #         """, unsafe_allow_html=True)

# # def render_summary_section(df, chat_mgr, session_mgr):
# #     """AI 요약 섹션 (간단하게 - 버튼만)"""
# #     st.markdown("##### 💻 AI 분석 요약")
# #     col1, col2 = st.columns([1,3])
# #     with col1:
# #         is_processing = st.session_state.get('is_processing', False)
# #         if st.button("📋 AI 요약 생성", disabled=is_processing, key="ai_summary_btn"):
# #             if chat_mgr:
# #                 chat_mgr.generate_summary(df, session_mgr)
# #                 # st.rerun()
# #             else:
# #                 st.error("AI 채팅 매니저를 사용할 수 없습니다.")
# #     with col2:
# #         st.info("💡 AI 요약 버튼 클릭시 : 영업일 변화와 이상 데이터를 포함한 종합 분석 제공")
    

# def render_chat_interface(chat_mgr, session_mgr):
#     """채팅 인터페이스 렌더링 (Azure AI 추가)"""
    
#     # Azure AI import
#     try:
#         azure_ai_available = True
#     except ImportError:
#         azure_ai_available = False
    
#     # 탭으로 나누기
#     if azure_ai_available:
#         tab1, tab2 = st.tabs(["💬 AI 채팅", "☁️ Azure AI 분석"])
#     else:
#         tab1, = st.tabs(["💬 AI 채팅"])
#         tab2 = None
    
#     # ✅ 기존 채팅 기능 (그대로 유지)
#     with tab1:
#         st.markdown("### 💬 AI와 대화하기")
        
#         # 기존 메시지 표시
#         messages = st.session_state.get('messages', [])
#         for msg in messages:
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])
        
#         # 사용자 입력 처리
#         is_processing = st.session_state.get('is_processing', False)
#         if not is_processing:
#             user_question = st.chat_input("💬 궁금한 점을 물어보세요!")
            
#             if user_question:
#                 with st.chat_message("user"):
#                     st.markdown(user_question)  # ✅ 사용자가 질문하자마자 UI에 표시
#                 if chat_mgr:
#                     reply = chat_mgr.handle_user_question(user_question, session_mgr)
#                     with st.chat_message("assistant"):
#                         st.markdown(reply)
#                 else:
#                     st.error("AI 채팅 매니저를 사용할 수 없습니다.")
    
#     # ✅ Azure AI 탭 (새로 추가)
#     if tab2 is not None:
#         with tab2:
#             st.markdown("##### ☁️ Azure 저장 데이터 AI 분석")
#             st.caption("2025년 1월~6월 Azure 저장 데이터를 바탕으로 AI가 분석해드립니다")
            
#             # 추천 질문 버튼들
#             st.markdown("**💡 추천 질문:**")
#             col1, col2, col3 = st.columns(3)
            
#             with col1:
#                 if st.button("📈 **5G 서비스 성장 현황**", 
#                            key="azure_q1",
#                            help="5G 관련 모든 서비스의 성장률과 트렌드를 분석합니다"):
#                     st.session_state['azure_query'] = "5G 관련 서비스들 성장률이 어떻게 변했어? 트렌드 분석해줘"
            
#             with col2:
#                 if st.button("🚗 **차량 IoT 시장 동향**",
#                            key="azure_q2", 
#                            help="차량용 서비스와 IoT 센서의 시장 성과를 비교분석합니다"):
#                     st.session_state['azure_query'] = "차량용 단말 월정액과 IoT 센서 서비스 비교해서 어느게 더 성장했어?"
            
#             with col3:
#                 if st.button("💼 **기업 서비스 수익성**",
#                            key="azure_q3",
#                            help="기업 대상 서비스들의 수익성과 ARPU를 분석합니다"):
#                     st.session_state['azure_query'] = "기업전용 패키지, VPN 서비스, 클라우드 연결 서비스 중에 어떤게 수익성이 가장 좋아?"
#             # 두 번째 줄
#             col4, col5, col6 = st.columns(3)
            
#             with col4:
#                 if st.button("🔍 **신규 출시 서비스 성과**",
#                            key="azure_q4",
#                            help="최근에 출시된 신규 서비스들의 초기 성과를 분석합니다"):
#                     st.session_state['azure_query'] = "2025년 3월 이후에 출시된 신규 서비스들 성과는 어때? 어떤 서비스가 가장 성공적이야?"
            
#             with col5:
#                 if st.button("📊 **LOB별 성과 비교**",
#                            key="azure_q5",
#                            help="모바일, 기업솔루션, IoT 등 사업부별 성과를 비교합니다"):
#                     st.session_state['azure_query'] = "LOB별로 어떤 사업부가 가장 성장했어? 모바일 vs 기업솔루션 vs IoT 비교해줘"
            
#             with col6:
#                 if st.button("💸 **할인 정책 효과 분석**",
#                            key="azure_q6",
#                            help="할인 정책이 각 서비스에 미친 영향을 분석합니다"):
#                     st.session_state['azure_query'] = "할인을 많이 받은 서비스들이 실제로 성장했어? 할인 정책 효과 분석해줘"
            
#             # 🎨 구분선
#             st.markdown("---")

#             # 사용자 직접 입력
#             st.markdown("#### 🤖 **직접 질문하기**")
#             user_question = st.text_input(
#                 "Azure 저장 데이터에 대해 질문하세요:",
#                 placeholder="예: DATA001 서비스가 언제부터 급성장했어? 원인은 뭘까?",
#                 key="azure_ai_input",
#                 help="구체적인 단위서비스 코드(예: DATA001, IOT002)를 언급하면 더 정확한 분석이 가능합니다"
#             )
            
#             # 질문 처리
#             query = user_question or st.session_state.get('azure_query', '')
            
#             if query:
                
#                 # AI 분석 실행
#                 # with st.spinner("🧠 Azure AI가 월별 데이터를 분석하고 있습니다..."):
#                 ai_response = handle_azure_ai_query(query)
                
#                 # 응답 표시
#                 st.markdown("##### 🤖 **AI 분석 결과**")
#                 st.markdown(ai_response)
                
#                 # 세션 정리
#                 if 'azure_query' in st.session_state:
#                     del st.session_state['azure_query']
            
#             # 📚 도움말
#             with st.expander("💡 **효과적인 질문 방법**"):
#                 st.markdown("""
#                 **🎯 구체적인 질문 예시:**
                
#                 **🔍 비교 분석:**
#                 * "5G vs LTE 성과 비교해줘"
#                 * "모바일 vs 기업솔루션 어느쪽이 더 좋아?"

#                 **📈 트렌드 분석:**
#                 * "가장 빠르게 성장한 서비스는?"
#                 * "IoT 서비스들 트렌드 어떻게 변했어?"

#                 **🏆 순위 분석:**
#                 * "수익성 가장 높은 서비스 TOP 10은?"
#                 * "LOB별 성과 순위 알려줘"

#                 **🆕 신규 서비스:**
#                 * "신규 출시된 서비스들 성과는?"
#                 * "2025년 상반기 런칭 서비스 분석해줘"
#                 """)
                
# def generate_smart_summary(df, df_flagged):
#     """스마트 AI 요약 생성"""
    
#     summary_parts = []
    
#     # 기본 현황
#     total_amount = df['청구금액'].sum() if '청구금액' in df.columns else 0
#     total_lines = df['회선수'].sum() if '회선수' in df.columns else 0
    
#     summary_parts.append(f"📊 **전체 현황**: {len(df)}개 서비스, 총 {total_amount/100000000:.1f}억원 ({total_lines/10000:.1f}만 회선)")
    
#     # 이상 항목 분석
#     if len(df_flagged) > 0:
#         anomaly_rate = (len(df_flagged) / len(df)) * 100
#         summary_parts.append(f"🚨 **이상 탐지**: {len(df_flagged)}개 항목 ({anomaly_rate:.1f}%) 에서 이상 패턴 발견")
        
#         # 최고 위험 항목
#         if '청구금액' in df_flagged.columns:
#             top_risk = df_flagged.loc[df_flagged['청구금액'].idxmax()]
#             summary_parts.append(f"⚠️ **최고 위험**: {top_risk.get('청구항목명', 'Unknown')} ({top_risk.get('청구금액', 0)/100000000:.1f}억원)")
#     else:
#         summary_parts.append("✅ **안정성**: 모든 서비스가 정상 범위 내에서 운영 중")
    
#     # LOB별 분석
#     if 'lob명' in df.columns:
#         lob_summary = df.groupby('lob명')['청구금액'].sum().sort_values(ascending=False)
#         top_lob = lob_summary.index[0]
#         summary_parts.append(f"🏆 **최대 사업부**: {top_lob} ({lob_summary.iloc[0]/100000000:.1f}억원)")
    
#     # 추천 액션
#     if len(df_flagged) > 5:
#         summary_parts.append("💡 **추천**: 이상 항목이 많습니다. 상세 분석을 통해 원인을 파악하고 개선 방안을 수립하세요.")
#     elif len(df_flagged) > 0:
#         summary_parts.append("💡 **추천**: 일부 이상 항목을 모니터링하고 필요시 조치하세요.")
#     else:
#         summary_parts.append("💡 **추천**: 안정적인 상태입니다. 성장 기회를 모색하세요.")
    
#     return "\n\n".join(summary_parts)
                
# def render_chart_visualization(df, keyword):
#     """차트 시각화 렌더링"""
#     try:
#         if df is None or len(df) == 0:
#             st.warning("시각화할 데이터가 없습니다.")
#             return
            
#         target_df = df[df[df.columns[0]].astype(str).str.contains(keyword, na=False, case=False)]
#         if not target_df.empty:
#             st.markdown("### 📊 관련 시각화")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 if 'm1월회선수' in target_df.columns:
#                     fig1 = px.line(
#                         target_df, 
#                         x="기준월", 
#                         y="m1월회선수", 
#                         title=f"📈 {keyword} - M1 월 회선수 추이",
#                         color_discrete_sequence=['#667eea']
#                     )
#                     fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
#                     st.plotly_chart(fig1, use_container_width=True)
            
#             with col2:
#                 if 'm1청구금액' in target_df.columns:
#                     fig2 = px.line(
#                         target_df, 
#                         x="기준월", 
#                         y="m1청구금액", 
#                         title=f"💰 {keyword} - M1 청구금액 추이",
#                         color_discrete_sequence=['#764ba2']
#                     )
#                     fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
#                     st.plotly_chart(fig2, use_container_width=True)
                    
#     except Exception as e:
#         st.warning(f"시각화 생성 중 오류: {str(e)}")

# def render_loading_spinner(message="처리 중..."):
#     """로딩 스피너 렌더링"""
#     with st.spinner(f"🤖 {message}"):
#         import time
#         time.sleep(0.1)

# ui/components.py (enhanced_anomaly 연결 버전)
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.azure_helper import handle_azure_ai_query

# 🆕 enhanced_anomaly 함수들 import
from ui.enhanced_anomaly import render_anomaly_detection, render_summary_section

def render_welcome_message():
    """환영 메시지 렌더링"""
    st.markdown("""
    <div class="success-box">
        <h3>🎯 청구 이상감지 시스템에 오신 것을 환영합니다!</h3>
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
        col1, col_sep, col2 = st.columns([1, 0.02, 2])  # 중간에 얇은 구분선 공간
        with col1:
            st.caption("📂 CSV 파일을 업로드하세요")
            file_upload_key = f"file_uploader_{st.session_state.current_session_id}"
            uploaded_file = st.file_uploader(
                    label="", 
                    key=file_upload_key,
                    label_visibility="collapsed",
                    type="csv",
                    help="청구 데이터 CSV 파일을 선택해주세요"
                )
        with col_sep:
            # 여기서 전체 배경을 회색으로
            st.markdown("")
        with col2:
            st.caption("**📋 필터 설정**")
            col1, col2,col3 =st.columns(3)
            with col1:
                min_amount = st.number_input(
                    "💰 요청금액 임계값", 
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
    st.markdown("##### 📄 데이터 미리보기")
    with st.container():
        st.dataframe(df.head(), use_container_width=True)
        total_rows = len(df)
        total_cols = len(df.columns)
        null_count = df.isnull().sum().sum()
        duplicate_count = df.duplicated().sum()
        html_table = f"""
        <table style='width:100%; text-align:center; table-layout:fixed;'>
        <tr>
            <td>📊 총 행 수</td>
            <td>📋 총 열 수</td>
            <td>❌ 결측값</td>
            <td>🔄 중복값</td>
        </tr>
        <tr>
            <td><b>{total_rows:,}</b></td>
            <td><b>{total_cols}</b></td>
            <td><b>{null_count:,}</b></td>
            <td><b>{duplicate_count:,}</b></td>
        </tr>
        </table>
        """

        st.markdown(html_table, unsafe_allow_html=True)
    
    # 영업일 분석 (간단하게)
    render_business_days_analysis(df, data_processor)
    
    # 🚀 향상된 이상 탐지 결과 - enhanced_anomaly.py에서 import
    render_anomaly_detection(df, data_processor)
    
    # 🚀 향상된 AI 요약 섹션 - enhanced_anomaly.py에서 import
    render_summary_section(df, chat_mgr, session_mgr)

def render_business_days_analysis(df, data_processor):
    """영업일 분석 렌더링 (간단하게)"""
    st.markdown("##### 📅 월별 영업일 수 (한국 공휴일 반영)")
    
    biz_day_data = data_processor.calculate_business_days(df)

    if biz_day_data:
        html = '<table style="border-collapse: collapse; width: 100%; text-align: center;"><tr>'

        for data in biz_day_data:
            month = data["월"]
            total_days = data["총 일수"]
            weekends = data["주말"]
            holidays = data["공휴일"]
            biz_days = data["영업일 수"]
            delta = data["전월 대비"]

            # 전월대비 표시용
            delta_html = ""
            if delta != "—":
                delta_color = "green" if "-" not in delta else "red"
                delta_html = f'<div style="font-size:13px; color:{delta_color}; margin-top:2px;">{delta}</div>'
            else:
                # delta 없을 때도 빈 공간을 줘서 높이 맞춤
                delta_html = '<div style="font-size:13px; color:transparent; margin-top:2px;">0</div>'

            # 셀 하나
            html += '<td style="border: 1px solid #ddd; padding: 10px; width: {}%;">'.format(int(100 / len(biz_day_data)))
            html += f'<div style="font-size:13px; color:#666;" title="총 {total_days}일 중 주말 {weekends}일, 공휴일 {holidays}일 제외">'
            html += f'📅 {month} (공휴일 {holidays}일)</div>'
            html += f'<div style="font-size:24px; font-weight:bold; margin-top:4px;">{biz_days}일</div>'
            html += delta_html
            html += '</td>'

        html += "</tr></table>"
        
    st.markdown(html, unsafe_allow_html=True)

# ✅ 기존 주석처리된 함수들은 삭제하고 enhanced_anomaly.py에서 import 사용

def render_chat_interface(chat_mgr, session_mgr):
    """채팅 인터페이스 렌더링 (Azure AI 추가)"""
    
    # Azure AI import
    try:
        azure_ai_available = True
    except ImportError:
        azure_ai_available = False
    
    # 탭으로 나누기
    if azure_ai_available:
        tab1, tab2 = st.tabs(["💬 AI 채팅", "☁️ Azure AI 분석"])
    else:
        tab1, = st.tabs(["💬 AI 채팅"])
        tab2 = None
    
    # ✅ 기존 채팅 기능 (그대로 유지)
    with tab1:
        st.markdown("##### 💬 AI와 대화하기")
        
        # 기존 메시지 표시
        messages = st.session_state.get('messages', [])
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # 사용자 입력 처리
        is_processing = st.session_state.get('is_processing', False)
        if not is_processing:
            user_question = st.chat_input("💬 궁금한 점을 물어보세요!")
            
            if user_question:
                with st.chat_message("user"):
                    st.markdown(user_question)  # ✅ 사용자가 질문하자마자 UI에 표시
                if chat_mgr:
                    reply = chat_mgr.handle_user_question(user_question, session_mgr)
                    with st.chat_message("assistant"):
                        st.markdown(reply)
                else:
                    st.error("AI 채팅 매니저를 사용할 수 없습니다.")
    
    # ✅ Azure AI 탭 (새로 추가)
    if tab2 is not None:
        with tab2:
            st.markdown("##### ☁️ Azure 저장 데이터 AI 분석")
            st.caption("2025년 1월~6월 Azure 저장 데이터를 바탕으로 AI가 분석해드립니다")
            
            # 추천 질문 버튼들
            st.markdown("**💡 추천 질문:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📈 **5G 서비스 성장 현황**", 
                           key="azure_q1",
                           help="5G 관련 모든 서비스의 성장률과 트렌드를 분석합니다"):
                    st.session_state['azure_query'] = "5G 관련 서비스들 성장률이 어떻게 변했어? 트렌드 분석해줘"
            
            with col2:
                if st.button("🚗 **차량 IoT 시장 동향**",
                           key="azure_q2", 
                           help="차량용 서비스와 IoT 센서의 시장 성과를 비교분석합니다"):
                    st.session_state['azure_query'] = "차량용 단말 월정액과 IoT 센서 서비스 비교해서 어느게 더 성장했어?"
            
            with col3:
                if st.button("💼 **기업 서비스 수익성**",
                           key="azure_q3",
                           help="기업 대상 서비스들의 수익성과 ARPU를 분석합니다"):
                    st.session_state['azure_query'] = "기업전용 패키지, VPN 서비스, 클라우드 연결 서비스 중에 어떤게 수익성이 가장 좋아?"
            # 두 번째 줄
            col4, col5, col6 = st.columns(3)
            
            with col4:
                if st.button("🔍 **신규 출시 서비스 성과**",
                           key="azure_q4",
                           help="최근에 출시된 신규 서비스들의 초기 성과를 분석합니다"):
                    st.session_state['azure_query'] = "2025년 3월 이후에 출시된 신규 서비스들 성과는 어때? 어떤 서비스가 가장 성공적이야?"
            
            with col5:
                if st.button("📊 **LOB별 성과 비교**",
                           key="azure_q5",
                           help="모바일, 기업솔루션, IoT 등 사업부별 성과를 비교합니다"):
                    st.session_state['azure_query'] = "LOB별로 어떤 사업부가 가장 성장했어? 모바일 vs 기업솔루션 vs IoT 비교해줘"
            
            with col6:
                if st.button("💸 **할인 정책 효과 분석**",
                           key="azure_q6",
                           help="할인 정책이 각 서비스에 미친 영향을 분석합니다"):
                    st.session_state['azure_query'] = "할인을 많이 받은 서비스들이 실제로 성장했어? 할인 정책 효과 분석해줘"
            
            # 🎨 구분선
            st.markdown("---")

            # 사용자 직접 입력
            st.markdown("#### 🤖 **직접 질문하기**")
            user_question = st.text_input(
                "Azure 저장 데이터에 대해 질문하세요:",
                placeholder="예: DATA001 서비스가 언제부터 급성장했어? 원인은 뭘까?",
                key="azure_ai_input",
                help="구체적인 단위서비스 코드(예: DATA001, IOT002)를 언급하면 더 정확한 분석이 가능합니다"
            )
            
            # 질문 처리
            query = user_question or st.session_state.get('azure_query', '')
            
            if query:
                
                # AI 분석 실행
                # with st.spinner("🧠 Azure AI가 월별 데이터를 분석하고 있습니다..."):
                ai_response = handle_azure_ai_query(query)
                
                # 응답 표시
                st.markdown("##### 🤖 **AI 분석 결과**")
                st.markdown(ai_response)
                
                # 세션 정리
                if 'azure_query' in st.session_state:
                    del st.session_state['azure_query']
            
            # 📚 도움말
            with st.expander("💡 **효과적인 질문 방법**"):
                st.markdown("""
                **🎯 구체적인 질문 예시:**
                
                **🔍 비교 분석:**
                * "5G vs LTE 성과 비교해줘"
                * "모바일 vs 기업솔루션 어느쪽이 더 좋아?"

                **📈 트렌드 분석:**
                * "가장 빠르게 성장한 서비스는?"
                * "IoT 서비스들 트렌드 어떻게 변했어?"

                **🏆 순위 분석:**
                * "수익성 가장 높은 서비스 TOP 10은?"
                * "LOB별 성과 순위 알려줘"

                **🆕 신규 서비스:**
                * "신규 출시된 서비스들 성과는?"
                * "2025년 상반기 런칭 서비스 분석해줘"
                """)
                
def generate_smart_summary(df, df_flagged):
    """스마트 AI 요약 생성"""
    
    summary_parts = []
    
    # 기본 현황
    total_amount = df['청구금액'].sum() if '청구금액' in df.columns else 0
    total_lines = df['회선수'].sum() if '회선수' in df.columns else 0
    
    summary_parts.append(f"📊 **전체 현황**: {len(df)}개 서비스, 총 {total_amount/100000000:.1f}억원 ({total_lines/10000:.1f}만 회선)")
    
    # 이상 항목 분석
    if len(df_flagged) > 0:
        anomaly_rate = (len(df_flagged) / len(df)) * 100
        summary_parts.append(f"🚨 **이상 탐지**: {len(df_flagged)}개 항목 ({anomaly_rate:.1f}%) 에서 이상 패턴 발견")
        
        # 최고 위험 항목
        if '청구금액' in df_flagged.columns:
            top_risk = df_flagged.loc[df_flagged['청구금액'].idxmax()]
            summary_parts.append(f"⚠️ **최고 위험**: {top_risk.get('청구항목명', 'Unknown')} ({top_risk.get('청구금액', 0)/100000000:.1f}억원)")
    else:
        summary_parts.append("✅ **안정성**: 모든 서비스가 정상 범위 내에서 운영 중")
    
    # LOB별 분석
    if 'lob명' in df.columns:
        lob_summary = df.groupby('lob명')['청구금액'].sum().sort_values(ascending=False)
        top_lob = lob_summary.index[0]
        summary_parts.append(f"🏆 **최대 사업부**: {top_lob} ({lob_summary.iloc[0]/100000000:.1f}억원)")
    
    # 추천 액션
    if len(df_flagged) > 5:
        summary_parts.append("💡 **추천**: 이상 항목이 많습니다. 상세 분석을 통해 원인을 파악하고 개선 방안을 수립하세요.")
    elif len(df_flagged) > 0:
        summary_parts.append("💡 **추천**: 일부 이상 항목을 모니터링하고 필요시 조치하세요.")
    else:
        summary_parts.append("💡 **추천**: 안정적인 상태입니다. 성장 기회를 모색하세요.")
    
    return "\n\n".join(summary_parts)
                
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