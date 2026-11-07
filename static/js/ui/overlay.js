// ui/overlay.js - Écran de chargement et fenêtre modale

import { $ } from '../utils.js';

let hideTimer = null;

export function setLoadingMessage(msg, isError = false) {
    const el = $('loading-msg');
    if (!el) return;
    el.textContent = msg;
    el.classList.toggle('error', isError);
}

export function showOverlay(msg) {
    clearTimeout(hideTimer);
    const overlay = $('loading-overlay');
    overlay.classList.remove('hidden', 'fading');
    if (msg) setLoadingMessage(msg);
}

export function hideOverlay({ fade = false } = {}) {
    const overlay = $('loading-overlay');
    if (!fade) {
        overlay.classList.add('hidden');
        return;
    }
    overlay.classList.add('fading');
    hideTimer = setTimeout(() => overlay.classList.replace('fading', 'hidden'), 300);
}

export const openModal = () => $('generate-modal').classList.add('open');
export const closeModal = () => $('generate-modal').classList.remove('open');
