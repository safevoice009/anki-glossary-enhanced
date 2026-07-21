/**
 * EnterMedSchool's Glossary - Popup JavaScript
 * Playful Chunky Design - Full UX features
 */

(function() {
    'use strict';

    const HISTORY_STORAGE_KEY = 'ems_nav_history';
    const MAX_HISTORY = 10;

    function loadHistoryFromStorage() {
        try {
            const stored = sessionStorage.getItem(HISTORY_STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    }

    function saveHistoryToStorage() {
        try {
            sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(state.history));
        } catch (e) {
        }
    }

    const state = {
        history: loadHistoryFromStorage(),
        currentTerm: null,
        fontSize: 100,
        isFavorite: false,
        sections: [],
        activeSection: 0,
    };

    function pycmd(msg) {
        if (window.pycmd) {
            window.pycmd(msg);
        } else if (window.bridgeCommand) {
            window.bridgeCommand(msg);
        } else {
            console.log('[EMS] pycmd:', msg);
        }
    }

    function pushHistory(termId) {
        if (state.currentTerm && state.currentTerm !== termId) {
            state.history.push(state.currentTerm);
            if (state.history.length > MAX_HISTORY) {
                state.history.shift();
            }
            saveHistoryToStorage();
        }
        state.currentTerm = termId;
        updateBackButton();
    }

    function goBack() {
        if (state.history.length > 0) {
            const prevTerm = state.history.pop();
            state.currentTerm = null;
            saveHistoryToStorage();
            pycmd(`ems_navigate_term:${prevTerm}`);
        }
    }

    function updateBackButton() {
        const backBtn = document.getElementById('backBtn');
        const badge = document.getElementById('historyBadge');
        
        if (backBtn) {
            backBtn.hidden = state.history.length === 0;
        }
        
        if (badge) {
            if (state.history.length > 0) {
                badge.textContent = state.history.length;
                badge.classList.add('visible');
            } else {
                badge.classList.remove('visible');
            }
        }
    }

    function showToast(message, type = 'info') {
        let toast = document.querySelector('.ems-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'ems-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.className = `ems-toast ems-toast-${type} visible`;
        
        setTimeout(() => {
            toast.classList.remove('visible');
        }, 2000);
    }

    window.playTermAudio = function(termName) {
        if (!termName) {
            const titleEl = document.querySelector('.ems-term-title');
            termName = titleEl ? titleEl.textContent : '';
        }
        if (!termName) return;

        const cleanTerm = termName.replace(/[^a-zA-Z0-9\s-]/g, '').trim();
        showToast('🔊 Pronouncing: ' + cleanTerm);

        const audioUrl = 'https://dict.youdao.com/dictvoice?audio=' + encodeURIComponent(cleanTerm) + '&type=2';
        const audio = new Audio(audioUrl);
        
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.catch(function(error) {
                console.log('[EMS] Audio fetch error, using Web Speech API fallback:', error);
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(cleanTerm);
                    utterance.lang = 'en-US';
                    utterance.rate = 0.92;
                    window.speechSynthesis.speak(utterance);
                }
            });
        }
    };

    function init() {
        const termId = document.body.dataset.termId;
        if (termId) {
            pushHistory(termId);
        }
        console.log('[EMS Popup] Initialized successfully with Audio Pronunciation');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
