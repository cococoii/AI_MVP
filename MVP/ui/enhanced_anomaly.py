# enhanced_anomaly.py
# 향상된 이상 탐지 결과 - 클릭 & 필터링 기능

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def render_anomaly_detection(df, data_processor):
    """향상된 이상 탐지 결과 렌더링 - 클릭 & 필터링 기능 포함"""
    st.markdown("##### 🚨 이상 탐지 결과")
    
    df_flagged = data_processor.detect_anomalies(df)
    
    if len(df_flagged) > 0:
        # 🎯 필터링 옵션
        # with st.expander("🔍 필터링 옵션", expanded=False):
        #     col1, col2 = st.columns(2)
            
        #     # 이상 유형 필터
        #     with col1:
        #         anomaly_types = ['전체'] + list(df_flagged['이상_유형'].unique()) if '이상_유형' in df_flagged.columns else ['전체']
        #         selected_anomaly = st.selectbox("이상 유형", anomaly_types, key="anomaly_filter")
            
        #     # LOB 필터
        #     with col2:
        #         lobs = ['전체'] + list(df_flagged['lob'].unique()) if 'lob' in df_flagged.columns else ['전체']
        #         selected_lob = st.selectbox("LOB", lobs, key="lob_filter")
            
            # 청구금액 변화율 범위
            # with col3:
            #     if '청구금액_변화율' in df_flagged.columns:
            #         min_change = float(df_flagged['청구금액_변화율'].min())
            #         max_change = float(df_flagged['청구금액_변화율'].max())
            #         change_range = st.slider(
            #             "청구금액 변화율 (%)", 
            #             min_change, max_change, 
            #             (min_change, max_change),
            #             key="change_filter"
            #         )
            #     else:
            #         change_range = None
            
            # # 회선수 변화율 범위
            # with col4:
            #     if '회선수_변화율' in df_flagged.columns:
            #         min_line_change = float(df_flagged['회선수_변화율'].min())
            #         max_line_change = float(df_flagged['회선수_변화율'].max())
            #         line_change_range = st.slider(
            #             "회선수 변화율 (%)", 
            #             min_line_change, max_line_change, 
            #             (min_line_change, max_line_change),
            #             key="line_change_filter"
            #         )
            #     else:
            #         line_change_range = None
        
        # 필터 적용
        filtered_df = df_flagged.copy()
        
        # if selected_anomaly != '전체' and '이상_유형' in filtered_df.columns:
        #     filtered_df = filtered_df[filtered_df['이상_유형'] == selected_anomaly]
        
        # if selected_lob != '전체' and 'lob' in filtered_df.columns:
        #     filtered_df = filtered_df[filtered_df['lob'] == selected_lob]
        
        # if change_range and '청구금액_변화율' in filtered_df.columns:
        #     filtered_df = filtered_df[
        #         (filtered_df['청구금액_변화율'] >= change_range[0]) & 
        #         (filtered_df['청구금액_변화율'] <= change_range[1])
        #     ]
        
        # if line_change_range and '회선수_변화율' in filtered_df.columns:
        #     filtered_df = filtered_df[
        #         (filtered_df['회선수_변화율'] >= line_change_range[0]) & 
        #         (filtered_df['회선수_변화율'] <= line_change_range[1])
        #     ]
        
        # 경고 메시지
        st.markdown(f"""
        <div style="background-color:#fee2e2; border:1px solid #fca5a5; border-radius:8px; padding:16px; margin:10px 0;">
            <div style="font-weight:bold; color:#dc2626;">⚠️ {len(filtered_df)}개의 이상 패턴이 발견되었습니다!</div>
            <div style="font-size:13px; color:#7f1d1d; margin-top:4px;">영업일 수 변화를 고려한 후에도 임계값을 초과하는 청구 항목들입니다.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 🎯 클릭 가능한 데이터 테이블
        if len(filtered_df) > 0:
            render_clickable_anomaly_table(filtered_df)
            
            # 요약 통계
            render_anomaly_summary_stats(filtered_df)
            
            # 📊 시각화 차트
            # render_anomaly_charts(filtered_df)
        else:
            st.warning("필터 조건에 맞는 이상 데이터가 없습니다.")
    else:
        st.markdown("""
        <div style="background-color:#dcfce7; border:1px solid #86efac; border-radius:8px; padding:16px; margin:10px 0;">
            <h4 style="color:#166534; margin:0;">✅ 영업일 변화를 고려한 결과, 이상 패턴이 발견되지 않았습니다!</h4>
            <p style="color:#166534; margin:8px 0 0 0;">모든 청구 항목이 영업일 수 변화 대비 정상 범위 내에 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)

