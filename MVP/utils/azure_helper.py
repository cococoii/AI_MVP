# utils/azure_ai_helper.py - Blob Storage에서 AI 분석
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
    """Azure Blob Storage + AI 분석 도우미"""
    
    def __init__(self):
        self.setup_connection()
        self.available_files = []
        self.months = []
        
        # Blob Storage의 월별 데이터 경로
        self.monthly_data_paths = {
            "2025-01": "monthly_data/billing_data_2025_01.csv",
            "2025-02": "monthly_data/billing_data_2025_02.csv", 
            "2025-03": "monthly_data/billing_data_2025_03.csv",
            "2025-04": "monthly_data/billing_data_2025_04.csv",
            "2025-05": "monthly_data/billing_data_2025_05.csv",
            "2025-06": "monthly_data/billing_data_2025_06.csv"
        }
        
        # 메타데이터 경로
        self.metadata_paths = {
            "5G 프리미엄 월정액": "plan_metadata/5G_프리미엄_월정액_metadata.json",
            "LTE 무제한 월정액": "plan_metadata/LTE_무제한_월정액_metadata.json",
            "IoT 센서 월정액": "plan_metadata/IoT_센서_월정액_metadata.json",
            "VPN 서비스 월정액": "plan_metadata/VPN_서비스_월정액_metadata.json",
            "가족 무제한 월정액": "plan_metadata/가족_무제한_월정액_metadata.json",
            "국제통화 사용료": "plan_metadata/국제통화_사용료_metadata.json",
            "기업 전용선 월정액": "plan_metadata/기업_전용선_월정액_metadata.json",
            "기업전용 패키지 월정액": "plan_metadata/기업전용_패키지_월정액_metadata.json",
            "데이터 사용료": "plan_metadata/데이터_사용료_metadata.json",
            "스마트홈 연결료": "plan_metadata/스마트홈_연결료_metadata.json",
            "시니어 안심 월정액": "plan_metadata/시니어_안심_월정액_metadata.json",
            "음성통화 사용료": "plan_metadata/음성통화_사용료_metadata.json",
            "차량용 단말 월정액": "plan_metadata/차량용_단말_월정액_metadata.json",
            "청소년 요금제 월정액": "plan_metadata/청소년_요금제_월정액_metadata.json",
            "컬러링 서비스": "plan_metadata/컬러링_서비스_metadata.json",
            "클라우드 백업 서비스": "plan_metadata/클라우드_백업_서비스_metadata.json",
            "클라우드 연결 서비스": "plan_metadata/클라우드_연결_서비스_metadata.json",
            "통화대기 서비스": "plan_metadata/통화대기_서비스_metadata.json"
        }
        
    def setup_connection(self):
        """Azure 연결 설정"""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.connected = False
        
        if connection_string:
            try:
                self.client = BlobServiceClient.from_connection_string(connection_string)
                self.connected = True
            except Exception as e:
                st.error(f"Azure 연결 실패: {e}")

    def upload_csv(self, df, filename):
        if not self.connected:
            return False, "Azure 연결 안됨"
        
        try:
            csv_string = df.to_csv(index=False, encoding='utf-8-sig')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"uploads/{timestamp}_{filename}"
            
            blob_client = self.client.get_blob_client(
                container="billing-data", 
                blob=blob_name
            )
            blob_client.upload_blob(csv_string, overwrite=True)
            return True, blob_name
        except Exception as e:
            return False, str(e)
        
    def _discover_available_files(self):
        """Azure Blob Storage에서 모든 청구 데이터 파일 자동 탐지"""
        try:
            container_client = self.client.get_container_client("billing-data")
            
            # 모든 blob 목록 가져오기
            blob_list = container_client.list_blobs()
            print(blob_list)  # 디버깅용 출력
            
            billing_files = []
            
            for blob in blob_list:
                blob_name = blob.name
                
                # CSV 파일이고 billing_data로 시작하는 파일들 찾기
                if (blob_name.endswith('.csv') and 
                    ('billing_data' in blob_name.lower() or 'billing' in blob_name.lower())):
                    
                    # 월 정보 추출 시도
                    month_match = re.search(r'20\d{2}[-_]?\d{2}', blob_name)
                    if month_match:
                        month_str = month_match.group().replace('_', '-')
                        if len(month_str) == 7:  # 2025-01 형태
                            billing_files.append({
                                'blob_name': blob_name,
                                'month': month_str,
                                'size': blob.size,
                                'last_modified': blob.last_modified
                            })
                    else:
                        # 월 정보가 없어도 청구 데이터로 보이면 포함
                        billing_files.append({
                            'blob_name': blob_name,
                            'month': 'unknown',
                            'size': blob.size,
                            'last_modified': blob.last_modified
                        })
            
            # 월순으로 정렬
            billing_files.sort(key=lambda x: x['month'] if x['month'] != 'unknown' else '9999-99')
            
            self.available_files = billing_files
            self.months = [f['month'] for f in billing_files if f['month'] != 'unknown']
            
            st.success(f"✅ {len(billing_files)}개 청구 데이터 파일 발견!")
            
            # # 발견된 파일들 표시
            # if billing_files:
            #     st.info("📁 **발견된 파일들:**")
            #     for file_info in billing_files:
            #         size_kb = file_info['size'] / 1024
            #         st.text(f"  📄 {file_info['blob_name']} ({file_info['month']}) - {size_kb:.1f}KB")
            
        except Exception as e:
            st.error(f"파일 탐지 실패: {e}")
            self.available_files = []
            self.months = []

    def analyze_service_query(self, user_question):
        """서비스별 정확한 분석 (자동 파일 탐지)"""
        if not self.connected:
            return "❌ Azure 연결이 필요합니다"
        
        self._discover_available_files()
        
        if not self.available_files:
            return "❌ 분석할 청구 데이터 파일을 찾을 수 없습니다"
        
        try:
            # 1. 모든 발견된 파일에서 데이터 수집
            all_monthly_data = self._collect_all_discovered_data()
            
            # 2. 고유 서비스 목록 생성
            unique_services = self._get_unique_services(all_monthly_data)
            
            # 3. 질문에서 타겟 서비스 찾기
            target_services = self._find_target_services(user_question, unique_services, all_monthly_data)
            
            # 4. 서비스별 완전한 이력 분석
            analysis_result = self._analyze_service_history(target_services, all_monthly_data, user_question)
            
            return analysis_result
            
        except Exception as e:
            return f"❌ 분석 중 오류: {e}"
    
    def _collect_all_discovered_data(self):
        """발견된 모든 파일에서 데이터 수집"""
        all_data = {}
        
        for file_info in self.available_files:
            blob_name = file_info['blob_name']
            month = file_info['month']
            
            try:
                df = self._download_csv_from_blob(blob_name)
                
                if df is not None and len(df) > 0:
                    # 고유 서비스 ID 생성
                    if '청구항목명' in df.columns and '단위서비스명' in df.columns:
                        df['서비스_ID'] = df['청구항목명'] + " (" + df['단위서비스명'] + ")"
                    else:
                        # 컬럼명이 다를 수 있으므로 유연하게 처리
                        billing_col = self._find_column(df, ['청구항목명', '항목명', 'item_name', 'plan_name'])
                        service_col = self._find_column(df, ['단위서비스명', '서비스명', 'service_name', 'unit_service'])
                        
                        if billing_col and service_col:
                            df['서비스_ID'] = df[billing_col] + " (" + df[service_col] + ")"
                        else:
                            # 서비스 ID를 만들 수 없으면 청구항목명만 사용
                            df['서비스_ID'] = df[billing_col] if billing_col else df.index.astype(str)
                    
                    all_data[month] = df
                    
            except Exception as e:
                st.warning(f"⚠️ {blob_name} 로드 실패: {e}")
        
        return all_data
    
    def _find_column(self, df, candidates):
        """컬럼명 후보 중에서 실제 존재하는 컬럼 찾기"""
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
            # 대소문자 무시하고 찾기
            for col in df.columns:
                if candidate.lower() == col.lower():
                    return col
        return None
    
    def _download_csv_from_blob(self, blob_name):
        """Azure에서 CSV 다운로드"""
        try:
            blob_client = self.client.get_blob_client(
                container="billing-data",
                blob=blob_name
            )
            
            csv_content = blob_client.download_blob().readall().decode('utf-8-sig')
            return pd.read_csv(io.StringIO(csv_content))
            
        except Exception as e:
            return None
    
    def _get_unique_services(self, all_monthly_data):
        """전체 기간의 고유 서비스 목록"""
        unique_services = set()
        
        for month, df in all_monthly_data.items():
            if '서비스_ID' in df.columns:
                services = df['서비스_ID'].tolist()
                unique_services.update(services)
        
        return sorted(list(unique_services))
    
    def _find_target_services(self, question, unique_services, all_monthly_data):
        """질문에서 타겟 서비스 찾기"""
        question_lower = question.lower()
        matching_services = []
        
        # 키워드 기반 서비스 매칭
        service_keywords = {
            "5g": ["5g", "프리미엄"],
            "lte": ["lte", "무제한"],
            "iot": ["iot", "센서", "스마트홈", "사물인터넷"],
            "차량": ["차량", "단말", "auto"],
            "기업": ["기업", "비즈니스", "corp", "busi"],
            "vpn": ["vpn", "브이피엔"],
            "클라우드": ["클라우드", "cloud", "백업"],
            "음성": ["음성", "통화", "voice"],
            "데이터": ["데이터", "data"],
            "부가": ["부가", "addon", "컬러링", "통화대기"]
        }
        
        # 단위서비스 코드 직접 매칭
        unit_service_codes = re.findall(r'\b[A-Z]{2,}[0-9]{2,3}\b', question.upper())
        
        for service in unique_services:
            # 1. 단위서비스 코드 직접 매칭
            for code in unit_service_codes:
                if code in service:
                    matching_services.append(service)
                    break
            
            # 2. 키워드 매칭
            service_added = False
            for category, keywords in service_keywords.items():
                if service_added:
                    break
                if any(keyword in question_lower for keyword in keywords):
                    if any(keyword in service.lower() for keyword in keywords):
                        if service not in matching_services:
                            matching_services.append(service)
                            service_added = True
        
        # 매칭된 서비스가 없으면 상위 10개 서비스 반환
        if not matching_services:
            # 가장 최근 월 기준 상위 10개
            if all_monthly_data:
                latest_month = max(all_monthly_data.keys())
                latest_data = all_monthly_data[latest_month]
                
                # 청구금액 컬럼 찾기
                amount_col = self._find_column(latest_data, ['청구금액', 'amount', 'billing_amount'])
                
                if amount_col:
                    top_services = latest_data.nlargest(10, amount_col)['서비스_ID'].tolist()
                    matching_services = top_services
                else:
                    # 청구금액 컬럼이 없으면 처음 10개
                    matching_services = unique_services[:10]
        
        return matching_services[:15]  # 최대 15개까지
    
    def _analyze_service_history(self, target_services, all_monthly_data, question):
        """서비스별 완전한 이력 분석"""
        if not target_services:
            return "❌ 분석할 서비스를 찾을 수 없습니다"
        
        response = f"📊 **자동 탐지 서비스 분석** (총 {len(target_services)}개 서비스)\n\n"
        response += f"🔍 **분석 기간**: {len(all_monthly_data)}개월 데이터 ({', '.join(sorted(all_monthly_data.keys()))})\n\n"
        
        for i, service_id in enumerate(target_services, 1):
            response += f"## {i}. {service_id}\n\n"
            
            # 서비스 이력 추출
            service_history = []
            
            for month in sorted(all_monthly_data.keys()):
                df = all_monthly_data[month]
                service_data = df[df['서비스_ID'] == service_id]
                
                if len(service_data) > 0:
                    row = service_data.iloc[0]
                    
                    # 유연한 컬럼 매핑
                    amount_col = self._find_column(df, ['청구금액', 'amount', 'billing_amount'])
                    lines_col = self._find_column(df, ['회선수', 'lines', 'line_count'])
                    arpu_col = self._find_column(df, ['ARPU', 'arpu', 'avg_revenue'])
                    discount_col = self._find_column(df, ['할인금액', 'discount_amount', 'discount'])
                    
                    service_history.append({
                        "월": month,
                        "청구금액": row.get(amount_col, 0) if amount_col else 0,
                        "회선수": row.get(lines_col, 0) if lines_col else 0,
                        "ARPU": row.get(arpu_col, 0) if arpu_col else 0,
                        "할인금액": row.get(discount_col, 0) if discount_col else 0,
                        "청구항목명": row.get('청구항목명', row.get('항목명', '')),
                        "단위서비스명": row.get('단위서비스명', row.get('서비스명', '')),
                        "LOB": row.get('lob명', row.get('LOB', ''))
                    })
            
            if service_history:
                # 서비스 기본 정보
                first_record = service_history[0]
                response += f"**📋 서비스 정보:**\n"
                response += f"* 청구항목명: {first_record['청구항목명']}\n"
                response += f"* 단위서비스: {first_record['단위서비스명']}\n"
                response += f"* LOB: {first_record['LOB']}\n"
                response += f"* 데이터 시작: {first_record['월']}\n"
                response += f"* 추적 기간: {len(service_history)}개월\n\n"
                
                # 월별 상세 이력
                response += f"**📈 월별 서비스 이력:**\n"
                for record in service_history:
                    response += f"* **{record['월']}**: "
                    response += f"청구 {record['청구금액']:,}원, "
                    response += f"회선 {record['회선수']:,}개"
                    
                    if record['ARPU'] > 0:
                        response += f", ARPU {record['ARPU']:,.0f}원"
                    if record['할인금액'] > 0:
                        response += f", 할인 {record['할인금액']:,}원"
                    response += "\n"
                
                # 트렌드 분석
                if len(service_history) >= 2:
                    first_amount = service_history[0]['청구금액']
                    last_amount = service_history[-1]['청구금액']
                    
                    first_lines = service_history[0]['회선수']
                    last_lines = service_history[-1]['회선수']
                    
                    total_growth = ((last_amount - first_amount) / first_amount * 100) if first_amount > 0 else 0
                    lines_growth = ((last_lines - first_lines) / first_lines * 100) if first_lines > 0 else 0
                    
                    response += f"\n**📊 전체 성과 ({len(service_history)}개월):**\n"
                    response += f"* 청구금액 변화: {total_growth:+.1f}%\n"
                    response += f"* 회선수 변화: {lines_growth:+.1f}%\n"
                    
                    # 성과 평가
                    if total_growth > 100:
                        response += "🔥 **폭발적 성장!** 매우 성공적인 서비스\n"
                    elif total_growth > 50:
                        response += "🚀 **급성장** 우수한 성과\n"
                    elif total_growth > 20:
                        response += "📈 **꾸준한 성장** 안정적 발전\n"
                    elif total_growth > -10:
                        response += "➡️ **안정적** 현상 유지\n"
                    else:
                        response += "⚠️ **감소세** 개선 필요\n"
                
                response += "\n---\n\n"
            else:
                response += "❌ 해당 서비스의 이력을 찾을 수 없습니다\n\n---\n\n"
        
        # 시스템 정보
        response += "## 🔧 **자동 탐지 시스템 정보**\n\n"
        response += f"📁 **발견된 파일**: {len(self.available_files)}개\n"
        response += f"📅 **분석 기간**: {len(all_monthly_data)}개월\n"
        response += f"🏷️ **총 서비스**: {len(self._get_unique_services(all_monthly_data))}개\n"
        response += f"💡 **장점**: 새로운 월 데이터 업로드시 자동으로 포함됩니다!\n"
        
        return response

def handle_azure_ai_query(user_question):
    """자동 탐지 Azure AI 질문 처리"""
    azure_ai = AzureHelper()
    
    if not azure_ai.connected:
        return "❌ Azure Blob Storage에 연결할 수 없습니다. 연결 설정을 확인하세요."
    
    # AI 분석 실행
    with st.spinner("🤖 Azure에서 데이터 분석 중..."):
        ai_response = azure_ai.analyze_service_query(user_question)
    
    
    return ai_response