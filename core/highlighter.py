"""
Highlighter for EnterMedSchool's Glossary.
Injects scripts and styles into cards to highlight glossary terms.
"""

from aqt import mw
from aqt.gui_hooks import reviewer_did_show_question, reviewer_did_show_answer
from ..utils.logging import log

def _inject_script(html: str) -> str:
    """Inject custom JS script into card HTML for universal double-click and term popups."""
    script = """
    <script id="ems-highlight-script">
    (function() {
        if (window.emsScriptInjected) return;
        window.emsScriptInjected = true;

        document.addEventListener('dblclick', function(e) {
            var sel = window.getSelection ? window.getSelection().toString().trim() : '';
            if (sel && sel.length >= 2) {
                var slug = sel.toLowerCase().replace(/[^a-z0-9\\s-]/g, '').trim().replace(/\\s+/g, '-');
                if (slug) {
                    if (typeof pycmd !== 'undefined') { pycmd('ems_term_click:' + slug); }
                    else if (window.pycmd) { window.pycmd('ems_term_click:' + slug); }
                    else if (typeof bridgeCommand !== 'undefined') { bridgeCommand('ems_term_click:' + slug); }
                }
            }
        });
    })();
    </script>
    """
    return html + script

def init_highlighter():
    log.info("Highlighter initialized with universal double-click lookup.")
