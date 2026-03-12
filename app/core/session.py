"""Session management"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import json
from pathlib import Path


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    current_url: Optional[str] = None
    current_platform: Optional[str] = None
    analyzed_pages: List[Dict] = []
    test_cases: List[Dict] = []
    exported_files: List[str] = []
    messages: List[Dict] = []
    metadata: Dict[str, Any] = {}


class SessionManager:
    
    def __init__(self, storage_dir: str = "./data/sessions", timeout: int = 3600):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self._sessions: Dict[str, SessionState] = {}
    
    def create(self) -> SessionState:
        session = SessionState()
        self._sessions[session.session_id] = session
        self._save_session(session)
        return session
    
    def get(self, session_id: str) -> Optional[SessionState]:
        if session_id in self._sessions:
            return self._sessions[session_id]
        session = self._load_session(session_id)
        if session:
            self._sessions[session_id] = session
        return session
    
    def get_or_create(self, session_id: Optional[str] = None) -> SessionState:
        if session_id:
            session = self.get(session_id)
            if session:
                return session
        return self.create()
    
    def update(self, session: SessionState) -> None:
        session.updated_at = datetime.now()
        self._sessions[session.session_id] = session
        self._save_session(session)
    
    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
        session_file = self.storage_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        session = self.get(session_id)
        if session:
            session.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self.update(session)
    
    def set_analysis(self, session_id: str, url: str, platform: str, pages: List[Dict]) -> None:
        session = self.get(session_id)
        if session:
            session.current_url = url
            session.current_platform = platform
            session.analyzed_pages = pages
            self.update(session)
    
    def set_test_cases(self, session_id: str, test_cases: List[Dict]) -> None:
        session = self.get(session_id)
        if session:
            session.test_cases = test_cases
            self.update(session)
    
    def add_exported_file(self, session_id: str, file_path: str) -> None:
        session = self.get(session_id)
        if session:
            session.exported_files.append(file_path)
            self.update(session)
    
    def get_context_summary(self, session_id: str) -> Dict:
        session = self.get(session_id)
        if not session:
            return {}
        return {
            "url": session.current_url,
            "platform": session.current_platform,
            "pages_count": len(session.analyzed_pages),
            "test_cases_count": len(session.test_cases),
            "exported_files": len(session.exported_files),
            "messages_count": len(session.messages)
        }
    
    def _save_session(self, session: SessionState) -> None:
        session_file = self.storage_dir / f"{session.session_id}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def _load_session(self, session_id: str) -> Optional[SessionState]:
        session_file = self.storage_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SessionState(**data)
