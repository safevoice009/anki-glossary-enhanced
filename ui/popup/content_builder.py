"""
Content Builder for EnterMedSchool's Glossary.
Builds popup HTML from term data.
"""

import os
import base64
from typing import Dict, List, Optional

from ...core.index_loader import get_index
from ...core.analytics import was_card_created
from ...utils.markdown import render_markdown, render_inline
from ...utils.config import is_beta_enabled


def get_addon_path() -> str:
    """Get the absolute path to the addon directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_logo_data_uri() -> str:
    """
    Get the logo as a data URI for reliable inline loading.
    Falls back to empty string if logo not found.
    """
    logo_path = os.path.join(get_addon_path(), "assets", "leo-logo.png")
    try:
        with open(logo_path, "rb") as f:
            logo_bytes = f.read()
            logo_b64 = base64.b64encode(logo_bytes).decode("utf-8")
            return f"data:image/png;base64,{logo_b64}"
    except (FileNotFoundError, IOError):
        return ""


def get_web_path() -> str:
    """Get the absolute path to the web resources directory."""
    return os.path.join(get_addon_path(), "ui", "web")


def load_css() -> str:
    """Load the popup CSS content."""
    try:
        css_path = os.path.join(get_web_path(), "popup.css")
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_fonts_css() -> str:
    """Load fonts CSS if available."""
    try:
        fonts_path = os.path.join(get_web_path(), "fonts.css")
        with open(fonts_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


SECTIONS = [
    ("definition", "📚", "Definition"),
    ("why_it_matters", "💡", "Why It Matters"),
    ("how_youll_see_it", "👁️", "How You'll See It"),
    ("tricks", "🧠", "Tricks & Mnemonics"),
]

COLLAPSED_BY_DEFAULT = []


def build_popup_html(term_data: dict, dark_mode: bool = False) -> str:
    """Build HTML for the popup window from term data."""
    level = term_data.get("level", "medschool")
    return build_medschool_popup_html(term_data, dark_mode)


def build_tags_html(tags: list, index) -> str:
    """Build HTML for tag pills."""
    if not tags:
        return ""
    
    html = ""
    for tag_id in tags:
        tag_info = index.get_tag_info(tag_id)
        name = tag_info.get("name", tag_id)
        color = tag_info.get("color", "#6C5CE7")
        icon = tag_info.get("icon", "")
        
        icon_html = f'<span class="ems-tag-pill-icon">{icon}</span>' if icon else ""
        html += f'''
        <span class="ems-tag-pill" style="--tag-color: {color};" title="{name}">
            {icon_html}{name}
        </span>
        '''
    return html


def build_section_html(key: str, icon: str, title: str, content, term_id: str, collapsed: bool = False) -> str:
    """Build HTML for a single section."""
    if not content:
        return ""
    
    content_html = ""
    if isinstance(content, list):
        items_html = ""
        for item in content:
            rendered_item = render_markdown(str(item))
            items_html += f'<li class="ems-section-list-item">{rendered_item}</li>'
        content_html = f'<ul class="ems-section-list">{items_html}</ul>'
    else:
        content_html = render_markdown(str(content))
    
    collapsed_class = " collapsed" if collapsed else ""
    collapsed_attr = ' data-collapsed="true"' if collapsed else ""
    
    card_btn_html = f'''
    <button class="ems-section-card-btn" onclick="createCard('{term_id}', '{key}')" title="Create flashcard from this section">
        <span class="ems-card-btn-icon">🎴</span>
        <span class="ems-card-btn-text">Make Card</span>
    </button>
    '''
    
    return f'''
    <section class="ems-section ems-section-{key}{collapsed_class}" data-section-key="{key}"{collapsed_attr}>
        <div class="ems-section-header" onclick="toggleSection('{key}')">
            <div class="ems-section-title-wrap">
                <span class="ems-section-icon">{icon}</span>
                <h2 class="ems-section-title">{title}</h2>
            </div>
            <div class="ems-section-actions">
                {card_btn_html}
                <span class="ems-accordion-toggle">▼</span>
            </div>
        </div>
        <div class="ems-section-body">
            <div class="ems-section-content">
                {content_html}
            </div>
        </div>
    </section>
    '''


def build_sources_html(sources: list) -> str:
    """Build HTML for sources section."""
    if not sources:
        return ""
    
    items = ""
    for s in sources:
        if isinstance(s, dict):
            name = s.get("name", "Source")
            url = s.get("url", "#")
            items += f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>'
        else:
            items += f'<li>{s}</li>'
            
    return f'''
    <section class="ems-section ems-section-sources collapsed" data-section-key="sources">
        <div class="ems-section-header" onclick="toggleSection('sources')">
            <div class="ems-section-title-wrap">
                <span class="ems-section-icon">🔗</span>
                <h2 class="ems-section-title">Sources</h2>
            </div>
            <span class="ems-accordion-toggle">▼</span>
        </div>
        <div class="ems-section-body">
            <ul class="ems-sources-list">{items}</ul>
        </div>
    </section>
    '''


def build_credits_html(credits: list) -> str:
    """Build HTML for credits section."""
    if not credits:
        return ""
    
    items = "".join([f'<li>{c}</li>' for c in credits])
    return f'''
    <section class="ems-section ems-section-credits collapsed" data-section-key="credits">
        <div class="ems-section-header" onclick="toggleSection('credits')">
            <div class="ems-section-title-wrap">
                <span class="ems-section-icon">🙏</span>
                <h2 class="ems-section-title">Credits</h2>
            </div>
            <span class="ems-accordion-toggle">▼</span>
        </div>
        <div class="ems-section-body">
            <ul class="ems-credits-list">{items}</ul>
        </div>
    </section>
    '''


def build_part_of_html(see_also: list, index) -> str:
    """Build HTML for part_of parent term banner."""
    if not see_also:
        return ""
    
    for term_id in see_also:
        term = index.get_term(term_id)
        if term:
            name = term.get("names", [term_id])[0]
            return f'''
            <div class="ems-part-of-banner" onclick="navigateToTerm('{term_id}')">
                <span class="ems-part-of-label">Part of</span>
                <span class="ems-part-of-name">{name}</span>
                <span class="ems-part-of-arrow">→</span>
            </div>
            '''
    return ""


def build_footer_html(see_also: list, prerequisites: list, index) -> str:
    """Build footer with related terms links."""
    links_html = ""
    
    all_related = []
    if see_also:
        all_related.extend([(tid, "related") for tid in see_also])
    if prerequisites:
        all_related.extend([(tid, "prereq") for tid in prerequisites])
        
    if not all_related:
        return ""
        
    for term_id, rel_type in all_related:
        term = index.get_term(term_id)
        if term:
            name = term.get("names", [term_id])[0]
            icon = "📋" if rel_type == "prereq" else "🔍"
            title = f"Prerequisite: {name}" if rel_type == "prereq" else name
            links_html += f'''
            <button class="ems-related-chip" onclick="navigateToTerm('{term_id}')" title="{title}">
                <span class="ems-chip-icon">{icon}</span>
                <span class="ems-chip-label">{name}</span>
            </button>
            '''
            
    if not links_html:
        return ""
        
    return f'''
    <footer class="ems-popup-footer">
        <div class="ems-related-title">Related Concepts</div>
        <div class="ems-related-chips">
            {links_html}
        </div>
    </footer>
    '''


def build_medschool_popup_html(term_data: dict, dark_mode: bool = False) -> str:
    """Build popup HTML for medical school level terms (full features)."""
    term_id = term_data.get("id", "")
    names = term_data.get("names", [term_id])
    primary_tag = term_data.get("primary_tag", "")
    tags = term_data.get("tags", [])
    
    index = get_index()
    tag_info = index.get_tag_info(primary_tag)
    icon = tag_info.get("icon", "📚")
    
    # Build tag pills
    tags_html = build_tags_html(tags, index)
    
    # Build sections
    sections_html = ""
    for section_key, section_icon, section_title in SECTIONS:
        content = term_data.get(section_key)
        if content:
            collapsed = section_key in COLLAPSED_BY_DEFAULT
            sections_html += build_section_html(
                section_key, section_icon, section_title, 
                content, term_id, collapsed
            )
    
    # Build see also
    see_also = term_data.get("see_also", [])
    prerequisites = term_data.get("prerequisites", [])
    footer_html = build_footer_html(see_also, prerequisites, index)
    
    # Build "Part of" banner for nested term navigation
    part_of_html = build_part_of_html(see_also, index)
    
    # Build sources/credits
    sources = term_data.get("sources", [])
    credits = term_data.get("credits", [])
    if sources:
        sections_html += build_sources_html(sources)
    if credits:
        sections_html += build_credits_html(credits)
    
    theme = "dark" if dark_mode else "light"
    
    # Get logo as data URI for reliable loading
    logo_src = get_logo_data_uri()
    logo_html = f'<img class="ems-logo" src="{logo_src}" width="32" height="32" alt="">' if logo_src else '<span class="ems-logo-fallback">📚</span>'
    
    # Inline CSS for reliable loading in Anki's WebView
    fonts_css = load_fonts_css()
    popup_css = load_css()
    
    return f'''
    <!DOCTYPE html>
    <html lang="en" dir="ltr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
{fonts_css}
        </style>
        <style>
{popup_css}
        </style>
    </head>
    <body class="ems-popup-body" data-theme="{theme}" data-term-id="{term_id}">
        <!-- Header stays fixed at top, outside scroll area -->
        <header class="ems-popup-header">
            <div class="ems-header-left">
                {logo_html}
                <span class="ems-tag-icon">{icon}</span>
                <h1 class="ems-term-title">{names[0]}</h1>
            </div>
            <button class="ems-close-btn" onclick="pycmd('ems_close_popup')" aria-label="Close">×</button>
        </header>
        
        <!-- Compact toolbar -->
        <div class="ems-toolbar">
            <div class="ems-toolbar-left">
                <button class="ems-tool-btn" id="backBtn" onclick="goBack()" title="Go back (Backspace)" hidden>
                    <span>←</span>
                    <span class="ems-history-badge" id="historyBadge"></span>
                </button>
                <button class="ems-tool-btn" id="favoriteBtn" onclick="toggleFavorite()" title="Add to favorites (F)">
                    <span id="favIcon">☆</span>
                </button>
            </div>
            <div class="ems-toolbar-center">
                <button class="ems-tool-btn" onclick="decreaseFont()" title="Decrease font (-)">
                    <span>A-</span>
                </button>
                <button class="ems-tool-btn" onclick="increaseFont()" title="Increase font (+)">
                    <span>A+</span>
                </button>
                <button class="ems-tool-btn ems-audio-btn" onclick="window.playTermAudio('{names[0]}')" title="Play Audio Pronunciation (🔊)">
                    <span>🔊 Audio</span>
                </button>
                <button class="ems-tool-btn" onclick="copyDefinition()" title="Copy definition (Ctrl+C)">
                    <span>📋</span>
                </button>
            </div>
            <div class="ems-toolbar-right">
                <button class="ems-tool-btn ems-menu-btn" onclick="toggleMenu(event)" title="Menu">
                    <span>≡</span>
                </button>
                <div class="ems-dropdown-menu" id="dropdownMenu" style="display:none;">
                    <button onclick="expandAll()">Expand All (E)</button>
                    <button onclick="collapseAll()">Collapse All (C)</button>
                    <hr>
                    <button onclick="showHistory()">History</button>
                </div>
            </div>
        </div>
        
        <!-- Tags bar also outside scroll area -->
        <div class="ems-tags-bar">
            {tags_html}
        </div>
        
        <!-- Breadcrumb navigation trail (shown when history exists) -->
        <div class="ems-breadcrumb-bar" id="breadcrumbBar"></div>
        
        <!-- Section quick-jump dots -->
        <nav class="ems-section-dots" id="sectionDots"></nav>
        
        <!-- Only this container scrolls -->
        <div class="ems-popup-container" id="scrollContainer">
            <!-- Part of banner for nested terms (scrolls with content) -->
            {part_of_html}
            
            <main class="ems-popup-content" id="popupContent">
                {sections_html}
            </main>
            
            {footer_html}
        </div>
    </body>
    </html>
    '''
