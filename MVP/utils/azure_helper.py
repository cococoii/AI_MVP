# utils/azure_ai_helper.py - v4 완전 재작성 (제대로 된 AI 분석)
import streamlit as st
import io
import pandas as pd
from azure.storage.blob import BlobServiceClient
import os
from datetime import datetime
import json
import re
from dotenv import load_dotenv

load_dotenv()

class AzureHelper:
    """Azure Blob Storage + 진짜 제대로 된 AI 분석 도우미 v4"""
    
    def __init__(self):
        self.setup_connection()
        self.available_files = []
        self.all_data_cache = None
        
    def setup_connection(self):
        """Azure 연결 설정"""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.connected = False
        
        if connection_string:
            try:
                self.client = BlobServiceClient.from_connection_string(connection_string)
                container_client = self.client.get_container_client("billing-data")
                container_client.get_container_properties()
                self.connected = True
                st.success("✅ Azure 연결 성공!")
            except Exception as e:
                st.error(f"❌ Azure 연결 실패: {e}")
                self.connected = False
        else:
            st.warning("⚠️ AZURE_STORAGE_CONNECTION_STRING이 설정되지 않았습니다.")

    def upload_csv(self, df, filename):
        """CSV 업로드"""
        if not self.connected:
            return False, "Azure 연결 안됨"
        
        try:
            csv_string = df.to_csv(index=False, encoding='utf-8-sig')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"uploads/{timestamp}_{filename}"
            
            blob_client = self.client.get_blob_client(container="billing-data", blob=blob_name)
            blob_client.upload_blob(csv_string, overwrite=True)
            return True, blob_name
        except Exception as e:
            return False, str(e)

    def _discover_files(self):
        """파일 탐지 및 데이터 로드"""
        if not self.connected:
            st.error("❌ Azure 연결이 필요합니다.")
            return {}
        
        try:
            container_client = self.client.get_container_client("billing-data")
            blob_list = container_client.list_blobs()
            
            all_data = {}
            file_count = 0
            
            with st.spinner("📊 Azure에서 데이터 파일들을 로드 중..."):
                for blob in blob_list:
                    blob_name = blob.name
                    
                    # 대상 폴더 확인
                    if not (blob_name.startswith('monthly_data/') or blob_name.startswith('plan_metadata/')):
                        continue
                    
                    # 파일 확장자 확인
                    if not blob_name.endswith(('.csv', '.xlsx', '.xls')):
                        continue
                    
                    # 청구 데이터 키워드 확인
                    billing_keywords = ['billing', 'data', '청구', '데이터', 'monthly', '월별']
                    if not any(keyword in blob_name.lower() for keyword in billing_keywords):
                        continue
                    
                    # 월 정보 추출
                    month_match = re.search(r'(\d{4})[-_]?(\d{2})', blob_name)
                    if month_match:
                        year, month = month_match.groups()
                        month_key = f"{year}-{month.zfill(2)}"
                    else:
                        month_key = f"unknown_{file_count}"
                    
                    # 데이터 로드
                    try:
                        if blob_name.endswith('.csv'):
                            df = self._load_csv_blob(blob_name)
                        else:
                            df = self._load_excel_blob(blob_name)
                        
                        if df is not None and len(df) > 0:
                            # 컬럼 정리
                            df = self._clean_dataframe(df)
                            all_data[month_key] = df
                            file_count += 1
                            # st.write(f"✅ {blob_name} 로드 완료 ({len(df)}행)")
                            
                    except Exception as e:
                        st.warning(f"로드 실패")
            
            if all_data:
                st.success(f"🎉 총 {len(all_data)}개 월의 데이터 로드 완료!")
                # 데이터 구조 미리보기
                sample_month = list(all_data.keys())[0]
                sample_df = all_data[sample_month]
                st.write(f"📋 **데이터 구조** ({sample_month} 샘플):")
                st.write(f"- 컬럼: {list(sample_df.columns)}")
                st.write(f"- 행 수: {len(sample_df)}")
                if len(sample_df) > 0:
                    st.write("- 샘플 데이터:")
                    st.dataframe(sample_df.head(3))
            else:
                st.error("❌ 로드할 수 있는 데이터 파일이 없습니다.")
            
            return all_data
            
        except Exception as e:
            st.error(f"❌ 파일 탐지 실패: {e}")
            return {}

    def _load_csv_blob(self, blob_name):
        """CSV 블롭 로드"""
        blob_client = self.client.get_blob_client(container="billing-data", blob=blob_name)
        csv_content = blob_client.download_blob().readall()
        
        # 인코딩 시도
        for encoding in ['utf-8-sig', 'utf-8', 'euc-kr', 'cp949']:
            try:
                content_str = csv_content.decode(encoding)
                return pd.read_csv(io.StringIO(content_str))
            except UnicodeDecodeError:
                continue
        
        raise Exception("지원되지 않는 인코딩")

    def _load_excel_blob(self, blob_name):
        """Excel 블롭 로드"""
        blob_client = self.client.get_blob_client(container="billing-data", blob=blob_name)
        excel_content = blob_client.download_blob().readall()
        return pd.read_excel(io.BytesIO(excel_content))

    def _clean_dataframe(self, df):
        """데이터프레임 정리 및 표준화"""
        # 컬럼명 정리
        df.columns = df.columns.str.strip()
        
        # 표준 컬럼 매핑
        column_mapping = {
            '청구항목명': 'service_name',
            '단위서비스명': 'unit_service_name',
            '청구금액': 'billing_amount',
            '회선수': 'line_count',
            'lob명': 'lob_name',
            'LOB명': 'lob_name',
            '사업부': 'lob_name'
        }
        
        # 매핑 적용
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # 숫자 컬럼 정리
        numeric_columns = ['billing_amount', 'line_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 통합 서비스명 생성 (서비스 코드 포함)
        if 'service_name' in df.columns:
            df['full_service_id'] = df['service_name'].astype(str)
            if 'unit_service_name' in df.columns:
                df['full_service_id'] = df['service_name'].astype(str) + " | " + df['unit_service_name'].astype(str)
        
        # 서비스 코드 추출
        if 'full_service_id' in df.columns:
            df['service_code'] = df['full_service_id'].str.extract(r'([A-Z]{2,5}[0-9]{2,4})', expand=False)
        
        return df

    def analyze_service_query(self, user_question):
        """🎯 메인 분석 함수 - 사용자 질문 처리"""
        
        if not self.connected:
            return "❌ **Azure 연결 오류**\n\nAzure Blob Storage 연결을 확인해주세요."
        
        # 데이터 로드 (캐시 활용)
        if self.all_data_cache is None:
            self.all_data_cache = self._discover_files()
        
        if not self.all_data_cache:
            return "❌ **데이터 없음**\n\n분석할 수 있는 청구 데이터가 없습니다."
        
        # 질문 분석 및 라우팅
        try:
            return self._route_question(user_question, self.all_data_cache)
        except Exception as e:
            return f"❌ **분석 오류**\n\n{str(e)}\n\n다시 시도해주세요."

    def _route_question(self, question, all_data):
        """질문 유형 분석 및 적절한 분석 함수 호출"""
        
        question_lower = question.lower().strip()
        
        # 🔍 1. 특정 서비스 코드 질문 (DATA001, IOT002 등)
        service_codes = re.findall(r'\b[A-Z]{2,5}[0-9]{2,4}\b', question.upper())
        if service_codes:
            return self._analyze_specific_service_code(service_codes[0], question, all_data)
        
        # 🔍 2. 서비스명 직접 언급 (부분 매칭)
        service_keywords = ['무제한', '프리미엄', '센서', 'iot', '5g', 'lte', 'vpn', '데이터']
        mentioned_services = [kw for kw in service_keywords if kw in question_lower]
        if mentioned_services:
            return self._analyze_service_by_keyword(mentioned_services, question, all_data)
        
        # 🔍 3. TOP/순위 분석
        if re.search(r'(top|톱|순위|랭킹)\s*\d*', question_lower):
            return self._analyze_top_ranking(question, all_data)
        
        # 🔍 4. 성장률/변화 분석
        if any(word in question_lower for word in ['성장', '변화', '증가', '감소', '트렌드']):
            return self._analyze_growth_trend(question, all_data)
        
        # 🔍 5. LOB/사업부 분석
        if any(word in question_lower for word in ['lob', '사업부', '부서별']):
            return self._analyze_lob_performance(question, all_data)
        
        # 🔍 6. 비교 분석
        if any(word in question_lower for word in ['vs', '비교', '대비', '차이']):
            return self._analyze_comparison(question, all_data)
        
        # 🔍 7. 기본 개요 분석
        return self._analyze_overview(question, all_data)

    def _analyze_specific_service_code(self, service_code, question, all_data):
        """특정 서비스 코드 분석 (DATA001, IOT002 등)"""
        
        response = f"🎯 **{service_code} 서비스 상세 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        # 해당 서비스 코드를 포함한 모든 서비스 찾기
        matching_services = set()
        service_data = {}
        
        for month, df in all_data.items():
            if 'service_code' in df.columns:
                matches = df[df['service_code'] == service_code]
                if len(matches) > 0:
                    for _, row in matches.iterrows():
                        service_full_name = row.get('full_service_id', '')
                        matching_services.add(service_full_name)
                        
                        if service_full_name not in service_data:
                            service_data[service_full_name] = {}
                        
                        service_data[service_full_name][month] = {
                            'billing_amount': row.get('billing_amount', 0),
                            'line_count': row.get('line_count', 0),
                            'lob_name': row.get('lob_name', 'Unknown')
                        }
        
        if not matching_services:
            return f"❌ **'{service_code}' 서비스를 찾을 수 없습니다**\n\n다른 서비스 코드를 확인해주세요."
        
        response += f"📋- **발견된 서비스**: {len(matching_services)}개\n\n"
        
        # 각 서비스별 상세 분석
        for service_name in sorted(matching_services):
            response += f"### 🔸 {service_name}\n\n"
            
            monthly_data = service_data[service_name]
            sorted_months = sorted(monthly_data.keys())
            
            if len(sorted_months) < 2:
                response += "⚠️ 충분한 월별 데이터가 없습니다.\n\n"
                continue
            
            # 월별 성과 표시
            response += "**📈 월별 성과**:\n\n"
            for month in sorted_months:
                data = monthly_data[month]
                amount = data['billing_amount']
                lines = data['line_count']
                arpu = amount / lines if lines > 0 else 0
                
                response += f"- **{month}**: {amount:,.0f}원, {lines:,.0f}회선, ARPU {arpu:,.0f}원\n"
            
            # 성장률 계산
            first_month_data = monthly_data[sorted_months[0]]
            last_month_data = monthly_data[sorted_months[-1]]
            
            first_amount = first_month_data['billing_amount']
            last_amount = last_month_data['billing_amount']
            
            if first_amount > 0:
                growth_rate = ((last_amount - first_amount) / first_amount) * 100
                
                response += f"\n**🚀 전체 성장률**: {growth_rate:+.1f}%\n"
                
                if growth_rate > 100:
                    evaluation = "🔥 폭발적 성장!"
                elif growth_rate > 50:
                    evaluation = "🚀 급성장!"
                elif growth_rate > 20:
                    evaluation = "📈 견실한 성장"
                elif growth_rate > 0:
                    evaluation = "➡️ 완만한 성장"
                else:
                    evaluation = "⚠️ 감소 추세"
                
                response += f"**평가**: {evaluation}\n\n"
                
                # 급성장 시점 분석 (질문에 "언제부터" 포함된 경우)
                if "언제부터" in question and "급성장" in question:
                    response += "**🔍 급성장 시점 분석**:\n\n"
                    
                    growth_points = []
                    for i in range(1, len(sorted_months)):
                        prev_month = sorted_months[i-1]
                        curr_month = sorted_months[i]
                        
                        prev_amount = monthly_data[prev_month]['billing_amount']
                        curr_amount = monthly_data[curr_month]['billing_amount']
                        
                        if prev_amount > 0:
                            month_growth = ((curr_amount - prev_amount) / prev_amount) * 100
                            if month_growth > 30:  # 30% 이상을 급성장으로 정의
                                growth_points.append({
                                    'month': curr_month,
                                    'growth': month_growth
                                })
                    
                    if growth_points:
                        first_growth_month = growth_points[0]['month']
                        response += f"**결론**: **{first_growth_month}부터** 급성장이 시작되었습니다!\n\n"
                        
                        for gp in growth_points:
                            response += f"- {gp['month']}: {gp['growth']:+.1f}% 급성장 🚀\n"
                    else:
                        response += "30% 이상의 급성장 구간을 찾을 수 없습니다.\n"
            
            response += "\n---\n\n"
        
        return response

    def _analyze_service_by_keyword(self, keywords, question, all_data):
        """키워드로 서비스 검색 및 분석"""
        
        response = f"🔍 **키워드 기반 서비스 분석**\n\n"
        response += f"**질문**: {question}\n"
        response += f"**검색 키워드**: {', '.join(keywords)}\n\n"
        
        # 키워드 매칭 서비스 찾기
        matching_services = set()
        
        for month, df in all_data.items():
            if 'full_service_id' in df.columns:
                for keyword in keywords:
                    matches = df[df['full_service_id'].str.contains(keyword, case=False, na=False)]
                    matching_services.update(matches['full_service_id'].tolist())
        
        if not matching_services:
            return f"❌ **'{', '.join(keywords)}' 관련 서비스를 찾을 수 없습니다**\n\n다른 키워드를 시도해보세요."
        
        response += f"- 📋 **발견된 서비스**: {len(matching_services)}개\n\n"
        
        # 최신 월 기준 성과 순위
        latest_month = max(all_data.keys())
        latest_data = all_data[latest_month]
        
        service_performance = []
        
        for service in matching_services:
            service_rows = latest_data[latest_data['full_service_id'] == service]
            if len(service_rows) > 0:
                row = service_rows.iloc[0]
                service_performance.append({
                    'service': service,
                    'amount': row.get('billing_amount', 0),
                    'lines': row.get('line_count', 0)
                })
        
        # 청구금액 순으로 정렬
        service_performance.sort(key=lambda x: x['amount'], reverse=True)
        
        response += f"- **📊 성과 순위** ({latest_month} 기준):\n\n"
        
        for i, sp in enumerate(service_performance[:10], 1):  # 상위 10개만
            service = sp['service']
            amount = sp['amount']
            lines = sp['lines']
            arpu = amount / lines if lines > 0 else 0
            
            rank_emoji = "- 🥇" if i == 1 else "- 🥈" if i == 2 else "- 🥉" if i == 3 else f"{i}."
            
            response += f"- {rank_emoji} **{service}**\n"
            response += f"- 💰 {amount:,.0f}원, 📱 {lines:,.0f}회선, ARPU {arpu:,.0f}원\n\n"
        
        return response

    def _analyze_top_ranking(self, question, all_data):
        """TOP/순위 분석"""
        
        # TOP 숫자 추출
        top_match = re.search(r'(top|톱|상위)\s*(\d+)', question.lower())
        top_count = int(top_match.group(2)) if top_match else 10
        
        response = f"🏆 **TOP {top_count} 서비스 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        # 최신 월 데이터 기준
        latest_month = max(all_data.keys())
        latest_data = all_data[latest_month]
        
        if 'full_service_id' not in latest_data.columns:
            return "❌ 서비스 데이터를 찾을 수 없습니다."
        
        # 서비스별 집계
        service_summary = latest_data.groupby('full_service_id').agg({
            'billing_amount': 'sum',
            'line_count': 'sum'
        }).fillna(0)
        
        # 청구금액 순으로 정렬
        service_summary = service_summary.sort_values('billing_amount', ascending=False)
        
        response += f"**📊 TOP {top_count} 서비스** ({latest_month} 기준):\n\n"
        
        for i, (service, data) in enumerate(service_summary.head(top_count).iterrows(), 1):
            amount = data['billing_amount']
            lines = data['line_count']
            arpu = amount / lines if lines > 0 else 0
            
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            response += f"{rank_emoji} **{service}**\n"
            response += f"   💰 {amount:,.0f}원\n"
            response += f"   📱 {lines:,.0f}회선\n"
            response += f"   💎 ARPU {arpu:,.0f}원\n\n"
        
        # 성장률 기준 TOP도 제공 (2개월 이상 데이터가 있는 경우)
        if len(all_data) >= 2:
            response += self._add_growth_ranking(all_data, top_count)
        
        return response

    def _add_growth_ranking(self, all_data, top_count):
        """성장률 기준 랭킹 추가"""
        
        months = sorted(all_data.keys())
        if len(months) < 2:
            return ""
        
        first_month = months[0]
        last_month = months[-1]
        
        # 성장률 계산
        growth_data = []
        
        # 공통 서비스 찾기
        first_services = set(all_data[first_month]['full_service_id'].dropna())
        last_services = set(all_data[last_month]['full_service_id'].dropna())
        common_services = first_services.intersection(last_services)
        
        for service in common_services:
            first_amount = all_data[first_month][all_data[first_month]['full_service_id'] == service]['billing_amount'].sum()
            last_amount = all_data[last_month][all_data[last_month]['full_service_id'] == service]['billing_amount'].sum()
            
            if first_amount > 0:
                growth_rate = ((last_amount - first_amount) / first_amount) * 100
                growth_data.append({
                    'service': service,
                    'growth_rate': growth_rate,
                    'first_amount': first_amount,
                    'last_amount': last_amount
                })
        
        # 성장률 순으로 정렬
        growth_data.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        response = f"\n**🚀 성장률 TOP {top_count}** ({first_month} → {last_month}):\n\n"
        
        for i, gd in enumerate(growth_data[:top_count], 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            response += f"{rank_emoji} **{gd['service']}**\n"
            response += f"   📈 성장률: {gd['growth_rate']:+.1f}%\n"
            response += f"   💰 {gd['first_amount']:,.0f}원 → {gd['last_amount']:,.0f}원\n\n"
        
        return response

    def _analyze_growth_trend(self, question, all_data):
        """성장률/트렌드 분석"""
        
        response = f"📈 **성장률 & 트렌드 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        months = sorted(all_data.keys())
        if len(months) < 2:
            return "❌ 트렌드 분석을 위해서는 최소 2개월 데이터가 필요합니다."
        
        response += f"**📊 분석 기간**: {months[0]} ~ {months[-1]} ({len(months)}개월)\n\n"
        
        # 전체 시장 트렌드
        monthly_totals = []
        for month in months:
            total_amount = all_data[month]['billing_amount'].sum()
            total_lines = all_data[month]['line_count'].sum()
            monthly_totals.append({
                'month': month,
                'amount': total_amount,
                'lines': total_lines
            })
        
        response += "**🌟 전체 시장 트렌드**:\n\n"
        
        for i, mt in enumerate(monthly_totals):
            growth_indicator = ""
            if i > 0:
                prev_amount = monthly_totals[i-1]['amount']
                if prev_amount > 0:
                    monthly_growth = ((mt['amount'] - prev_amount) / prev_amount) * 100
                    if monthly_growth > 5:
                        growth_indicator = f" 📈 ({monthly_growth:+.1f}%)"
                    elif monthly_growth < -5:
                        growth_indicator = f" 📉 ({monthly_growth:+.1f}%)"
                    else:
                        growth_indicator = f" ➡️ ({monthly_growth:+.1f}%)"
            
            response += f"- **{mt['month']}**: {mt['amount']:,.0f}원, {mt['lines']:,.0f}회선{growth_indicator}\n"
        
        # 전체 성장률
        if monthly_totals[0]['amount'] > 0:
            total_growth = ((monthly_totals[-1]['amount'] - monthly_totals[0]['amount']) / monthly_totals[0]['amount']) * 100
            response += f"\n**🎯 전체 성장률**: {total_growth:+.1f}%\n\n"
        
        # 고성장 서비스 TOP 5
        response += self._add_growth_ranking(all_data, 5)
        
        return response

    def _analyze_lob_performance(self, question, all_data):
        """LOB/사업부별 성과 분석"""
        
        response = f"🏢 **LOB별 성과 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        latest_month = max(all_data.keys())
        latest_data = all_data[latest_month]
        
        if 'lob_name' not in latest_data.columns:
            return "❌ LOB 정보를 찾을 수 없습니다."
        
        # LOB별 집계
        lob_summary = latest_data.groupby('lob_name').agg({
            'billing_amount': 'sum',
            'line_count': 'sum'
        }).fillna(0)
        
        lob_summary = lob_summary.sort_values('billing_amount', ascending=False)
        
        response += f"**📊 LOB별 성과** ({latest_month} 기준):\n\n"
        
        for i, (lob, data) in enumerate(lob_summary.iterrows(), 1):
            amount = data['billing_amount']
            lines = data['line_count']
            arpu = amount / lines if lines > 0 else 0
            
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            response += f"{rank_emoji} **{lob}**\n"
            response += f"   💰 {amount/100000000:.1f}억원\n"
            response += f"   📱 {lines/10000:.1f}만 회선\n"
            response += f"   💎 ARPU {arpu:,.0f}원\n\n"
        
        return response

    def _analyze_comparison(self, question, all_data):
        """비교 분석"""
        
        response = f"⚖️ **비교 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        # 비교 대상 추출 시도
        comparison_keywords = re.findall(r'(\w+)\s*(?:vs|비교|대비)\s*(\w+)', question.lower())
        
        if comparison_keywords:
            keyword1, keyword2 = comparison_keywords[0]
            response += f"**🔍 비교 대상**: {keyword1} vs {keyword2}\n\n"
            
            # 각 키워드에 해당하는 서비스 찾기
            latest_month = max(all_data.keys())
            latest_data = all_data[latest_month]
            
            services1 = latest_data[latest_data['full_service_id'].str.contains(keyword1, case=False, na=False)]
            services2 = latest_data[latest_data['full_service_id'].str.contains(keyword2, case=False, na=False)]
            
            if len(services1) > 0 and len(services2) > 0:
                amount1 = services1['billing_amount'].sum()
                amount2 = services2['billing_amount'].sum()
                lines1 = services1['line_count'].sum()
                lines2 = services2['line_count'].sum()
                
                response += f"**📊 {keyword1.upper()} 계열**:\n"
                response += f"- 💰 청구금액: {amount1:,.0f}원\n"
                response += f"- 📱 회선수: {lines1:,.0f}개\n"
                response += f"- 💎 ARPU: {amount1/lines1 if lines1 > 0 else 0:,.0f}원\n\n"
                
                response += f"**📊 {keyword2.upper()} 계열**:\n"
                response += f"- 💰 청구금액: {amount2:,.0f}원\n"
                response += f"- 📱 회선수: {lines2:,.0f}개\n"
                response += f"- 💎 ARPU: {amount2/lines2 if lines2 > 0 else 0:,.0f}원\n\n"
                
                # 승부 결과
                if amount1 > amount2:
                    winner = keyword1.upper()
                    margin = ((amount1 - amount2) / amount2) * 100
                else:
                    winner = keyword2.upper()
                    margin = ((amount2 - amount1) / amount1) * 100
                
                response += f"**🏆 결과**: {winner} 승! ({margin:.1f}% 차이)\n"
            else:
                response += "❌ 비교할 서비스를 찾을 수 없습니다.\n"
        else:
            response += "❌ 비교 대상을 명확히 지정해주세요. (예: 5G vs LTE)\n"
        
        return response

    def _analyze_overview(self, question, all_data):
        """기본 개요 분석"""
        
        response = f"📊 **Azure 청구 데이터 종합 분석**\n\n"
        response += f"**질문**: {question}\n\n"
        
        # 기본 통계
        total_months = len(all_data)
        months = sorted(all_data.keys())
        
        response += f"**📋 데이터 현황**:\n"
        response += f"- 분석 기간: {months[0]} ~ {months[-1]} ({total_months}개월)\n"
        
        # 최신 월 기준 통계
        latest_month = months[-1]
        latest_data = all_data[latest_month]
        
        total_services = len(latest_data['full_service_id'].unique()) if 'full_service_id' in latest_data.columns else 0
        total_amount = latest_data['billing_amount'].sum()
        total_lines = latest_data['line_count'].sum()
        
        response += f"- 전체 서비스: {total_services}개\n"
        response += f"- 총 청구금액: {total_amount/100000000:.1f}억원\n"
        response += f"- 총 회선수: {total_lines/10000:.1f}만개\n"
        response += f"- 평균 ARPU: {total_amount/total_lines if total_lines > 0 else 0:,.0f}원\n\n"
        
        # LOB 분포 (있는 경우)
        if 'lob_name' in latest_data.columns:
            lob_count = len(latest_data['lob_name'].unique())
            response += f"**🏢 사업부(LOB)**: {lob_count}개\n\n"
            
            lob_summary = latest_data.groupby('lob_name')['billing_amount'].sum().sort_values(ascending=False)
            for lob, amount in lob_summary.head(3).items():
                response += f"- {lob}: {amount/100000000:.1f}억원\n"
        
        response += f"\n**💡 분석 팁**:\n"
        response += f"- 특정 서비스 분석: '데이터101 서비스 언제부터 급성장했어?'\n"
        response += f"- 순위 분석: '고성장 서비스 TOP 10'\n"
        response += f"- 비교 분석: '5G vs LTE 성과 비교'\n"
        response += f"- LOB 분석: 'LOB별 성과 순위'\n"
        
        return response


def handle_azure_ai_query(user_question):
    """Azure AI 질문 처리 함수 (메인 진입점)"""
    
    if not user_question or user_question.strip() == "":
        return "❓ **질문을 입력해주세요**\n\n분석하고 싶은 내용을 구체적으로 말씀해주세요."
    
    # Azure Helper 초기화
    azure_helper = AzureHelper()
    
    if not azure_helper.connected:
        return """❌ **Azure 연결 실패**

**해결 방법**:
1. `.env` 파일에 `AZURE_STORAGE_CONNECTION_STRING` 확인
2. Azure Storage 계정 접근 권한 확인
3. `billing-data` 컨테이너 존재 여부 확인

연결 후 다시 시도해주세요."""
    
    # 분석 실행
    try:
        with st.spinner("🤖 Azure 데이터를 분석하고 있습니다..."):
            result = azure_helper.analyze_service_query(user_question)
        
        return result
        
    except Exception as e:
        error_msg = f"""❌ **분석 중 오류 발생**

**오류 내용**: {str(e)}

**해결 방법**:
- 네트워크 연결 확인
- Azure Storage 접근 권한 확인  
- 데이터 파일 형식 확인
- 다시 시도

**지원**: 문제가 지속되면 시스템 관리자에게 문의하세요."""
        
        return error_msg


# 🎯 사용 예시 및 테스트 함수들 (옵션)
def test_azure_analysis():
    """테스트용 함수"""
    test_questions = [
        "DATA001 서비스가 언제부터 급성장했어?",
        "고성장 서비스 TOP 5",
        "5G vs LTE 성과 비교",
        "LOB별 성과 순위",
        "IOT 서비스들 성장률은?"
    ]
    
    for question in test_questions:
        print(f"\n🔍 테스트 질문: {question}")
        result = handle_azure_ai_query(question)
        print(result)
        print("="*50)

if __name__ == "__main__":
    # 직접 실행 시 테스트
    test_azure_analysis()