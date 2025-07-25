# ui/styles.py
import streamlit as st

def load_custom_styles():
    """커스텀 CSS 스타일 로드"""
    st.markdown("""
    <style>
        /* 메인 헤더 스타일 */
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        /* 메트릭 카드 스타일 */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
        }
        
        /* 버튼 스타일 개선 */
        .stButton > button {
            width: 100%;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            font-weight: 600;
            color: #333;
            background:
                linear-gradient(white, white) padding-box,  /* 내부 배경 */
                linear-gradient(135deg, #667eea, #764ba2) border-box;  /* 테두리용 그라디언트 */
            border: 1px solid transparent;  /* 투명 테두리로 공간 확보 */
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* 경고/성공 박스 스타일 */
        .warning-box {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #ff6b6b;
            margin: 0 0 1rem 0;
        }
        
        .success-box {
            background: linear-gradient(135deg, #a8e6cf 0%, #dcedc1 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #4ecdc4;
            margin: 0rem 0 1rem 0;
        }
        
        /* 사이드바 개선 */
        .css-1d391kg {
            background-color: #f8f9ff;
        }
        
        /* 로딩 애니메이션 개선 */
        .stSpinner > div {
            border-color: #667eea transparent #667eea transparent;
        }
        
        /* 채팅 메시지 개선 */
        .chat-message {
            background: #f8f9ff;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 3px solid #667eea;
        }
        
        /* 데이터프레임 스타일 */
        .dataframe {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* 업로드 섹션 스타일 */
        .upload-section {
            background: #f8f9ff;
            padding: 1.5rem;
            border-radius: 10px;
            border: 2px dashed #667eea;
            margin: 1rem 0;
        }
        
        /* 프로그레스 바 스타일 */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
                
        /* 커스텀 버튼 스타일 */
        .custom-btn {
            background: linear-gradient(135deg, #78FFCD, #3C465C);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            border: none;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }

        .custom-btn:hover {
            background: linear-gradient(135deg, #54d8a3, #2e3544);
            transform: scale(1.03);
        }
        div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 16rem; /* 기본 sidebar 너비 고려 */
        right: 0;
        background-color: white;
        padding: 1rem;
        box-shadow: 0 -1px 4px rgba(0,0,0,0.1);
        z-index: 9999;
        }
                
    </style>
    """, unsafe_allow_html=True)