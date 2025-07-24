### 📘 Azure 기반 생성형 AI 프로젝트 제안서

#### ✅ 프로젝트: Azure 기반 청구 데이터 대화형 분석 및 리포트 자동화 시스템

---

#### 📌 개요 및 목적

요금제 및 청구 CSV 업로드하면, 
Azure 기반 GPT-4o-mini가 **이상 탐지, 시각화, 요약 리포트 생성, 자연어 질문 응답**까지 자동으로 수행하는  
**청구 데이터 Copilot 시스템**

- AI 기반 자동 탐지 : 한국 공휴일과 주말을 고려한 패턴 분석
- Azure 클라우드 연동 : 대용량 월별 데이터 실시간으로 처리
- AI 기반 채팅 분석 :  GPT-4o-mini을 이용한 실시간 챗봇을 통한 자연어 질의 응답 
- 데이터 시각화 : 청구금액과 이상 탐지를 그래프로 시각화

---

#### 📁 프로젝트 구조

```
AI_MVP/
├── .gitigore               
├── requirements.txt                 # 📦 의존성 패키지
└── MVP/
    ├── main.py                      # 🎯 메인 실행 파일
    ├── .env                         # 🔐 환경 변수
    ├── chat/
    │   └── manager.py               # 💬 채팅 관리 로직 
    ├── config/
    │   └── settings.py              # ⚙️ 설정 및 상수
    ├── data/
    │   └── processor.py             # 📊 데이터 처리 로직
    ├── ui/
    │   ├── styles.py                # 🎨 CSS 스타일
    │   ├── layout.py                # 📐 레이아웃 컴포넌트
    │   └── components.py            # 🧩 Azure 업로드 컴포넌트 추가
    │   └── enhanced_anomaly.py      # 🕐시계열 차트 컴포넌트 추가
    └── utils/
        ├── session.py               # 🔄 세션 유지
        └── azure_helper.py          # ☁️ Azure Blob 설정

```

---

#### 💻 기술 스택

| 영역             | 기술                                                         |
|------------------|--------------------------------------------------------------|
| **Frontend & UI**    | Streamlit 🎨 - 반응형 인터페이스, 실시간 상태 관리             |
| **Backend**          | Python 3.11, Pandas, NumPy, Scikit-learn 🐍              |
| **AI & NLP**         | OpenAI GPT-4o-mini 🤖 - 자연어 리포트, 질문 응답, 도메인 최적화     |
| **Visualization**    | Plotly 📊 - 인터랙티브 그래프, 모바일 대응             |
| **Storage & Cloud**  | Azure Blob Storage ☁️ - 대용량 저장, 자동 백업, 고가용성       |

---

#### 🔄 처리 프로세스

📂 사용자 CSV 업로드  
⬇️  
🐍 Streamlit + Pandas  
⬇️  
📊 CSV DataFrame 및 임계치 이상에 대한 이상 탐지  
⬇️  
🧠 Azure OpenAI GPT-4o-mini 사용하여 자동요약 리포트  
⬇️  
📈 Plotly 시각화 사용하여 청구 금액 및 회선수에 대한 최근 3개월간의 트렌드 시간화  
⬇️  
💬 사용자 자연어 질문 입력    
⬇️  
☁️ Azure Blob Storage에 저장된 여러 개월치 데이터 자동 인식 및 분석  

---

#### 🎯 기대 효과

- 📉 청구 데이터 이상 징후 조기 탐지 → 매출 손실 최소화
- ⏱ 수작업 리포트 작성 → AI 자동화 
- 💬 누구나 자연어로 질문 → 데이터 인사이트 즉시 확보

---

#### 🛠 기능 확장

- 고급 분석 기능 : 시계열 기반 미래 트렌드 예측
- AI 모델 고도화 : 도메인 특화 LLM 적용하여 AI 분석 결과의 근거 표시
- 자동 보고서 생성 : 일/주/월 자동 리포트

---
#### 🔗 데모 링크

[🌐 Azure Web App 바로가기](https://ktds16web001-e9gfddfybqd5h9b7.centralus-01.azurewebsites.net/)

