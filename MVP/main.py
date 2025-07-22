# main.py (에러 처리 추가 버전)
import streamlit as st

# 안전한 import (에러 시 명확한 메시지)
try:
    from config.settings import setup_page_config
    from ui.styles import load_custom_styles
    from ui.layout import render_header, render_sidebar, render_footer
    from data.processor import DataProcessor
    from chat.manager import ChatManager
    from utils.session import SessionManager
except ImportError as e:
    st.error(f"❌ 모듈 import 오류: {e}")
    st.error("📁 폴더 구조와 __init__.py 파일들을 확인해주세요!")
    st.info("""
    필요한 파일들:
    - config/__init__.py (빈 파일)
    - ui/__init__.py (빈 파일) 
    - data/__init__.py (빈 파일)
    - chat/__init__.py (빈 파일)
    - utils/__init__.py (빈 파일)
    """)
    st.stop()

def main():
    try:
        # 페이지 설정
        setup_page_config()
        
        # 커스텀 스타일 로드
        load_custom_styles()
        
        # 세션 매니저 초기화
        session_mgr = SessionManager()
        session_mgr.init_state()
        
        # 데이터 프로세서 초기화
        data_processor = DataProcessor()
        
        # 채팅 매니저 초기화
        chat_mgr = ChatManager()
        
        # UI 렌더링
        render_header()
        render_sidebar(session_mgr, chat_mgr)
        
        # 메인 콘텐츠
        render_main_content(data_processor, chat_mgr, session_mgr)
        
        # 푸터
        render_footer()
        
    except Exception as e:
        st.error(f"❌ 애플리케이션 실행 중 오류: {e}")
        st.error("🔧 .env 파일의 OpenAI API 설정을 확인해주세요!")

def render_main_content(data_processor, chat_mgr, session_mgr):
    """메인 콘텐츠 렌더링"""
    try:
        from ui.components import (
            render_welcome_message, 
            render_upload_section, 
            render_data_analysis,
            render_chat_interface
        )
        
        # 데이터가 없을 때 환영 메시지
        if st.session_state.get('last_dataframe') is None:
            render_welcome_message()
        
        # 업로드 섹션
        df = render_upload_section(data_processor, session_mgr)
        
        # 데이터 분석 섹션
        if df is not None:
            render_data_analysis(df, data_processor, chat_mgr, session_mgr)
        
        # 채팅 인터페이스
        render_chat_interface(chat_mgr, session_mgr)
        
    except Exception as e:
        st.error(f"❌ UI 렌더링 중 오류: {e}")
        st.error("📄 각 파일들이 올바른 위치에 있는지 확인해주세요!")

if __name__ == "__main__":
    main()