"""
Popup Window for EnterMedSchool's Glossary.
Qt WebEngineView-based popup for displaying term details.
Enhanced with Wikipedia Medical REST API fallback and Movable Window.
"""

import os
from typing import Optional, List
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QWebEngineView, QUrl, Qt,
    QPoint, QSize, pyqtSlot
)
from aqt.webview import AnkiWebView

from .content_builder import build_popup_html
from ...core.index_loader import get_term_content, get_index
from ...core.analytics import record_term_view, is_favorite, get_preference
from ...core.card_creator import create_card_from_section

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
        super().__init__(parent)
        self.setWindowTitle("EnterMedSchool's Glossary")
        # Movable window that stays on top of Anki review screen
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.current_term_id: Optional[str] = None
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
        """Show the popup for a specific term."""
        log.info(f"Showing popup for term: {term_id}")
        self.current_term_id = term_id
        self._search_query = search_query
        
        term_data = get_term_content(term_id)
        if not term_data:
            log.info(f"Term content missing locally, fetching online fallback for: {term_id}")
            term_data = self._fetch_online_fallback(term_id)
        
        record_term_view(term_id)
        dark_mode = self._is_dark_mode()
        html = build_popup_html(term_data, dark_mode)
        
        self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
        self._apply_user_preferences(term_id)
        
        if position:
            self._position_near(position)
        
        self.show()
        self.raise_()

    def _fetch_online_fallback(self, term_id: str) -> dict:
        """Fetch live rich medical definition and section details online from Wikipedia Medical API."""
        term_title = term_id.replace('_', ' ').replace('-', ' ').title()
        extract = ""
        full_text = ""
        best_title = term_title

        try:
            import urllib.request
            import urllib.parse
            import json

            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(term_title)}&format=json"
            req_search = urllib.request.Request(search_url, headers={'User-Agent': 'AnkiEnterMedSchoolGlossary/2.0'})
            with urllib.request.urlopen(req_search, timeout=3) as resp:
                s_data = json.loads(resp.read().decode('utf-8'))
                results = s_data.get('query', {}).get('search', [])
                if results:
                    best_title = results[0]['title']

            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
            req_sum = urllib.request.Request(summary_url, headers={'User-Agent': 'AnkiEnterMedSchoolGlossary/2.0'})
            with urllib.request.urlopen(req_sum, timeout=3) as resp:
                sum_data = json.loads(resp.read().decode('utf-8'))
                if 'extract' in sum_data and sum_data['extract']:
                    extract = sum_data['extract']

            full_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote(best_title)}&format=json"
            req_full = urllib.request.Request(full_url, headers={'User-Agent': 'AnkiEnterMedSchoolGlossary/2.0'})
            with urllib.request.urlopen(req_full, timeout=3) as resp:
                f_data = json.loads(resp.read().decode('utf-8'))
                pages = f_data.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    full_text = pdata.get('extract', '')
        except Exception as e:
            log.warning(f"Online fetch error for {term_id}: {e}")

        sentences = [s.strip() for s in (extract or full_text).split('. ') if s.strip()]

        def_text = (sentences[0] + '.') if sentences else f"Medical term and clinical concept '{best_title}'."
        why_text = ('. '.join(sentences[1:4]) + '.') if len(sentences) > 1 else f"Key clinical mechanism, physiological role, and medical relevance of {best_title}."

        see_list = []
        if '==' in full_text:
            sections = full_text.split('==')
            for idx in range(1, len(sections), 2):
                sec_heading = sections[idx].strip()
                sec_lower = sec_heading.lower()
                sec_content = sections[idx+1].strip() if idx+1 < len(sections) else ""
                if sec_content and any(k in sec_lower for k in ['use', 'clinical', 'indication', 'symptom', 'sign', 'diagnosis', 'treatment', 'mechanism', 'side effect', 'adverse', 'pharmacology', 'safety', 'precaution', 'toxicity']):
                    clean_para = sec_content.split('\n\n')[0].strip()
                    if clean_para and len(clean_para) > 20:
                        see_list.append(f"**{sec_heading}**: {clean_para[:450]}")
                        if len(see_list) >= 3:
                            break

        if not see_list:
            if len(sentences) > 4:
                see_list = ['. '.join(sentences[4:7]) + '.']
            else:
                see_list = [f"Commonly evaluated in clinical practice, diagnostic workup, and medical board examinations for {best_title}."]

        tricks_list = []
        title_lower = best_title.lower()

        for line in full_text.split('\n'):
            line_s = line.strip()
            if any(k in line_s.lower() for k in ['mnemonic', 'acronym', 'triad', 'pentad', 'classic feature', 'hallmark', 'pearl']):
                if len(line_s) > 15 and len(line_s) < 300:
                    tricks_list.append(f"💡 **Memory Aid**: {line_s}")
                    if len(tricks_list) >= 2:
                        break

        if 'folat' in title_lower or 'folic' in title_lower:
            tricks_list.append("💡 **Exam Trap**: Folic acid supplementation treats anemia but **MASKS Vitamin B12 deficiency**! It does NOT prevent neurological damage (Subacute Combined Degeneration of spinal cord). Always verify B12 levels before giving folate!")
        elif 'calcium' in title_lower:
            tricks_list.append("💡 **Exam Trap**: **Milk-Alkali Syndrome**! Triad of hypercalcemia, metabolic alkalosis, and renal insufficiency caused by high ingestion of calcium carbonate antacids.")
        elif 'iron' in title_lower or 'ferrous' in title_lower:
            tricks_list.append("💡 **Exam Trap**: Acute Iron Toxicity presents with hematemesis, abdominal pain, anion gap metabolic acidosis, and radiopaque tablets on X-ray. **Deferoxamine** is the antidote!")
        elif 'aspirin' in title_lower:
            tricks_list.append("💡 **Mnemonic/Trap**: Aspirin overdose causes **Mixed Respiratory Alkalosis & Metabolic Acidosis**. Do NOT give to children with viral illness (Reye syndrome!).")
        elif 'statin' in title_lower or 'atorvastatin' in title_lower:
            tricks_list.append("💡 **Exam Trap**: Statins inhibit HMG-CoA reductase. Adverse effect: **Myopathy / Rhabdomyolysis** (especially when combined with Fibrates or Niacin). Monitor LFTs and CK!")
        elif 'ace' in title_lower or 'lisinopril' in title_lower or 'enalapril' in title_lower:
            tricks_list.append("💡 **Mnemonic**: CAPTOPRIL (Cough, Angioedema, Proteinuria, Taste changes, Orthostatic hypotension, Pregnancy contraindication, Rash, Increased K+, Leukopenia).")
        elif 'metformin' in title_lower:
            tricks_list.append("💡 **Exam Trap**: Major risk is **Lactic Acidosis**. Withhold metformin prior to IV contrast administration and in severe renal impairment (eGFR < 30).")

        if not tricks_list:
            if len(sentences) >= 3:
                tricks_list = [f"💡 **High-Yield Pearl**: {sentences[1]}", f"💡 **Clinical Key**: {sentences[2]}"]
            else:
                tricks_list = [f"💡 **High-Yield Pearl**: Key board-relevant concept for {best_title} evaluated in medical exams."]

        return {
            "id": term_id,
            "names": [best_title],
            "aliases": [],
            "abbr": [],
            "patterns": [term_title.lower()],
            "primary_tag": "general",
            "tags": ["general", "online_wiki"],
            "level": "medschool",
            "definition": def_text,
            "why_it_matters": why_text,
            "how_youll_see_it": see_list,
            "tricks": tricks_list
        }

    def _get_web_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

    def _is_dark_mode(self) -> bool:
        try:
            config = mw.addonManager.getConfig(__name__.split('.')[0]) or {}
            dark_mode_setting = config.get('dark_mode', 'auto')
            if dark_mode_setting == 'dark': return True
            elif dark_mode_setting == 'light': return False
            else: return mw.pm.night_mode()
        except Exception:
            return False

    def _apply_user_preferences(self, term_id: str):
        is_fav = is_favorite(term_id)
        self.web_view.page().runJavaScript(f'window.setFavoriteState && window.setFavoriteState({str(is_fav).lower()})')
        font_size = get_preference("popup_font_size", "100")
        try:
            size = int(font_size)
            self.web_view.page().runJavaScript(f'window.setFontSize && window.setFontSize({size})')
        except ValueError:
            pass

    def _position_near(self, position: QPoint):
        screen = mw.screen()
        if screen:
            screen_rect = screen.availableGeometry()
            popup_size = self.size()
            x = position.x()
            y = position.y() + 20
            if x + popup_size.width() > screen_rect.right():
                x = screen_rect.right() - popup_size.width() - 10
            if y + popup_size.height() > screen_rect.bottom():
                y = position.y() - popup_size.height() - 20
            if y < screen_rect.top():
                y = screen_rect.top()
            self.move(x, y)

    @pyqtSlot(str)
    def _on_bridge_command(self, cmd: str):
        if cmd.startswith("ems_close_popup"):
            self.hide()
        elif cmd.startswith("ems_create_card:"):
            parts = cmd.split(":")
            if len(parts) >= 3:
                term_id = parts[1]
                section = parts[2]
                try:
                    success, message = create_card_from_section(term_id, section)
                except Exception as e:
                    log.error(f"Error creating card: {e}", exc_info=True)
                    success = False
                    message = "Error creating card"
                import json
                safe_message = json.dumps(message)
                safe_section = json.dumps(section)
                js = f'window.handleCardCreationResult && window.handleCardCreationResult({str(success).lower()}, {safe_message}, {safe_section})'
                self.web_view.page().runJavaScript(js)
        elif cmd.startswith("ems_open_term:"):
            term_id = cmd.split(":")[1]
            self.show_term(term_id)
        elif cmd.startswith("ems_navigate_term:"):
            term_id = cmd.split(":")[1]
            self._navigate_to_term(term_id)

    def _navigate_to_term(self, term_id: str):
        log.info(f"Navigating to term: {term_id}")
        term_data = get_term_content(term_id)
        if not term_data:
            term_data = self._fetch_online_fallback(term_id)
        record_term_view(term_id)
        self.current_term_id = term_id
        dark_mode = self._is_dark_mode()
        html = build_popup_html(term_data, dark_mode)
        self.web_view.setHtml(html, QUrl.fromLocalFile(self._get_web_path()))
        self._apply_user_preferences(term_id)
