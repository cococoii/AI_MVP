# chat/manager.py (이상 항목 상세 표시)
import streamlit as st
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from ui.components import render_chart_visualization
from config.settings import MODEL_NAME, API_VERSION

load_dotenv()

class ChatManager:
    def __init__(self):
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                api_version=API_VERSION,
                azure_endpoint=os.getenv("OPENAI_API_BASE")
            )
            self.model_name = os.getenv("OPENAI_DEPLOYMENT_NAME", MODEL_NAME)
        except Exception as e:
            st.error(f"OpenAI 클라이언트 초기화 오류: {e}")
            self.client = None
    
    def load_session(self, session_id, session_data):
        """세션 로드"""
        st.session_state.messages = session_data['messages']
        st.session_state.current_session_id = session_id
        st.session_state.last_file = session_data.get('file')
        st.session_state.last_dataframe = session_data.get('data')
        st.session_state.is_processing = False
    
    def generate_summary(self, df, session_mgr):
        """AI 요약 생성 (이상 항목 상세 표시)"""
        if not self.client:
            st.error("AI 클라이언트가 초기화되지 않았습니다.")
            return
            
        st.session_state.is_processing = True
        
        # 사용자 메시지 추가
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": "📋 데이터 요약을 요청합니다."})
        
        try:
            with st.spinner("🤖 AI가 데이터를 분석하고 있습니다..."):
                # 데이터 프로세서 인스턴스 생성하여 이상 탐지
                from data.processor import DataProcessor
                processor = DataProcessor()
                
                # 이상 탐지 실행
                df_flagged = processor.detect_anomalies(df)
                
                # 요약 프롬프트 생성
                summary_prompt = self._create_detailed_anomaly_prompt(df, df_flagged)
                
                summary_reply = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                reply_text = summary_reply.choices[0].message.content
                
                # AI 응답 표시
                with st.chat_message("assistant"):
                    st.markdown(reply_text)
                
                st.session_state.messages.append({"role": "assistant", "content": reply_text})
                
                if session_mgr:
                    session_mgr.save_current_chat()
                
        except Exception as e:
            error_msg = f"죄송합니다. 요약 생성 중 오류가 발생했습니다: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        finally:
            st.session_state.is_processing = False
    
    def _create_detailed_anomaly_prompt(self, df, df_flagged):
        """이상 항목 상세 정보를 포함한 요약 프롬프트"""
        # 영업일 상세 정보
        detailed_biz_days = st.session_state.get('detailed_biz_days', {})
        biz_days_summary = st.session_state.get('biz_days', {})
        
        # 영업일 변화 분석
        biz_changes = []
        if biz_days_summary and len(biz_days_summary) > 0:
            months = sorted(biz_days_summary.keys())
            
            for i, month in enumerate(months):
                current_days = biz_days_summary[month]
                
                # 공휴일 정보 가져오기
                holiday_info = ""
                if month in detailed_biz_days and detailed_biz_days[month].get('holiday_list'):
                    holidays = [h['name'] for h in detailed_biz_days[month]['holiday_list']]
                    holiday_info = f" (공휴일: {', '.join(holidays)})"
                elif month in detailed_biz_days and detailed_biz_days[month].get('holiday_days', 0) == 0:
                    holiday_info = " (공휴일 없음)"
                
                if i == 0:
                    biz_changes.append(f"- {month}: {current_days}일{holiday_info}")
                else:
                    prev_month = months[i-1]
                    prev_days = biz_days_summary[prev_month]
                    change = current_days - prev_days
                    change_pct = (change / prev_days * 100) if prev_days > 0 else 0
                    
                    change_text = "변화없음" if change == 0 else f"{change:+d}일 ({change_pct:+.1f}%)"
                    biz_changes.append(f"- {month}: {current_days}일, 전월({prev_month}) 대비 {change_text}{holiday_info}")
        
        # 이상 데이터 상세 분석
        anomaly_details = ""
        detailed_anomaly_list = ""
        
        if len(df_flagged) > 0:
            # 이상 유형별 분포
            if '이상_유형' in df_flagged.columns:
                type_counts = df_flagged['이상_유형'].value_counts()
                type_analysis = []
                for type_name, count in type_counts.items():
                    type_analysis.append(f"  • {type_name}: {count}개")
                
                anomaly_details = f"""
📊 **이상 항목 상세 분석:**
- 총 이상 항목: {len(df_flagged)}개
- 유형별 분포:
{chr(10).join(type_analysis)}
"""
                
                # 변화율 통계
                if '청구금액_변화율' in df_flagged.columns and '회선수_변화율' in df_flagged.columns:
                    avg_billing_change = df_flagged['청구금액_변화율'].mean()
                    avg_line_change = df_flagged['회선수_변화율'].mean()
                    max_billing_change = df_flagged['청구금액_변화율'].max()
                    min_billing_change = df_flagged['청구금액_변화율'].min()
                    
                    anomaly_details += f"""
- 평균 청구금액 변화율: {avg_billing_change:.1f}%
- 평균 회선수 변화율: {avg_line_change:.1f}%
- 청구금액 변화율 범위: {min_billing_change:.1f}% ~ {max_billing_change:.1f}%
"""
                
                # 🔥 상세 이상 항목 리스트 (특히 이상하게 늘어난 것들)
                detailed_anomaly_list = self._create_detailed_anomaly_list(df_flagged)
        else:
            anomaly_details = "📊 **이상 항목:** 탐지된 이상 패턴이 없습니다."
        
        # 영업일 변화 텍스트
        biz_change_text = "\n".join(biz_changes) if biz_changes else "- 영업일 변화 정보를 계산할 수 없습니다."
        
        return f"""
다음은 한국 공휴일을 고려한 청구 데이터 분석 결과입니다:

📅 **월별 영업일 수 현황:**
{biz_change_text}

{anomaly_details}

🔍 **이상 항목 상세 리스트:**
{detailed_anomaly_list}

📋 **전체 데이터 현황:**
- 분석 대상 데이터: {len(df)}개
- 분석 기간: {df['기준월'].min().strftime('%Y-%m')} ~ {df['기준월'].max().strftime('%Y-%m')}

🎯 **요약 요청사항:**

다음 내용을 **구체적이고 상세하게** 요약해주세요:

1. **📅 영업일 수 변화 분석**
   - 각 월별 영업일 수와 전월 대비 변화
   - 영업일 변화에 따른 정상적인 청구금액 증가 범위

2. **🚨 이상 데이터 상세 분석**
   - **특히 이상하게 늘어난 항목들을 구체적으로 언급**
   - 각 이상 항목의 변화율과 문제점
   - 영업일 증가로는 설명되지 않는 과도한 증가 패턴
   - **구체적인 고객/상품명과 수치를 포함하여 설명**

3. **💡 핵심 인사이트 및 주의사항**
   - 즉시 확인이 필요한 항목들
   - 비즈니스 관점에서의 리스크 요소

**응답 형식:**
- 각 섹션을 명확히 구분
- **이상 항목은 구체적인 이름과 수치로 설명**
- 심각도 순으로 정렬하여 제시
- 영업일 정규화 후에도 비정상적인 패턴 강조

**특히 중요:** 이상 항목들을 "항목 A", "항목 B" 같은 일반적 표현이 아닌, 
**실제 데이터의 구체적인 내용**으로 설명해주세요.
        """
    
    def _create_detailed_anomaly_list(self, df_flagged):
        """상세 이상 항목 리스트 생성"""
        if len(df_flagged) == 0:
            return "탐지된 이상 항목이 없습니다."
        
        # 청구금액 변화율로 정렬 (높은 순)
        if '청구금액_변화율' in df_flagged.columns:
            df_sorted = df_flagged.sort_values('청구금액_변화율', ascending=False)
        else:
            df_sorted = df_flagged
        
        anomaly_list = []
        
        # 상위 10개 이상 항목 상세 정보
        display_count = min(10, len(df_sorted))
        
        for i in range(display_count):
            row = df_sorted.iloc[i]
            
            # 기본 정보
            item_info = {}
            
            # 첫 번째 컬럼을 항목명으로 사용
            first_col = df_flagged.columns[0]
            item_name = str(row[first_col]) if first_col in row else f"항목_{i+1}"
            item_info['이름'] = item_name
            
            # 변화율 정보
            if '청구금액_변화율' in row:
                item_info['청구금액_변화율'] = f"{row['청구금액_변화율']:+.1f}%"
            if '회선수_변화율' in row:
                item_info['회선수_변화율'] = f"{row['회선수_변화율']:+.1f}%"
            
            # 이상 유형
            if '이상_유형' in row:
                item_info['이상_유형'] = row['이상_유형']
            
            # 실제 수치
            if 'm1청구금액' in row and 'm2청구금액' in row:
                m1_amount = row['m1청구금액']
                m2_amount = row['m2청구금액']
                item_info['청구금액'] = f"{m2_amount:,.0f}원 → {m1_amount:,.0f}원"
            
            if 'm1월회선수' in row and 'm2월회선수' in row:
                m1_lines = row['m1월회선수']
                m2_lines = row['m2월회선수']
                item_info['회선수'] = f"{m2_lines:,.0f}개 → {m1_lines:,.0f}개"
            
            # ARPU 정보
            if 'arpu' in row:
                item_info['ARPU'] = f"{row['arpu']:,.0f}원"
            
            # 심각도 판단
            billing_change = abs(row.get('청구금액_변화율', 0))
            if billing_change >= 50:
                severity = "🔴 매우 심각"
            elif billing_change >= 30:
                severity = "🟡 심각"
            elif billing_change >= 15:
                severity = "🟠 주의"
            else:
                severity = "🔵 경미"
            
            item_info['심각도'] = severity
            
            # 텍스트 생성
            anomaly_text = f"""
**{i+1}. {item_info['이름']}** ({item_info.get('심각도', '')})
- 이상 유형: {item_info.get('이상_유형', 'N/A')}
- 청구금액 변화: {item_info.get('청구금액_변화율', 'N/A')} ({item_info.get('청구금액', 'N/A')})
- 회선수 변화: {item_info.get('회선수_변화율', 'N/A')} ({item_info.get('회선수', 'N/A')})
- ARPU: {item_info.get('ARPU', 'N/A')}
"""
            
            anomaly_list.append(anomaly_text)
        
        # 요약 추가
        if len(df_flagged) > display_count:
            anomaly_list.append(f"\n... 외 {len(df_flagged) - display_count}개 항목이 더 있습니다.")
        
        return "\n".join(anomaly_list)
    
    def _get_system_prompt(self):
        """시스템 프롬프트"""
        return """
너는 한국의 청구 데이터 분석 전문가야.
특히 영업일 수 변화와 이상 데이터 탐지가 전문 분야야.

분석 원칙:
1. 영업일 수 변화를 항상 우선 고려
2. 이상 항목들을 구체적인 이름과 수치로 설명
3. 심각도에 따라 우선순위를 정해서 설명
4. 영업일 정규화 후 실질적 이상 패턴만 식별

응답 스타일:
- 친근하고 전문적인 톤
- **이상 항목은 구체적인 데이터로 설명**
- 실제 고객명/상품명과 변화 수치 포함
- 비즈니스 관점에서의 실용적 조언

특히 이상하게 늘어난 항목들을 구체적으로 언급하고,
각 항목의 문제점과 확인이 필요한 이유를 명확히 설명해줘.

"항목 A", "고객 B" 같은 일반적 표현 대신, 
실제 데이터에 있는 구체적인 이름과 수치를 사용해서 설명해줘.
        """
    
    def handle_user_question(self, user_question, session_mgr):
        """사용자 질문 처리"""
        if not self.client:
            st.error("AI 클라이언트가 초기화되지 않았습니다.")
            return
            
        with st.chat_message("user"):
            st.markdown(user_question)
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": user_question})
        st.session_state.is_processing = True

        try:
            with st.spinner("🤖 AI가 답변을 준비하고 있습니다..."):
                df = st.session_state.last_dataframe
                detailed_biz_days = st.session_state.get('detailed_biz_days', {})
                
                prompt = f"""
사용자의 질문: {user_question}

현재 분석 중인 데이터 정보:
- 전체 데이터 행 수: {len(df)}

📅 한국 공휴일 고려 영업일 정보:
{self._format_business_days(detailed_biz_days)}

📊 관련 데이터 샘플:
{df.head(10).to_csv(index=False)}

질문에 대해 영업일 수 변화를 고려한 정확한 답변을 제공해주세요.
구체적인 수치와 데이터 근거를 포함하여 답변해주세요.
                """
                
                gpt_reply = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2500
                )
                
                reply = gpt_reply.choices[0].message.content
                
                with st.chat_message("assistant"):
                    st.markdown(reply)
                    
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
                if session_mgr:
                    session_mgr.save_current_chat()

        except Exception as e:
            error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
            with st.chat_message("assistant"):
                st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        finally:
            st.session_state.is_processing = False
        
        # 요금제 관련 질문일 경우 시각화 추가
        if st.session_state.last_dataframe is not None and "요금제" in user_question:
            keyword = self._extract_keyword_from_question(user_question)
            if keyword:
                render_chart_visualization(st.session_state.last_dataframe, keyword)
    
    def _format_business_days(self, detailed_biz_days):
        """영업일 정보 포맷팅"""
        if not detailed_biz_days:
            return "영업일 정보가 없습니다."
        
        formatted_lines = []
        for month, info in detailed_biz_days.items():
            holiday_text = ""
            if info['holiday_list']:
                holidays_str = ", ".join([f"{h['date']}({h['name']})" for h in info['holiday_list']])
                holiday_text = f" [공휴일: {holidays_str}]"
            
            formatted_lines.append(
                f"- {month}: 총 {info['total_days']}일 중 영업일 {info['business_days']}일 "
                f"(주말 {info['weekend_days']}일, 공휴일 {info['holiday_days']}일){holiday_text}"
            )
        
        return "\n".join(formatted_lines)
    
    def _extract_keyword_from_question(self, question):
        """질문에서 키워드 추출"""
        if "요금제" in question:
            parts = question.split("요금제")
            if len(parts) > 1:
                after_plan = parts[-1].strip().split()
                if after_plan:
                    return after_plan[0]
                before_plan = parts[0].strip().split()
                if before_plan:
                    return before_plan[-1]
        return ""
    
    def get_conversation_summary(self):
        """대화 요약 반환"""
        if not st.session_state.get('messages', []):
            return "대화 기록이 없습니다."
        
        user_questions = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        return f"총 {len(user_questions)}개의 질문이 있었습니다: {', '.join(user_questions[:3])}{'...' if len(user_questions) > 3 else ''}"
    
    def clear_conversation(self):
        """대화 기록 초기화"""
        st.session_state.messages = []
        st.session_state.is_processing = False