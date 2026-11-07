// features/negativeCycles.js - Onglet « Circuits absorbants »

import { state } from '../state.js';
import { $ } from '../utils.js';

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

export async function runNegativeCycleCheck() {
    const container = $('negative-cycles-results');

    if (state.startNode === null || state.startNode === undefined) {
        alert('Veuillez sélectionner un sommet de départ 🚗 sur la carte.');
        return;
    }
    if (container) container.textContent = "Analyse des circuits absorbants en cours...";

    try {
        const res = await fetch(
            `/api/analysis/detect-absorbent-cycles?start=${encodeURIComponent(state.startNode)}&view=${encodeURIComponent(state.view)}`
        );
        if (!res.ok) throw new Error("Erreur lors de l'analyse des circuits absorbants");

        const json = await res.json();
        const data = json.result || json;

        if (container) {
            container.innerHTML = `
                <div class="card stack text-sm">
                    <b class="text-blue">Module 3 : Circuits Absorbants</b>
                    <p>Sommet source analysé : <b>${escapeHtml(state.startNode)}</b></p>
                    <p>Circuit absorbant détecté : <b class="${data.has_negative_cycle ? 'danger' : 'ok'}">${data.has_negative_cycle ? 'OUI (Incohérence)' : 'NON (Stable)'}</b></p>
                    ${data.has_negative_cycle ? `<p>Accessible depuis la source : <b>${data.accessible_from_source ? 'OUI' : 'NON'}</b></p>` : ''}
                    <p><b>Méthode :</b> ${escapeHtml(data.method_used)}</p>
                    <div class="alert ${data.has_negative_cycle ? 'alert-ko' : 'alert-ok'} mt-sm">
                        ${escapeHtml(data.message)}
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error(error);
        if (container) container.innerHTML = `<span class="error-text">Erreur : ${escapeHtml(error.message)}</span>`;
    }
}