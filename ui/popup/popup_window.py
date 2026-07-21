"""
Popup Window for EnterMedSchool's Glossary.
Qt WebEngineView-based popup for displaying term details.
"""

import os
from typing import Optional, List
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QWebEngineView, QUrl, Qt,
    QPoint, QSize, pyqtSlot
)
from aqt.webview import AnkiWebView

from .content_builder import build_popup_html, build_loading_html
from ...core.index_loader import get_term_content, get_index
from ...core.analytics import record_term_view, is_favorite, get_preference
from ...core.card_creator import create_card_from_section

# Import logger with fallback to print
try:
    from ...utils import logger as log
except ImportError:
    class _FallbackLog:
        def debug(self, msg): print(f"[EMS DEBUG] {msg}")
        def info(self, msg): print(f"[EMS INFO] {msg}")
        def warning(self, msg): print(f"[EMS WARNING] {msg}")
        def error(self, msg, exc_info=False): print(f"[EMS ERROR] {msg}")
    log = _FallbackLog()


class GlossaryPopup(QDialog):
    """
    Main popup window for displaying glossary terms.
    Uses WebEngineView for rich HTML rendering.
    """
    
    _instance: Optional['GlossaryPopup'] = None
    
    @classmethod
    def instance(cls) -> 'GlossaryPopup':
        """Get or create the singleton popup instance."""
        if cls._instance is None:
            cls._instance = cls(mw)
        return cls._instance
    
    def __init__(self, parent=None):
        super().__init__(parent if parent else mw)
        self.setWindowTitle("EnterMedSchool's Glossary")
        # Parented Tool window: Minimizes automatically WITH Anki!
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.current_term_id: Optional[str] = None
        self._is_bubble: bool = False
        self._saved_size: Optional[QSize] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the popup UI."""
        self.setMinimumSize(350, 300)
        
        # Load saved size or use defaults
        saved_width = get_preference("popup_width", "500")
        saved_height = get_preference("popup_height", "550")
        try:
            self.resize(int(saved_width), int(saved_height))
        except ValueError:
            self.resize(500, 550)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view
        self.web_view = AnkiWebView(self)
        self.web_view.set_bridge_command(self._on_bridge_command, self)
        layout.addWidget(self.web_view)
    
    def show_term(self, term_id: str, position: Optional[QPoint] = None, search_query: Optional[str] = None):
        """
        Show the popup for a specific term.
        Background thread online fetch so Anki NEVER freezes!
        """
        log.info(f"Showing popup for term: {term_id}")
        self.current_term_id = term_id
        self._search_query = search_query
        
        # Auto-expand if currently minimized to bubble
        if self._is_bubble:
            self.setMinimumSize(350, 300)
            self._is_bubble = False
            if self._saved_size:
                self.resize(self._saved_size)

        # Position popup near cursor and bring to top
        from aqt.qt import QCursor
        cursor_pos = QCursor.pos()
        self._position_near(position if position else cursor_pos)
        
        self.show()
        self.raise_()
        self.activateWindow()

        term_data = get_term_content(term_id)
        dark_mode = self._is_dark_mode()

        if term_data:
            # Local term exists: display immediately
            html = build_popup_html(term_data, dark_mode)
            self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
            record_term_view(term_id)
            self._apply_user_preferences(term_id)
        else:
            # Term missing locally: show loading screen IMMEDIATELY on main thread (0ms delay)
            loading_html = build_loading_html(term_id, dark_mode)
            self.web_view.setHtml(loading_html, QUrl.fromLocalFile(self._get_web_path()))
            
            # Perform online fetch in background thread to prevent UI freezing
            try:
                from aqt.operations import QueryOp
                
                def fetch_op(col):
                    return self._fetch_online_fallback(term_id)
                
                def on_success(fetched_data):
                    if fetched_data and self.current_term_id == term_id:
                        html = build_popup_html(fetched_data, dark_mode)
                        self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
                        record_term_view(term_id)
                        self._apply_user_preferences(term_id)
                
                op = QueryOp(
                    parent=self,
                    op=fetch_op,
                    success=on_success
                )
                op.with_progress(False).run_in_background()
            except Exception as e:
                log.warning(f"Background fetch fallback error: {e}")
                # Fallback to direct call if QueryOp is unavailable
                fetched_data = self._fetch_online_fallback(term_id)
                html = build_popup_html(fetched_data, dark_mode)
                self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
                record_term_view(term_id)
                self._apply_user_preferences(term_id)

    def minimize_to_bubble(self):
        """Collapse Glossary popup into a compact Messenger Bubble (60x60)."""
        from .content_builder import build_bubble_html
        self._is_bubble = True
        self._saved_size = self.size()
        self.resize(70, 70)
        self.setMinimumSize(60, 60)
        bubble_html = build_bubble_html(self._is_dark_mode())
        self.web_view.setHtml(bubble_html, QUrl.fromLocalFile(self._get_web_path()))

    def expand_from_bubble(self):
        """Expand Messenger Bubble back to full Glossary window."""
        self._is_bubble = False
        self.setMinimumSize(350, 300)
        if self._saved_size:
            self.resize(self._saved_size)
        else:
            self.resize(500, 550)
            
        if self.current_term_id:
            term_data = get_term_content(self.current_term_id)
            if not term_data:
                term_data = self._fetch_online_fallback(self.current_term_id)
            html = build_popup_html(term_data, self._is_dark_mode())
            self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
