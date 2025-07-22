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
            
            # ✅ 누락된 메타데이터들 추가
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

    def analyze_plan_query(self, user_question):
        """사용자 질문 분석해서 요금제 정보 제공"""
        if not self.connected:
            return "❌ Azure에 연결되지 않았습니다"
        
        try:
            # 1. 질문에서 요금제명 추출
            plan_names = self.extract_plan_names(user_question)
            
            # 2. 질문에서 월 정보 추출
            months = self.extract_months(user_question)
            
            # 3. 질문 유형 분석
            query_type = self.analyze_query_type(user_question)
            
            # 4. Blob Storage에서 데이터 조회
            plan_data = self.fetch_plan_data(plan_names, months)
            
            # 5. AI 분석 결과 생성
            ai_response = self.generate_ai_response(user_question, plan_data, query_type)
            
            return ai_response
            
        except Exception as e:
            return f"❌ 분석 중 오류 발생: {e}"
    
    def extract_plan_names(self, question):
        """질문에서 요금제명 추출"""
        plan_keywords = {
            "5G 프리미엄": ["5g", "프리미엄", "5G 프리미엄", "프리미엄 5G"],
            "LTE 무제한": ["lte", "무제한", "LTE 무제한", "무제한 LTE"],
            "IoT 센서": ["iot", "센서", "사물인터넷", "IoT 센서"],
            "기업전용 패키지": ["기업", "비즈니스", "기업전용", "패키지"],
            "차량용 단말": ["차량", "자동차", "차량용", "단말"],
            "VPN 서비스": ["vpn", "브이피엔", "VPN"],
            "클라우드": ["클라우드", "cloud", "백업"]
        }
        
        found_plans = []
        question_lower = question.lower()
        
        for plan_name, keywords in plan_keywords.items():
            if any(keyword.lower() in question_lower for keyword in keywords):
                found_plans.append(plan_name)
        
        return found_plans if found_plans else ["전체"]  # 특정 요금제 없으면 전체 분석
    
    def extract_months(self, question):
        """질문에서 월 정보 추출"""
        # 월 패턴 찾기
        month_patterns = [
            r'2025[-.]?0?([1-6])월?',  # 2025-01, 2025.1월 등
            r'([1-6])월',               # 1월, 6월 등
            r'(1월|2월|3월|4월|5월|6월)', # 한글 월
            r'(상반기|전체)'            # 전체 기간
        ]
        
        months = []
        for pattern in month_patterns:
            matches = re.findall(pattern, question)
            for match in matches:
                if match in ['1', '2', '3', '4', '5', '6']:
                    months.append(f"2025-{int(match):02d}")
                elif match in ['1월', '2월', '3월', '4월', '5월', '6월']:
                    month_num = int(match.replace('월', ''))
                    months.append(f"2025-{month_num:02d}")
                elif match in ['상반기', '전체']:
                    months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
                    break
        
        return months if months else ["2025-06"]  # 기본값: 최근 월
    
    def analyze_query_type(self, question):
        """질문 유형 분석"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['왜', '이유', '원인', 'why']):
            return "원인분석"
        elif any(word in question_lower for word in ['어떻게', '방법', '개선', 'how']):
            return "개선방안"
        elif any(word in question_lower for word in ['언제', '시점', '출시', 'when']):
            return "시점분석"
        elif any(word in question_lower for word in ['비교', '차이', 'vs', '대비']):
            return "비교분석"
        elif any(word in question_lower for word in ['트렌드', '변화', '추세', 'trend']):
            return "트렌드분석"
        elif any(word in question_lower for word in ['할인', '프로모션', '혜택']):
            return "할인분석"
        else:
            return "기본분석"
    
    def fetch_plan_data(self, plan_names, months):
        """Azure Blob Storage에서 요금제 데이터 조회"""
        plan_data = {}
        
        for month in months:
            if month not in self.monthly_data_paths:
                continue
            
            try:
                # CSV 파일 다운로드
                blob_path = self.monthly_data_paths[month]
                df = self.download_csv_from_blob(blob_path)
                
                if df is not None:
                    # 요금제별 필터링
                    if "전체" not in plan_names:
                        # 특정 요금제만 필터링
                        filtered_df = pd.DataFrame()
                        for plan_name in plan_names:
                            plan_rows = df[df['청구항목명'].str.contains(plan_name, case=False, na=False)]
                            filtered_df = pd.concat([filtered_df, plan_rows])
                        df = filtered_df
                    
                    plan_data[month] = df
                    
            except Exception as e:
                st.error(f"{month} 데이터 로드 실패: {e}")
        
        return plan_data
    
    def download_csv_from_blob(self, blob_path):
        """Blob에서 CSV 다운로드"""
        try:
            blob_client = self.client.get_blob_client(
                container="billing-data",
                blob=blob_path
            )
            
            csv_content = blob_client.download_blob().readall().decode('utf-8-sig')
            
            # ✅ pd.StringIO → io.StringIO 변경
            return pd.read_csv(io.StringIO(csv_content))
            
        except Exception as e:
            st.error(f"Blob 다운로드 실패 ({blob_path}): {e}")
            return None
    
    def generate_ai_response(self, question, plan_data, query_type):
        """AI 분석 응답 생성"""
        if not plan_data:
            return "❌ 요청하신 데이터를 찾을 수 없습니다"
        
        # 데이터 분석
        analysis_result = self.analyze_data(plan_data, query_type)
        
        # 질문 유형별 응답 생성
        if query_type == "원인분석":
            return self.create_cause_analysis_response(question, analysis_result)
        elif query_type == "트렌드분석":
            return self.create_trend_analysis_response(question, analysis_result)
        elif query_type == "할인분석":
            return self.create_discount_analysis_response(question, analysis_result)
        elif query_type == "비교분석":
            return self.create_comparison_response(question, analysis_result)
        else:
            return self.create_basic_response(question, analysis_result)
    
    def analyze_data(self, plan_data, query_type):
        """데이터 분석 수행"""
        result = {
            "months": list(plan_data.keys()),
            "total_items": 0,
            "monthly_summary": {},
            "trends": {},
            "top_plans": [],
            "discount_info": {}
        }
        
        monthly_totals = {}
        
        for month, df in plan_data.items():
            if df.empty:
                continue
            
            # 월별 요약
            month_summary = {
                "total_amount": df['청구금액'].sum() if '청구금액' in df.columns else 0,
                "total_lines": df['회선수'].sum() if '회선수' in df.columns else 0,
                "total_discount": df['할인금액'].sum() if '할인금액' in df.columns else 0,
                "item_count": len(df)
            }
            
            result["monthly_summary"][month] = month_summary
            monthly_totals[month] = month_summary["total_amount"]
            
            # 상위 요금제 (최근 월 기준)
            if month == max(plan_data.keys()):
                if '청구항목명' in df.columns and '청구금액' in df.columns:
                    top_plans = df.nlargest(5, '청구금액')[['청구항목명', '청구금액', '할인율']]
                    result["top_plans"] = top_plans.to_dict('records')
        
        # 트렌드 분석
        if len(monthly_totals) >= 2:
            months_sorted = sorted(monthly_totals.keys())
            first_month = monthly_totals[months_sorted[0]]
            last_month = monthly_totals[months_sorted[-1]]
            
            if first_month > 0:
                growth_rate = ((last_month - first_month) / first_month) * 100
                result["trends"]["growth_rate"] = growth_rate
                result["trends"]["direction"] = "증가" if growth_rate > 0 else "감소"
        
        return result
    
    def create_trend_analysis_response(self, question, analysis):
        """트렌드 분석 응답"""
        months = analysis["months"]
        monthly_summary = analysis["monthly_summary"]
        trends = analysis.get("trends", {})
        
        response = f"📈 **요금제 트렌드 분석 ({min(months)} ~ {max(months)})**\n\n"
        
        # 월별 변화
        response += "**💰 월별 청구금액 변화:**\n"
        for month in sorted(months):
            if month in monthly_summary:
                amount = monthly_summary[month]["total_amount"]
                response += f"* {month}: {amount:,}원\n"
        
        # 성장률
        if "growth_rate" in trends:
            growth_rate = trends["growth_rate"]
            direction = trends["direction"]
            response += f"\n**📊 전체 성장률:** {growth_rate:+.1f}% ({direction})\n"
            
            if growth_rate > 20:
                response += "🔥 **급성장 중!** 마케팅 투자 확대 고려\n"
            elif growth_rate < -20:
                response += "⚠️ **급감세!** 요금제 개선 필요\n"
            else:
                response += "✅ **안정적 성장** 현 상태 유지\n"
        
        # 상위 요금제
        if analysis["top_plans"]:
            response += f"\n**🏆 주요 요금제 (최근 월 기준):**\n"
            for i, plan in enumerate(analysis["top_plans"][:3], 1):
                response += f"{i}. {plan['청구항목명']}: {plan['청구금액']:,}원\n"
        
        return response
    
    def create_discount_analysis_response(self, question, analysis):
        """할인 분석 응답"""
        months = analysis["months"]
        monthly_summary = analysis["monthly_summary"]
        
        response = f"💸 **할인 혜택 분석 ({min(months)} ~ {max(months)})**\n\n"
        
        total_discount = 0
        total_amount = 0
        
        # 월별 할인 현황
        response += "**📊 월별 할인 현황:**\n"
        for month in sorted(months):
            if month in monthly_summary:
                discount = monthly_summary[month]["total_discount"]
                amount = monthly_summary[month]["total_amount"]
                discount_rate = (discount / (amount + discount) * 100) if (amount + discount) > 0 else 0
                
                response += f"* {month}: {discount:,}원 할인 ({discount_rate:.1f}%)\n"
                total_discount += discount
                total_amount += amount
        
        # 전체 할인율
        overall_discount_rate = (total_discount / (total_amount + total_discount) * 100) if (total_amount + total_discount) > 0 else 0
        response += f"\n**💯 전체 할인율:** {overall_discount_rate:.1f}%\n"
        response += f"**💰 총 할인 혜택:** {total_discount:,}원\n"
        
        # 할인 수준 평가
        if overall_discount_rate >= 15:
            response += "🎉 **높은 할인율!** 고객 만족도 높을 것으로 예상\n"
        elif overall_discount_rate >= 8:
            response += "✅ **적정 할인율** 경쟁력 있는 수준\n"
        else:
            response += "💡 **할인 확대 고려** 고객 유치를 위한 프로모션 검토\n"
        
        return response
    
    def create_basic_response(self, question, analysis):
        """기본 분석 응답"""
        months = analysis["months"]
        monthly_summary = analysis["monthly_summary"]
        
        response = f"📊 **요금제 분석 결과 ({min(months)} ~ {max(months)})**\n\n"
        
        # 전체 현황
        total_amount = sum(summary["total_amount"] for summary in monthly_summary.values())
        total_lines = sum(summary["total_lines"] for summary in monthly_summary.values())
        total_discount = sum(summary["total_discount"] for summary in monthly_summary.values())
        
        response += f"**💰 총 청구금액:** {total_amount:,}원\n"
        response += f"**📱 총 회선수:** {total_lines:,}개\n"
        response += f"**💸 총 할인금액:** {total_discount:,}원\n"
        
        if total_lines > 0:
            avg_arpu = total_amount / total_lines
            response += f"**📊 평균 ARPU:** {avg_arpu:,.0f}원\n"
        
        # 상위 요금제
        if analysis["top_plans"]:
            response += f"\n**🏆 주요 요금제:**\n"
            for i, plan in enumerate(analysis["top_plans"][:5], 1):
                response += f"{i}. {plan['청구항목명']}: {plan['청구금액']:,}원"
                if '할인율' in plan and plan['할인율'] > 0:
                    response += f" ({plan['할인율']}% 할인)"
                response += "\n"
        
        return response

# 사용 예시 함수
def handle_azure_ai_query(user_question):
    """Azure AI 질문 처리 함수"""
    azure_ai = AzureHelper()
    
    if not azure_ai.connected:
        return "❌ Azure Blob Storage에 연결할 수 없습니다. 연결 설정을 확인하세요."
    
    # AI 분석 실행
    with st.spinner("🤖 Azure에서 데이터 분석 중..."):
        ai_response = azure_ai.analyze_plan_query(user_question)
    
    return ai_response