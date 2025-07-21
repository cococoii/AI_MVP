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

# 사이드바: 새 채팅 및 이전 대화
with st.sidebar:
    st.header("💬 채팅 메뉴")
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
        st.subheader("📁 이전 대화 기록")
        for sid, session in sorted(st.session_state.chat_sessions.items(), key=lambda x: x[1]['timestamp'], reverse=True):
            label = session['timestamp'].strftime("%m/%d %H:%M")
            if st.button(f"📂 {label}", key=sid):
                st.session_state.messages = session['messages']
                st.session_state.current_session_id = sid
                st.session_state.last_file = session.get('file')
                st.session_state.last_dataframe = session.get('data')
                st.rerun()

# 안내 메시지 출력
if st.session_state.last_dataframe is None:
    with st.chat_message("assistant"):
        st.markdown("📂 CSV 파일을 업로드하면 분석을 시작할 수 있어요!")

# CSV 업로드 및 설정
with st.expander("📂 CSV 업로드 및 필터 설정", expanded=st.session_state.last_dataframe is None):
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

if st.session_state.last_dataframe is not None:
    df = st.session_state.last_dataframe.copy()

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

    if st.button("📋 요약 요청하기"):
        with st.chat_message("user"):
            st.markdown("요약을 요청합니다.")
        with st.spinner("GPT 요약 생성 중..."):
            summary_prompt = f"""
            다음은 청구 데이터 일부와 월별 영업일 수입니다:

            ▶ 영업일 수 변화: {st.session_state.biz_days}
            ▶ 샘플 데이터:
            {df.head(20).to_csv(index=False)}

            다음 기준으로 요약해줘:
            1. 청구 항목별 이상 패턴 요약
            2. 영업일 변화와 청구금액/회선수 변화의 상관관계
            3. ARPU나 청구금액의 이상 탐지 기준이 타당한지에 대한 의견
            간단한 문장과 표 형태로 정리해줘.
            """
            summary_reply = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 통계 기반 Copilot이야."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            reply_text = summary_reply.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply_text})

        with st.chat_message("assistant"):
            st.markdown(reply_text)

    user_question = st.chat_input("질문을 입력하세요")
    if user_question:
        st.session_state.messages.append({"role": "user", "content": user_question})

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.spinner("GPT 응답 생성 중..."):
            prompt = f"""
            사용자의 질문: {user_question}
            기준월별 영업일 수 변화: {st.session_state.biz_days}

            아래는 관련 청구 요금제 데이터입니다:
            {df.head(20).to_csv(index=False)}

            질문에 대한 통계적 분석과 시각적 인사이트를 제시해줘. 해당 요금제에 대한 회선수와 청구금액 추이도 분석해줘.
            """
            gpt_reply = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 데이터 분석 Copilot이야."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = gpt_reply.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})

        with st.chat_message("assistant"):
            st.markdown(reply)

        if "요금제" in user_question:
            keyword = user_question.split("요금제")[-1].strip().split()[0]
            if keyword:
                target_df = df[df[df.columns[0]].astype(str).str.contains(keyword, na=False)]
                if not target_df.empty:
                    fig1 = px.line(target_df, x="기준월", y="m1월회선수", title=f"{keyword} - M1 월 회선수 추이")
                    fig2 = px.line(target_df, x="기준월", y="m1청구금액", title=f"{keyword} - M1 청구금액 추이")
                    st.plotly_chart(fig1)
                    st.plotly_chart(fig2)

    if st.session_state.messages:
        st.subheader("💬 Copilot 대화 기록")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

