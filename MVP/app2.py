# streamlit_app.py
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from pandas.tseries.offsets import BDay
import plotly.express as px
import datetime
import uuid

# Load environment variables
load_dotenv()

# Azure OpenAI setup
client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("OPENAI_API_BASE")
)
MODEL_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# Streamlit config
st.set_page_config(page_title="청구 Copilot", layout="wide")
st.title("💼 청구 Copilot - 이상 감지 + 요약 분석")

# 세션 상태 초기화
def init_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    if 'last_file' not in st.session_state:
        st.session_state.last_file = None
    if 'last_dataframe' not in st.session_state:
        st.session_state.last_dataframe = None
    if 'biz_days' not in st.session_state:
        st.session_state.biz_days = {}
init_state()

# 채팅 내역 영역만 사이드바에 유지
with st.sidebar:
    st.header("💬 저장된 채팅 내역")
    if st.button("🆕 새 채팅 시작"):
        if st.session_state.messages:
            st.session_state.chat_sessions[st.session_state.current_session_id] = {
                "messages": st.session_state.messages.copy(),
                "timestamp": datetime.datetime.now(),
                "file": st.session_state.last_file,
                "data": st.session_state.last_dataframe
            }
        st.session_state.messages = []
        st.session_state.current_session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        st.session_state.last_file = None
        st.session_state.last_dataframe = None
        st.session_state.biz_days = {}
        st.rerun()

    if st.session_state.chat_sessions:
        st.caption("저장된 대화 불러오기:")
        for sid, session in sorted(st.session_state.chat_sessions.items(), key=lambda x: x[1]['timestamp'], reverse=True):
            label = session['timestamp'].strftime("%m/%d %H:%M")
            if st.button(f"📂 {label}", key=sid):
                st.session_state.messages = session['messages']
                st.session_state.current_session_id = sid
                st.session_state.last_file = session.get('file')
                st.session_state.last_dataframe = session.get('data')
                st.rerun()

# 상단 설정 영역
with st.container():
    with st.expander("📂 CSV 업로드 및 필터 설정", expanded=True):
        uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")
        col1, col2, col3 = st.columns(3)
        with col1:
            min_amount = st.number_input("요청 금액 임계값", value=10_000_000)
        with col2:
            min_lines = st.number_input("월 회선수 임계값", value=500)
        with col3:
            change_threshold = st.slider("변화율 임계값 (%)", 0, 100, 15)

# 파일 핸들링 및 분석 시작
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")
    st.session_state.last_file = uploaded_file.name
    st.session_state.last_dataframe = df.copy()

    if '기준월' not in df.columns:
        df['기준월'] = '2024-06-01'

    st.subheader("📄 데이터 미리보기")
    st.dataframe(df.head())

    df['기준월'] = pd.to_datetime(df['기준월'], errors='coerce')
    months = df['기준월'].dropna().dt.to_period("M").unique()
    for m in months:
        start, end = pd.Timestamp(m.start_time), pd.Timestamp(m.end_time)
        biz_days = pd.date_range(start, end, freq=BDay())
        st.session_state.biz_days[m.strftime("%Y-%m")] = len(biz_days)
        st.markdown(f"📅 {m} 영업일 수: {len(biz_days)}일")

    df_filtered = df.copy()
    for col in ["m1요청금액", "m2요청금액", "m1월회선수", "m2월회선수", "m1청구금액", "m2청구금액"]:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_filtered["arpu"] = df_filtered["m1청구금액"] / df_filtered["m1월회선수"]

    df_flagged = df_filtered[
        ((df_filtered["m1월회선수"] + df_filtered["m2월회선수"]) > 0) &
        ((df_filtered["m1요청금액"] >= min_amount) | (df_filtered["m2요청금액"] >= min_amount)) &
        (df_filtered["m1월회선수"] > min_lines) &
        (df_filtered["arpu"] >= 0.1) &
        (((df_filtered["m1청구금액"] - df_filtered["m2청구금액"]) / df_filtered["m2청구금액"]).abs() >= change_threshold / 100) &
        (((df_filtered["m1월회선수"] - df_filtered["m2월회선수"]) / df_filtered["m2월회선수"]).abs() >= change_threshold / 100)
    ]

    st.subheader("🚨 이상 탐지 결과")
    st.dataframe(df_flagged)

    csv_sample = df.to_csv(index=False)

    # 영업일 요약 텍스트 생성
    biz_day_summary = "\n".join([
        f"- {month}: {days}일" for month, days in st.session_state.biz_days.items()
    ])

    auto_prompt = f"""
    다음은 전체 청구 요금제별 데이터입니다:

    {csv_sample}

    아래는 각 월의 영업일 수입니다:
    {biz_day_summary}

    다음 기준으로 요약해줘:
    - 어떤 항목들이 주요한지 (이상 포함)
    - 공통된 패턴은?
    - 영업일 변화가 청구금액/회선수에 미친 영향이 있다면 설명
    - 필터 기준은 무엇이 타당해보이는지
    """

    with st.spinner("GPT 요약 생성 중..."):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 청구 데이터를 분석하는 Copilot이야."},
                {"role": "user", "content": auto_prompt}
            ]
        )
        gpt_summary = response.choices[0].message.content

    st.session_state.messages.append({"role": "user", "content": auto_prompt})
    st.session_state.messages.append({"role": "assistant", "content": gpt_summary})

    st.subheader("💬 Copilot 대화 기록")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_question = st.chat_input("질문을 입력하세요")
    if user_question:
        followup_prompt = f"""
        다음은 전체 청구 요금제별 데이터입니다:

        {csv_sample}

        사용자 질문: {user_question}

        아래는 각 월의 영업일 수입니다:
        {biz_day_summary}

        위 데이터를 바탕으로 통계적으로 분석하고 설명해줘.
        필요하다면 특정 요금제에 대한 회선수 및 청구금액 추이도 보여줘.
        """
        st.session_state.messages.append({"role": "user", "content": user_question})

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.spinner("GPT 응답 생성 중..."):
            followup = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 청구 데이터를 분석하는 Copilot이야."},
                    {"role": "user", "content": followup_prompt}
                ]
            )
            assistant_msg = followup.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            with st.chat_message("assistant"):
                st.markdown(assistant_msg)

            # 특정 요금제에 대한 그래프 출력
            if "요금제" in user_question:
                keyword = user_question.split("요금제")[-1].strip().split()[0]
                target_df = df[df[df.columns[0]].str.contains(keyword, na=False)]
                if not target_df.empty:
                    fig1 = px.line(target_df, x="기준월", y="m1월회선수", title=f"{keyword} - M1 월 회선수 추이")
                    fig2 = px.line(target_df, x="기준월", y="m1청구금액", title=f"{keyword} - M1 청구금액 추이")
                    st.plotly_chart(fig1)
                    st.plotly_chart(fig2)