"""
EnterMedSchool's Glossary - Enhanced Edition
Anki addon for highlighting medical terms and showing detailed popups.
Enhanced with live Wikipedia Medical API fallback, universal double-click lookup, high-yield exam traps engine, and movable window.
"""

from .ui.popup import GlossaryPopup
from .core.highlighter import init_highlighter

# Initialize the addon components
init_highlighter()
