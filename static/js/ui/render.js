// ui/render.js - Petits constructeurs de HTML (toutes les valeurs dynamiques sont échappées)

import { escapeHtml as esc } from '../utils.js';

export { esc };

export const num = (value, digits = 2) =>
    value == null ? '—' : Number(value).toLocaleString('fr-FR', { maximumFractionDigits: digits });

export const withUnit = (value, unit, digits = 2) => (value == null ? '—' : `${num(value, digits)} ${unit}`);

export const idList = (ids, max = 12) => {
    const shown = ids.slice(0, max).map(esc).join(', ');
    return ids.length > max ? `${shown}… (+${ids.length - max})` : shown;
};

export const arrows = (path) => path.map(esc).join(' → ');

export const badge = (ok, yes, no) =>
    `<span class="badge ${ok ? 'badge-ok' : 'badge-ko'}">${ok ? yes : no}</span>`;

export const errorHtml = (error) => `<span class="error-text">Erreur : ${esc(error.message)}</span>`;

/** headers : texte ; rows : tableaux de cellules déjà en HTML sûr. */
export function table(headers, rows) {
    const head = headers.map((h) => `<th>${h}</th>`).join('');
    const body = rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('');
    return `<div class="table-wrap"><table class="grid"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

export const fold = (summary, body) => `<details class="fold"><summary>${summary}</summary>${body}</details>`;

export const yesNo = (value) => (value ? '<b class="ok">oui</b>' : '<b class="danger">non</b>');
