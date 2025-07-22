# utils/session.py (날짜 처리 오류 해결 버전)
import streamlit as st
import datetime
import uuid
import pickle
import json

class SessionManager:
    def __init__(self):
        pass
    
    def init_state(self):
        """세션 상태 초기화"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = self._generate_session_id()
        if 'last_file' not in st.session_state:
            st.session_state.last_file = None
        if 'last_dataframe' not in st.session_state:
            st.session_state.last_dataframe = None
        if 'biz_days' not in st.session_state:
            st.session_state.biz_days = {}
        if 'is_processing' not in st.session_state:
            st.session_state.is_processing = False
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = self._get_default_preferences()
        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []
    
    def _generate_session_id(self):
        """새로운 세션 ID 생성"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        return f"{timestamp}_{unique_id}"
    
    def _get_default_preferences(self):
        """기본 사용자 설정 반환"""
        return {
            "theme": "light",
            "auto_save": True,
            "show_tooltips": True,
            "chart_style": "plotly",
            "default_filters": {
                "min_amount": 10_000_000,
                "min_lines": 500,
                "change_threshold": 15
            }
        }
    
    def start_new_chat(self):
        """새 채팅 시작"""
        # 현재 채팅 저장
        if st.session_state.messages:
            self.save_current_chat()
        
        # 새 세션 초기화
        st.session_state.messages = []
        st.session_state.current_session_id = self._generate_session_id()
        st.session_state.last_file = None
        st.session_state.last_dataframe = None
        st.session_state.biz_days = {}
        st.session_state.is_processing = False
        
        # 분석 히스토리에 기록
        self._add_to_analysis_history("new_chat", "새 채팅 시작")
    
    def save_current_chat(self):
        """현재 채팅 저장"""
        if not st.session_state.messages:
            return
            
        session_data = {
            "messages": st.session_state.messages.copy(),
            "timestamp": datetime.datetime.now(),  # ✅ datetime 객체로 저장
            "file": st.session_state.last_file,
            "data": st.session_state.last_dataframe,
            "biz_days": st.session_state.biz_days.copy(),
            "session_summary": self._generate_session_summary()
        }
        
        st.session_state.chat_sessions[st.session_state.current_session_id] = session_data
        
        # 자동 저장이 활성화된 경우 로컬 저장
        if st.session_state.user_preferences.get("auto_save", True):
            self._save_to_local_storage(st.session_state.current_session_id, session_data)
    
    def update_session_data(self, filename, dataframe):
        """세션 데이터 업데이트"""
        # 현재 세션이 없으면 생성
        if st.session_state.current_session_id not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[st.session_state.current_session_id] = {
                "messages": [],
                "timestamp": datetime.datetime.now(),  # ✅ datetime 객체로 생성
                "file": None,
                "data": None,
                "biz_days": {},
                "session_summary": ""
            }

        # 세션 데이터 업데이트
        session = st.session_state.chat_sessions[st.session_state.current_session_id]
        session["messages"] = st.session_state.messages.copy()
        session["file"] = filename
        session["data"] = dataframe
        session["timestamp"] = datetime.datetime.now()  # ✅ datetime 객체로 업데이트
        
        # 분석 히스토리에 기록
        self._add_to_analysis_history("file_upload", f"파일 업로드: {filename}")
    
    def _generate_session_summary(self):
        """세션 요약 생성"""
        if not st.session_state.messages:
            return "빈 세션"
        
        user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
        if not user_messages:
            return "사용자 메시지 없음"
        
        # 첫 번째와 마지막 사용자 메시지 기반으로 요약
        first_msg = user_messages[0]["content"][:50]
        if len(user_messages) > 1:
            last_msg = user_messages[-1]["content"][:50]
            return f"{first_msg}... → {last_msg}..."
        else:
            return first_msg
    
    def _add_to_analysis_history(self, action_type, description):
        """분석 히스토리에 추가"""
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),  # ✅ datetime 객체로 저장
            "session_id": st.session_state.current_session_id,
            "action_type": action_type,
            "description": description,
            "file_name": st.session_state.last_file
        }
        
        st.session_state.analysis_history.append(history_entry)
        
        # 히스토리 크기 제한 (최대 100개)
        if len(st.session_state.analysis_history) > 100:
            st.session_state.analysis_history = st.session_state.analysis_history[-100:]
    
    def _save_to_local_storage(self, session_id, session_data):
        """로컬 스토리지에 저장 (시뮬레이션)"""
        try:
            # 실제 환경에서는 파일 시스템에 저장
            # 여기서는 세션 상태에만 저장
            if 'saved_sessions' not in st.session_state:
                st.session_state.saved_sessions = {}
            
            # 데이터프레임은 저장하지 않고 메타데이터만 저장
            save_data = {
                "messages": session_data["messages"],
                "timestamp": session_data["timestamp"],  # datetime 객체 그대로 저장
                "file": session_data["file"],
                "biz_days": session_data["biz_days"],
                "session_summary": session_data["session_summary"]
            }
            
            st.session_state.saved_sessions[session_id] = save_data
            
        except Exception as e:
            st.warning(f"세션 저장 중 오류 발생: {str(e)}")
    
    def load_session_from_storage(self, session_id):
        """저장된 세션 로드"""
        try:
            if 'saved_sessions' in st.session_state and session_id in st.session_state.saved_sessions:
                return st.session_state.saved_sessions[session_id]
        except Exception as e:
            st.error(f"세션 로드 중 오류 발생: {str(e)}")
        return None
    
    def delete_session(self, session_id):
        """세션 삭제"""
        try:
            # 메모리에서 삭제
            if session_id in st.session_state.chat_sessions:
                del st.session_state.chat_sessions[session_id]
            
            # 로컬 저장소에서 삭제
            if 'saved_sessions' in st.session_state and session_id in st.session_state.saved_sessions:
                del st.session_state.saved_sessions[session_id]
            
            # 분석 히스토리에 기록
            self._add_to_analysis_history("session_delete", f"세션 삭제: {session_id}")
            
            return True
        except Exception as e:
            st.error(f"세션 삭제 중 오류 발생: {str(e)}")
            return False
    
    def get_session_statistics(self):
        """세션 통계 반환"""
        stats = {
            "total_sessions": len(st.session_state.chat_sessions),
            "total_messages": sum(len(session.get("messages", [])) for session in st.session_state.chat_sessions.values()),
            "files_analyzed": len(set(session.get("file") for session in st.session_state.chat_sessions.values() if session.get("file"))),
            "analysis_actions": len(st.session_state.analysis_history)
        }
        return stats
    
    def export_session_data(self, session_id=None):
        """세션 데이터 내보내기 (날짜 직렬화 처리)"""
        try:
            if session_id:
                # 특정 세션만 내보내기
                if session_id in st.session_state.chat_sessions:
                    data = {session_id: st.session_state.chat_sessions[session_id]}
                else:
                    return None
            else:
                # 모든 세션 내보내기
                data = st.session_state.chat_sessions.copy()
            
            # 데이터프레임은 제외하고 내보내기 (용량 문제)
            export_data = {}
            for sid, session in data.items():
                timestamp = session.get("timestamp")
                # ✅ datetime 객체를 문자열로 변환
                timestamp_str = timestamp.isoformat() if isinstance(timestamp, datetime.datetime) else str(timestamp)
                
                export_data[sid] = {
                    "messages": session.get("messages", []),
                    "timestamp": timestamp_str,  # 문자열로 변환
                    "file": session.get("file"),
                    "biz_days": session.get("biz_days", {}),
                    "session_summary": session.get("session_summary", "")
                }
            
            return json.dumps(export_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            st.error(f"데이터 내보내기 중 오류 발생: {str(e)}")
            return None
    
    def import_session_data(self, json_data):
        """세션 데이터 가져오기 (날짜 파싱 처리)"""
        try:
            imported_data = json.loads(json_data)
            
            for session_id, session_data in imported_data.items():
                # ✅ 타임스탬프 복원 (문자열을 datetime으로)
                if session_data.get("timestamp"):
                    try:
                        session_data["timestamp"] = datetime.datetime.fromisoformat(session_data["timestamp"])
                    except ValueError:
                        # 문자열 파싱에 실패하면 현재 시간 사용
                        session_data["timestamp"] = datetime.datetime.now()
                else:
                    session_data["timestamp"] = datetime.datetime.now()
                
                # 데이터프레임은 None으로 설정 (별도로 업로드 필요)
                session_data["data"] = None
                
                st.session_state.chat_sessions[session_id] = session_data
            
            # 분석 히스토리에 기록
            self._add_to_analysis_history("session_import", f"{len(imported_data)}개 세션 가져오기")
            
            return True
            
        except Exception as e:
            st.error(f"데이터 가져오기 중 오류 발생: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, days_old=30):
        """오래된 세션 정리"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
            sessions_to_delete = []
            
            for session_id, session_data in st.session_state.chat_sessions.items():
                session_timestamp = session_data.get("timestamp")
                
                # ✅ timestamp가 문자열인지 datetime인지 확인
                if isinstance(session_timestamp, str):
                    try:
                        session_timestamp = datetime.datetime.fromisoformat(session_timestamp)
                    except ValueError:
                        continue  # 파싱 실패하면 건너뛰기
                
                if session_timestamp and session_timestamp < cutoff_date:
                    sessions_to_delete.append(session_id)
            
            # 오래된 세션 삭제
            for session_id in sessions_to_delete:
                self.delete_session(session_id)
            
            # 분석 히스토리에 기록
            if sessions_to_delete:
                self._add_to_analysis_history("cleanup", f"{len(sessions_to_delete)}개 오래된 세션 정리")
            
            return len(sessions_to_delete)
            
        except Exception as e:
            st.error(f"세션 정리 중 오류 발생: {str(e)}")
            return 0
    
    def update_user_preferences(self, preferences):
        """사용자 설정 업데이트"""
        try:
            st.session_state.user_preferences.update(preferences)
            # 분석 히스토리에 기록
            self._add_to_analysis_history("preferences_update", "사용자 설정 업데이트")
            return True
        except Exception as e:
            st.error(f"설정 업데이트 중 오류 발생: {str(e)}")
            return False
    
    def get_recent_files(self, limit=10):
        """최근 분석한 파일 목록 반환"""
        try:
            files = []
            for session in sorted(st.session_state.chat_sessions.values(), 
                                key=lambda x: self._safe_get_timestamp(x), 
                                reverse=True):
                file_name = session.get("file")
                if file_name and file_name not in [f["name"] for f in files]:
                    files.append({
                        "name": file_name,
                        "timestamp": self._safe_get_timestamp(session),
                        "session_id": next(sid for sid, s in st.session_state.chat_sessions.items() if s == session)
                    })
                
                if len(files) >= limit:
                    break
            
            return files
        except Exception as e:
            st.error(f"최근 파일 조회 중 오류 발생: {str(e)}")
            return []
    
    def _safe_get_timestamp(self, session):
        """세션에서 안전하게 timestamp 가져오기"""
        timestamp = session.get("timestamp", datetime.datetime.min)
        
        # ✅ 문자열이면 datetime으로 변환
        if isinstance(timestamp, str):
            try:
                return datetime.datetime.fromisoformat(timestamp)
            except ValueError:
                return datetime.datetime.min
        # datetime 객체면 그대로 반환
        elif isinstance(timestamp, datetime.datetime):
            return timestamp
        else:
            return datetime.datetime.min
    
    def get_analysis_insights(self):
        """분석 인사이트 반환"""
        try:
            insights = {
                "most_active_hour": self._get_most_active_hour(),
                "average_session_length": self._get_average_session_length(),
                "common_question_types": self._get_common_question_types(),
                "file_analysis_frequency": self._get_file_analysis_frequency()
            }
            return insights
        except Exception as e:
            st.error(f"인사이트 생성 중 오류 발생: {str(e)}")
            return {}
    
    def _get_most_active_hour(self):
        """가장 활동적인 시간대 반환"""
        hours = []
        for entry in st.session_state.analysis_history:
            timestamp = entry.get("timestamp")
            # ✅ timestamp 안전하게 처리
            if isinstance(timestamp, datetime.datetime):
                hours.append(timestamp.hour)
            elif isinstance(timestamp, str):
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    hours.append(dt.hour)
                except ValueError:
                    continue
        
        if hours:
            from collections import Counter
            most_common = Counter(hours).most_common(1)
            return most_common[0][0] if most_common else 0
        return 0
    
    def _get_average_session_length(self):
        """평균 세션 길이 반환 (메시지 수 기준)"""
        session_lengths = [len(session.get("messages", [])) for session in st.session_state.chat_sessions.values()]
        return sum(session_lengths) / len(session_lengths) if session_lengths else 0
    
    def _get_common_question_types(self):
        """일반적인 질문 유형 반환"""
        question_keywords = []
        for session in st.session_state.chat_sessions.values():
            for message in session.get("messages", []):
                if message.get("role") == "user":
                    content = message.get("content", "").lower()
                    if "요금제" in content:
                        question_keywords.append("요금제")
                    elif "트렌드" in content or "변화" in content:
                        question_keywords.append("트렌드")
                    elif "이상" in content:
                        question_keywords.append("이상탐지")
                    else:
                        question_keywords.append("일반")
        
        if question_keywords:
            from collections import Counter
            return dict(Counter(question_keywords).most_common(3))
        return {}
    
    def _get_file_analysis_frequency(self):
        """파일 분석 빈도 반환"""
        file_counts = {}
        for session in st.session_state.chat_sessions.values():
            file_name = session.get("file")
            if file_name:
                file_counts[file_name] = file_counts.get(file_name, 0) + 1
        return file_counts