def render_clickable_anomaly_table(df):
    """클릭 가능한 이상 탐지 테이블"""
    
    # 세션 상태 초기화
    # if 'selected_anomaly_row' not in st.session_state:
    #     st.session_state.selected_anomaly_row = None
    # if 'show_anomaly_detail' not in st.session_state:
    #     st.session_state.show_anomaly_detail = False
    
    # st.markdown("**📋 이상 탐지 상세 결과** (회선수 변화율을 클릭하면 상세 분석을 볼 수 있습니다)")
    
    # 컬럼 순서 정리
    display_columns = []
    if '이상_유형' in df.columns:
        display_columns.append('이상_유형')
    if '청구금액_변화율' in df.columns:
        display_columns.append('청구금액_변화율')
    if '회선수_변화율' in df.columns:
        display_columns.append('회선수_변화율')
    
    # 나머지 컬럼들 추가
    other_columns = [col for col in df.columns if col not in display_columns]
    display_columns.extend(other_columns)
    
    # 테이블 표시
    display_df = df[display_columns].reset_index(drop=True)
    
    # 스타일링을 위한 함수
    def highlight_clickable_columns(s):
        styles = []
        for col in s.index:
            if '회선수_변화율' in col:
                styles.append('background-color: #e0f2fe; cursor: pointer; font-weight: bold;')
            elif '청구금액_변화율' in col:
                styles.append('background-color: #f3e5f5;')
            elif '이상_유형' in col:
                styles.append('background-color: #ffebee;')
            else:
                styles.append('')
        return styles
    
    # 데이터 표시
    # styled_df = display_df.style.apply(highlight_clickable_columns, axis=1)
    
    # 클릭 이벤트를 위한 선택 가능한 데이터프레임
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # 행 선택 처리
    if event.selection and event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        selected_row_data = df.iloc[selected_row_idx]
        print(f"Selected row index: {selected_row_idx}, Data: {selected_row_data.to_dict()}")
        
        # 상세 분석 모달/expander 표시
        with st.expander(f"📊 상세 분석: {selected_row_data.get('청구항목명', '선택된 항목')}", expanded=True):
            render_detailed_anomaly_analysis(selected_row_data, df)
    
    # 도움말
    # st.markdown("""
    # <div style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px; margin-top:10px;">
    #     <div style="font-size:12px; color:#64748b;">
    #         💡 <b>사용 방법</b>:<br>
    #         • 테이블의 행을 클릭하면 해당 서비스의 상세 분석을 볼 수 있습니다<br>
    #         • 회선수 변화율이 파란색으로 표시된 항목은 특별히 주의가 필요합니다<br>
    #         • 필터링 옵션을 사용하여 특정 조건의 이상 항목만 볼 수 있습니다
    #     </div>
    # </div>
    # """, unsafe_allow_html=True)

