# config/settings.py
import streamlit as st

def setup_page_config():
    """페이지 설정"""
    st.set_page_config(
        page_title="청구 Copilot", 
        layout="wide",
        page_icon="💼",
        initial_sidebar_state="expanded"
    )

# 환경 변수 및 상수 설정
MODEL_NAME = "gpt-4o"
MIN_AMOUNT_DEFAULT = 10_000_000
MIN_LINES_DEFAULT = 500
CHANGE_THRESHOLD_DEFAULT = 15

# API 설정
API_VERSION = "2024-05-01-preview"