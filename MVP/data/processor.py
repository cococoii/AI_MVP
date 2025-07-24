# data/processor.py (한국 공휴일 고려 버전)
import pandas as pd
import streamlit as st
from pandas.tseries.offsets import BDay
import holidays
import datetime
from config.settings import MIN_AMOUNT_DEFAULT, MIN_LINES_DEFAULT, CHANGE_THRESHOLD_DEFAULT

class DataProcessor:
    def __init__(self):
        # 한국 공휴일 (2024-2026년까지)
        self.kr_holidays = holidays.KR(years=[2024, 2025, 2026])
        self.min_amount = MIN_AMOUNT_DEFAULT
        self.min_lines = MIN_LINES_DEFAULT
        self.change_threshold = CHANGE_THRESHOLD_DEFAULT
    
    def update_thresholds(self, min_amount, min_lines, change_threshold):
        """임계값 업데이트"""
        self.min_amount = min_amount
        self.min_lines = min_lines
        self.change_threshold = change_threshold
    
    def calculate_korean_business_days(self, year, month):
        """한국 공휴일을 고려한 영업일 수 계산"""
        # 해당 월의 첫째 날과 마지막 날
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        # 전체 날짜 생성
        total_days = 0
        business_days = 0
        weekend_days = 0
        holiday_days = 0
        holiday_list = []
        
        # 🔍 디버그: 각 날짜별 상세 로그
        # print(f"🔍 === {year}년 {month}월 영업일 계산 시작 ===")
        # print(f"기간: {start_date} ~ {end_date}")
        
        current_date = start_date
        while current_date <= end_date:
            total_days += 1
            
            day_type = ""
            
            # 주말 확인 (토요일=5, 일요일=6)
            if current_date.weekday() >= 5:
                weekend_days += 1
                day_type = f"주말 (weekday={current_date.weekday()})"
            # 공휴일 확인
            elif current_date in self.kr_holidays:
                holiday_days += 1
                holiday_name = self.kr_holidays.get(current_date, '공휴일')
                holiday_list.append({
                    'date': current_date.strftime('%m-%d'),
                    'name': holiday_name
                })
                day_type = f"공휴일 ({holiday_name})"
            else:
                business_days += 1
                day_type = "영업일"
            
            # 각 날짜별 상세 로그
            # print(f"  {current_date.strftime('%m-%d')} ({current_date.strftime('%A')}): {day_type}")
            
            current_date += datetime.timedelta(days=1)
        
        # 🔍 디버그: 최종 계산 결과
        # print(f"🔍 === {year}년 {month}월 계산 완료 ===")
        # print(f"  📊 총 일수: {total_days}일")
        # print(f"  📅 주말: {weekend_days}일")  
        # print(f"  🎌 공휴일: {holiday_days}일")
        # print(f"  💼 영업일: {business_days}일")
        # print(f"  🎌 공휴일 목록: {holiday_list}")
        # print(f"🔍 ================================")
        
        return {
            'year': year,
            'month': month,
            'total_days': total_days,
            'business_days': business_days,
            'weekend_days': weekend_days,
            'holiday_days': holiday_days,
            'holiday_list': holiday_list
        }
    
    def calculate_business_days(self, df):
        """영업일 수 계산 (한국 공휴일 포함)"""
        try:
            if '기준월' not in df.columns:
                # 기본값으로 2025년 6월 설정
                df['기준월'] = '2025-06-01'
            
            df['기준월'] = pd.to_datetime(df['기준월'], errors='coerce')
            base_date = df['기준월'].dropna().sort_values().iloc[-1]
            # 3개월 리스트 생성
            base_period = base_date.to_period('M') 
            
            months =  [base_period - 2, base_period - 1, base_period]
            print(months)
            
            biz_day_data = []
            prev_days = None
            
            # biz_days 세션 상태 초기화
            if 'biz_days' not in st.session_state:
                st.session_state.biz_days = {}
            
            if 'detailed_biz_days' not in st.session_state:
                st.session_state.detailed_biz_days = {}
            
            for m in months:
                year = m.year
                month = m.month
                ym_str = m.strftime("%Y-%m")
                
                # 한국 공휴일 고려한 영업일 계산
                biz_info = self.calculate_korean_business_days(year, month)
                current_days = biz_info['business_days']
                
                # 세션 상태에 저장
                st.session_state.biz_days[ym_str] = current_days
                st.session_state.detailed_biz_days[ym_str] = biz_info

                if prev_days is None:
                    delta = 0
                    delta_text = "—"
                    delta_percent = 0
                else:
                    delta = current_days - prev_days
                    delta_percent = (delta / prev_days * 100) if prev_days > 0 else 0
                    delta_text = f"{'+' if delta > 0 else ''}{delta}일 ({delta_percent:+.1f}%)"

                biz_day_data.append({
                    "월": ym_str,
                    "영업일 수": current_days,
                    "전월 대비": delta_text,
                    "변화": delta,
                    "변화율": delta_percent,
                    "총 일수": biz_info['total_days'],
                    "주말": biz_info['weekend_days'],
                    "공휴일": biz_info['holiday_days'],
                    "공휴일 목록": biz_info['holiday_list']
                })
                prev_days = current_days
            
            return biz_day_data
            
        except Exception as e:
            st.error(f"영업일 계산 중 오류: {str(e)}")
            return []
    
    def process_uploaded_file(self, uploaded_file, session_mgr=None):
        """업로드된 파일 처리"""
        try:
            with st.spinner("📊 데이터를 처리하고 있습니다..."):
                # CSV 파일 읽기
                df = pd.read_csv(uploaded_file)
                
                # 컬럼명 정리
                df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")
                
                # 데이터 기본 정리
                df = self._clean_data(df)
                
                # 세션 상태 업데이트
                st.session_state.last_file = uploaded_file.name
                st.session_state.last_dataframe = df.copy()
                
                # 영업일 수 미리 계산
                self.calculate_business_days(df)
                
                # 세션 매니저가 있을 때만 호출
                if session_mgr is not None:
                    session_mgr.update_session_data(uploaded_file.name, df)
                else:
                    self._update_basic_session_data(uploaded_file.name, df)
                
                # ✅ Azure 업로드 기능 추가
                from utils.azure_helper import AzureHelper
                azure = AzureHelper()
                if azure.connected:
                    success, result = azure.upload_csv(df, uploaded_file.name)
                    if success:
                        st.info(f"☁️ Azure Blob에 저장됨: {uploaded_file.name}")
                    else:
                        st.warning(f"❌ Azure 업로드 실패: {result}")
                else:
                    st.warning("⚠️ Azure 연결 실패 - 환경변수 또는 네트워크 확인")
                
            # st.success("✅ 데이터가 성공적으로 업로드되었습니다!")
            return df
            
        except Exception as e:
            st.error(f"❌ 파일 업로드 중 오류가 발생했습니다: {str(e)}")
            return None
    
    def _update_basic_session_data(self, filename, dataframe):
        """기본 세션 데이터 업데이트 (session_mgr 없이)"""
        try:
            if 'current_session_id' not in st.session_state:
                import uuid
                st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
            
            if 'chat_sessions' not in st.session_state:
                st.session_state.chat_sessions = {}
            
            if st.session_state.current_session_id not in st.session_state.chat_sessions:
                st.session_state.chat_sessions[st.session_state.current_session_id] = {
                    "messages": [],
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # ✅ 문자열로 저장
                    "file": None,
                    "data": None,
                    "biz_days": {}
                }

            session = st.session_state.chat_sessions[st.session_state.current_session_id]
            session["messages"] = st.session_state.get("messages", [])
            session["file"] = filename
            session["data"] = dataframe
            session["timestamp"] = datetime.datetime.now()
            
        except Exception as e:
            st.warning(f"세션 데이터 업데이트 중 오류: {str(e)}")
    
    def _clean_data(self, df):
        """데이터 정리"""
        df = df.dropna(how='all')
        
        numeric_columns = ["m1요청금액", "m2요청금액", "m1월회선수", "m2월회선수", "m1청구금액", "m2청구금액"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def detect_anomalies(self, df):
        """이상 패턴 탐지 (상세 정보 포함)"""
        try:
            df_filtered = df.copy()
            
            # 숫자형 변환
            for col in ["m1요청금액", "m2요청금액", "m1월회선수", "m2월회선수", "m1청구금액", "m2청구금액"]:
                if col in df_filtered.columns:
                    df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

            # ARPU 계산
            df_filtered["arpu"] = df_filtered.apply(
                lambda row: row["m1청구금액"] / row["m1월회선수"] 
                if row["m1월회선수"] > 0 else 0, axis=1
            )
            
            # 청구금액 변화율 계산
            df_filtered["청구금액_변화율"] = df_filtered.apply(
                lambda row: ((row["m1청구금액"] - row["m2청구금액"]) / row["m2청구금액"] * 100) 
                if row["m2청구금액"] > 0 else 0, axis=1
            )
            
            # 회선수 변화율 계산
            df_filtered["회선수_변화율"] = df_filtered.apply(
                lambda row: ((row["m1월회선수"] - row["m2월회선수"]) / row["m2월회선수"] * 100) 
                if row["m2월회선수"] > 0 else 0, axis=1
            )

            # 이상 데이터 필터링 조건
            conditions = [
                ((df_filtered["m1월회선수"] + df_filtered["m2월회선수"]) > 0),
                ((df_filtered["m1요청금액"] >= self.min_amount) | (df_filtered["m2요청금액"] >= self.min_amount)),
                (df_filtered["m1월회선수"] > self.min_lines),
                (df_filtered["arpu"] >= 0.1),
                (abs(df_filtered["청구금액_변화율"]) >= self.change_threshold),
                (abs(df_filtered["회선수_변화율"]) >= self.change_threshold)
            ]
            
            if conditions:
                final_condition = conditions[0]
                for condition in conditions[1:]:
                    final_condition = final_condition & condition
                    
                df_flagged = df_filtered[final_condition].copy()
                
                # 이상 유형 분류
                if len(df_flagged) > 0:
                    df_flagged["이상_유형"] = df_flagged.apply(self._classify_anomaly_type, axis=1)
                    
            else:
                df_flagged = pd.DataFrame()
            
            return df_flagged
            
        except Exception as e:
            st.error(f"이상 탐지 중 오류: {str(e)}")
            return pd.DataFrame()
    
    def _classify_anomaly_type(self, row):
        """이상 유형 분류"""
        types = []
        
        if abs(row["청구금액_변화율"]) >= self.change_threshold:
            if row["청구금액_변화율"] > 0:
                types.append("청구금액 급증")
            else:
                types.append("청구금액 급감")
        
        if abs(row["회선수_변화율"]) >= self.change_threshold:
            if row["회선수_변화율"] > 0:
                types.append("회선수 급증")
            else:
                types.append("회선수 급감")
        
        if row["m1요청금액"] >= self.min_amount:
            types.append("고액 요청")
        
        if row["arpu"] < 1000:  # ARPU가 너무 낮은 경우
            types.append("저ARPU")
        elif row["arpu"] > 50000:  # ARPU가 너무 높은 경우
            types.append("고ARPU")
        
        return " / ".join(types) if types else "기타"
    
    def get_anomaly_summary(self, df_flagged):
        """이상 항목 요약 정보"""
        if len(df_flagged) == 0:
            return "이상 항목이 발견되지 않았습니다."
        
        summary = {
            "총_이상_항목": len(df_flagged),
            "유형별_분포": df_flagged["이상_유형"].value_counts().to_dict(),
            "평균_청구금액_변화율": df_flagged["청구금액_변화율"].mean(),
            "평균_회선수_변화율": df_flagged["회선수_변화율"].mean(),
            "최고_청구금액": df_flagged["m1청구금액"].max(),
            "최고_회선수": df_flagged["m1월회선수"].max()
        }
        
        return summary
    
    def get_business_days_impact_analysis(self, df, df_flagged):
        """영업일 수 변화가 청구금액에 미치는 영향 분석"""
        try:
            biz_days_info = st.session_state.get('detailed_biz_days', {})
            
            analysis = {
                "영업일_변화_요약": [],
                "청구금액_대비_영업일_효율성": [],
                "이상항목_영업일_연관성": ""
            }
            
            # 영업일 변화 분석
            months = sorted(biz_days_info.keys())
            for i, month in enumerate(months):
                biz_info = biz_days_info[month]
                
                if i > 0:
                    prev_month = months[i-1]
                    prev_biz_info = biz_days_info[prev_month]
                    
                    biz_change = biz_info['business_days'] - prev_biz_info['business_days']
                    biz_change_pct = (biz_change / prev_biz_info['business_days'] * 100) if prev_biz_info['business_days'] > 0 else 0
                    
                    # 해당 월의 청구금액 변화
                    month_data = df[df['기준월'].dt.strftime('%Y-%m') == month]
                    if len(month_data) > 0:
                        avg_billing = month_data['m1청구금액'].mean()
                        
                        analysis["영업일_변화_요약"].append({
                            "월": month,
                            "영업일_변화": biz_change,
                            "영업일_변화율": biz_change_pct,
                            "공휴일_수": biz_info['holiday_days'],
                            "공휴일_목록": [h['name'] for h in biz_info['holiday_list']],
                            "평균_청구금액": avg_billing
                        })
            
            # 이상항목과 영업일 연관성 분석
            if len(df_flagged) > 0:
                flagged_months = df_flagged['기준월'].dt.strftime('%Y-%m').unique()
                high_anomaly_months = []
                
                for month in flagged_months:
                    month_anomalies = len(df_flagged[df_flagged['기준월'].dt.strftime('%Y-%m') == month])
                    if month in biz_days_info:
                        biz_info = biz_days_info[month]
                        high_anomaly_months.append({
                            "월": month,
                            "이상항목_수": month_anomalies,
                            "영업일_수": biz_info['business_days'],
                            "공휴일_수": biz_info['holiday_days']
                        })
                
                analysis["이상항목_영업일_연관성"] = high_anomaly_months
            
            return analysis
            
        except Exception as e:
            st.error(f"영업일 영향 분석 중 오류: {str(e)}")
            return {}