def render_detailed_anomaly_analysis(selected_row, full_df):
    """선택된 행의 상세 분석"""
    
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     st.markdown("**📊 기본 정보**")
        
    #     info_data = {
    #         "서비스명": selected_row.get('청구항목명', 'N/A'),
    #         "단위서비스명": selected_row.get('단위서비스명', 'N/A'),
    #         "LOB": selected_row.get('lob', 'N/A'),
    #         "이상 유형": selected_row.get('이상_유형', 'N/A')
    #     }
        
    #     for key, value in info_data.items():
    #         st.markdown(f"• **{key}**: {value}")
    
    # with col2:
    #     st.markdown("**📈 변화율 정보**")
        
    #     change_data = {
    #         "청구금액 변화율": f"{selected_row.get('청구금액_변화율', 0):.1f}%",
    #         "회선수 변화율": f"{selected_row.get('회선수_변화율', 0):.1f}%",
    #         "현재 청구금액": f"{selected_row.get('m1요청금액', 0):,.0f}원",
    #         "이전 청구금액": f"{selected_row.get('m2요청금액', 0):,.0f}원" if 'm2요청금액' in selected_row else "N/A"
    #     }
        
    #     for key, value in change_data.items():
    #         st.markdown(f"• **{key}**: {value}")
    
    # 시계열 차트 (가능한 경우)
    if 'm1요청금액' in selected_row and 'm2요청금액' in selected_row:
        # st.markdown("📊 청구금액 변화 추이")
        
        # 간단한 추이 차트
        base_date = selected_row.get("기준월")
        months = [
            base_date - pd.DateOffset(months=2),
            base_date - pd.DateOffset(months=1),
            base_date
        ]
        month_labels = [d.strftime("%Y%m") for d in months]

        amounts = [
            selected_row.get('m3청구금액', 0),
            selected_row.get('m2청구금액', 0),
            selected_row.get('m1청구금액', 0)
        ]
        svccounts =[
            selected_row.get('m3월회선수', 0),
            selected_row.get('m2월회선수', 0),
            selected_row.get('m1월회선수', 0)
        ]

        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=month_labels,
                y=amounts,
                mode='lines+markers',
                name='청구금액',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=10)
            ))
            
            fig.update_layout(
                yaxis_title="청구금액 (원)",
                xaxis=dict(type="category"),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=month_labels,
                y=svccounts,
                mode='lines+markers',
                name='회선수',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=10)
            ))
            
            fig.update_layout(
                yaxis_title="회선 수",
                xaxis=dict(type="category"),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

    
    # 🚨 이상 분석 및 권장사항
    # st.markdown("**🔍 이상 분석 및 권장사항**")
    
    # billing_change = selected_row.get('청구금액_변화율', 0)
    # line_change = selected_row.get('회선수_변화율', 0)
    
    # recommendations = []
    
    # if billing_change > 50:
    #     recommendations.append("🚨 **급격한 청구금액 증가**: 마케팅 캠페인 효과 또는 요금제 변경 영향을 검토하세요.")
    # elif billing_change < -30:
    #     recommendations.append("⚠️ **청구금액 급감**: 고객 이탈 또는 서비스 품질 이슈를 점검하세요.")
    
    # if line_change > 30:
    #     recommendations.append("📈 **회선수 급증**: 인프라 확장 필요성과 서비스 품질 유지 방안을 검토하세요.")
    # elif line_change < -20:
    #     recommendations.append("📉 **회선수 감소**: 경쟁사 동향 분석 및 고객 유지 전략을 수립하세요.")
    
    # if abs(billing_change - line_change) > 20:
    #     if billing_change > line_change:
    #         recommendations.append("💰 **ARPU 상승**: 고객 품질 개선으로 판단되며, 이 추세를 지속할 방안을 모색하세요.")
    #     else:
    #         recommendations.append("💸 **ARPU 하락**: 가격 경쟁력 검토 및 부가서비스 확대를 고려하세요.")
    
    # if not recommendations:
    #     recommendations.append("✅ **정상 범위**: 지속적인 모니터링을 통해 트렌드를 관찰하세요.")
    
    # for rec in recommendations:
    #     st.markdown(f"• {rec}")

def render_anomaly_summary_stats(df):
    """이상 탐지 요약 통계"""
    avg_change = df['청구금액_변화율'].mean()
    max_amount = df['m1청구금액'].max()
    html_table = f"""
    <table style='width:100%; text-align:center; table-layout:fixed;'>
    <tr>
        <td>🔍 탐지된 이상 항목</td>
        <td>📊 평균 청구금액 변화율</td>
        <td>💰 최고 청구금액</td>
    </tr>
    <tr>
        <td><b>{len(df):,}</b></td>
        <td><b>{avg_change:.1f}%</b></td>
        <td><b>{max_amount:,.0f}</b></td>
    </tr>
    </table>
    """
    st.markdown(html_table, unsafe_allow_html=True)
    # col1, col2, col3 = st.columns(3)
    
    # with col1:
    #     st.markdown("""
    #     <div style="background-color:#f0f9ff; border:1px solid #0ea5e9; border-radius:8px; padding:0.5rem; text-align:center;">
    #         <div style="font-size:14px; color:#0369a1; font-weight:600;">🔍 탐지된 이상 항목</div>
    #         <div style="font-size:24px; font-weight:bold; color:#0c4a6e; margin:8px 0;">{:,}</div>
    #     </div>
    #     """.format(len(df)), unsafe_allow_html=True)
    
    # with col2:
    #     avg_change = df['청구금액_변화율'].mean() if '청구금액_변화율' in df.columns else 0
    #     st.markdown("""
    #     <div style="background-color:#f0fdf4; border:1px solid #22c55e; border-radius:8px; padding:0.5rem; text-align:center;">
    #         <div style="font-size:14px; color:#16a34a; font-weight:600;">📊 평균 청구금액 변화율</div>
    #         <div style="font-size:24px; font-weight:bold; color:#15803d; margin:8px 0;">{:.1f}%</div>
    #     </div>
    #     """.format(avg_change), unsafe_allow_html=True)
    
    # with col3:
    #     max_amount = df['m1요청금액'].max() if 'm1요청금액' in df.columns else 0
    #     st.markdown("""
    #     <div style="background-color:#fefce8; border:1px solid #eab308; border-radius:8px; padding:0.5rem; text-align:center;">
    #         <div style="font-size:14px; color:#ca8a04; font-weight:600;">💰 최고 요청금액</div>
    #         <div style="font-size:24px; font-weight:bold; color:#a16207; margin:8px 0;">{:,.0f}</div>
    #     </div>
    #     """.format(max_amount), unsafe_allow_html=True)

def render_anomaly_charts(df):
    """이상 탐지 시각화 차트"""
    
    st.markdown("**📈 이상 탐지 시각화**")
    if '청구금액_변화율' in df.columns and '회선수_변화율' in df.columns:
        fig = px.scatter(
            df, 
            x='회선수_변화율', 
            y='청구금액_변화율',
            hover_data=['청구항목명'] if '청구항목명' in df.columns else None,
            title="청구금액 vs 회선수 변화율",
            labels={
                '회선수_변화율': '회선수 변화율 (%)',
                '청구금액_변화율': '청구금액 변화율 (%)'
            }
        )
        fig.update_traces(marker=dict(size=10, opacity=0.7))
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # tab1, tab2, tab3 = st.tabs(["변화율 분포", "LOB별 분석", "이상 유형별 분석"])
    
    # with tab1:
    #     if '청구금액_변화율' in df.columns and '회선수_변화율' in df.columns:
    #         fig = px.scatter(
    #             df, 
    #             x='회선수_변화율', 
    #             y='청구금액_변화율',
    #             hover_data=['청구항목명'] if '청구항목명' in df.columns else None,
    #             title="청구금액 vs 회선수 변화율",
    #             labels={
    #                 '회선수_변화율': '회선수 변화율 (%)',
    #                 '청구금액_변화율': '청구금액 변화율 (%)'
    #             }
    #         )
    #         fig.update_traces(marker=dict(size=10, opacity=0.7))
    #         fig.update_layout(height=400)
    #         st.plotly_chart(fig, use_container_width=True)
    
    # with tab2:
    #     if 'lob' in df.columns:
    #         lob_summary = df.groupby('lob').agg({
    #             '청구금액_변화율': 'mean',
    #             '회선수_변화율': 'mean'
    #         }).reset_index()
            
    #         fig = px.bar(
    #             lob_summary, 
    #             x='lob', 
    #             y='청구금액_변화율',
    #             title="LOB별 평균 청구금액 변화율",
    #             labels={'청구금액_변화율': '평균 변화율 (%)'}
    #         )
    #         fig.update_layout(height=400)
    #         st.plotly_chart(fig, use_container_width=True)
    
    # with tab3:
    #     if '이상_유형' in df.columns:
    #         anomaly_counts = df['이상_유형'].value_counts()
            
    #         fig = px.pie(
    #             values=anomaly_counts.values,
    #             names=anomaly_counts.index,
    #             title="이상 유형별 분포"
    #         )
    #         fig.update_layout(height=400)
    #         st.plotly_chart(fig, use_container_width=True)

def render_summary_section(df, chat_mgr, session_mgr):
    """향상된 AI 요약 섹션"""
    st.markdown("##### 💻 AI 분석 요약")
    
    col1, col2= st.columns([1, 2.5])
    
    with col1:
        is_processing = st.session_state.get('is_processing', False)
        if st.button("📋 AI 요약 생성", disabled=is_processing, key="ai_summary_btn"):
            if chat_mgr:
                chat_mgr.generate_summary(df, session_mgr)
            else:
                st.error("AI 채팅 매니저를 사용할 수 없습니다.")
    
    with col2:
        st.info("💡 AI 요약: 영업일 변화와 이상 데이터 종합 분석 | 상세 리포트: 시각화와 함께 심층 분석")

# def generate_detailed_anomaly_report(df):
#     """상세 이상 탐지 리포트 생성"""
#     st.markdown("### 📊 이상 탐지 상세 리포트")
    
#     # 리포트 내용을 expander로 표시
#     with st.expander("📄 상세 리포트 보기", expanded=True):
        
#         st.markdown("#### 🔍 탐지 결과 요약")
        
#         if len(df) > 0:
#             total_anomalies = len(df)
#             avg_billing_change = df['청구금액_변화율'].mean() if '청구금액_변화율' in df.columns else 0
#             avg_line_change = df['회선수_변화율'].mean() if '회선수_변화율' in df.columns else 0
            
#             st.markdown(f"""
#             - **총 이상 항목**: {total_anomalies:,}개
#             - **평균 청구금액 변화율**: {avg_billing_change:.1f}%
#             - **평균 회선수 변화율**: {avg_line_change:.1f}%
#             - **분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#             """)
            
#             # 심각도별 분류
#             if '청구금액_변화율' in df.columns:
#                 high_severity = len(df[abs(df['청구금액_변화율']) > 50])
#                 medium_severity = len(df[(abs(df['청구금액_변화율']) > 20) & (abs(df['청구금액_변화율']) <= 50)])
#                 low_severity = len(df[abs(df['청구금액_변화율']) <= 20])
                
#                 st.markdown("#### 🚨 심각도별 분류")
#                 st.markdown(f"""
#                 - **높음 (±50% 초과)**: {high_severity}개
#                 - **보통 (±20~50%)**: {medium_severity}개  
#                 - **낮음 (±20% 이하)**: {low_severity}개
#                 """)
        
#         else:
#             st.markdown("이상 항목이 발견되지 않았습니다.")