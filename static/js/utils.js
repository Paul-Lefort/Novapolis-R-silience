// utils.js - Petits helpers sans dépendance

export const $ = (id) => document.getElementById(id);

/** "12" -> 12, "A3" -> "A3", 12 -> 12 (les ids peuvent être numériques ou textuels). */
export function parseId(value) {
    if (typeof value === 'number') return value;
    const s = String(value).trim();
    return s !== '' && Number.isFinite(Number(s)) ? Number(s) : s;
}

/** Échappe une valeur avant insertion dans du HTML. */
export function escapeHtml(value) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value ?? '').replace(/[&<>"']/g, (c) => map[c]);
}
