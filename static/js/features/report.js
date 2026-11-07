// features/report.js - Onglet « Diagnostic & accessibilité »

import { state } from '../state.js';
import { $, escapeHtml } from '../utils.js';
import * as api from '../api.js';
import { highlightUnreachableNodes } from '../map/highlights.js';

let unreachable = [];

const block = (title, body, notion, last = false) =>
    `<div class="report-block${last ? ' last' : ''}"><b class="text-blue">${title}</b><br>${body}` +
    `<div class="notion">Notion : ${notion}</div></div>`;

function renderReport(data, view) {
    const casernes = data.casernes_reference || [];
    const isoles = data.sites_isoles || [];
    const list = (ids) => escapeHtml(ids.join(', '));

    const unreachableHtml = unreachable.length > 0
        ? `<b class="danger">${list(unreachable)}</b><br>
           <button class="btn btn-sm btn-red mt-sm" data-action="show-unreachable">
               Afficher les ${unreachable.length} sites en rouge
           </button>`
        : '<i>Tous les sites sont couverts !</i>';

    const cycles = data.cycles_orientes
        ? '⚠️ <b class="danger">Cycles détectés</b>'
        : '✅ <b class="ok">Graphe Acyclique (DAG)</b>';

    return `
        <div class="card stack">
            <p class="text-xs muted"><b>Vue analysée :</b> ${escapeHtml(view.toUpperCase())}</p>
            ${block('1. Accessibilité des secours (BFS)', `
                <span class="text-sm">Casernes détectées : <b>${list(casernes) || 'Aucune'}</b></span><br>
                <span class="text-sm">Sites couverts : <b>${data.nb_sites_accessibles ?? 0}</b></span>`,
                'accessibilité depuis une source (BFS orienté depuis chaque caserne), pas la connexité forte.')}
            ${block('2. Connexité Fibre (DFS)', `
                <span class="text-sm">Composantes connexes : <b>${data.nb_composantes_fibre ?? 0}</b></span>`,
                'connexité ordinaire du graphe fibre non orienté (DFS).')}
            ${block('3. Itinéraire min. arcs (BFS)', `
                <span class="text-xs muted">Sélectionnez <b>BFS</b> dans l'onglet <b>Algorithmes</b>
                pour tracer l'itinéraire minimisant le nombre de sauts.</span>`,
                'plus court chemin en nombre d\'arcs (BFS), sans tenir compte des poids.')}
            ${block('4. Cycles orientés (DFS)', `<span class="text-sm">Statut : ${cycles}</span>`,
                'cycle orienté du graphe routier (DFS : un arc retour vers un sommet en cours de visite).')}
            ${block('5. Défaut de couverture & Isolation', `
                <span class="text-sm">Sites non atteignables : <b>${unreachable.length}</b></span><br>
                <div class="text-xs">${unreachableHtml}</div>
                <span class="text-sm block mt-sm">Sites isolés (degré 0) :
                    ${isoles.length > 0 ? `<b class="danger">${list(isoles)}</b>` : '<i>Aucun</i>'}</span>`,
                'non atteignable = inaccessible depuis toutes les casernes en suivant le sens des routes ; isolé = degré 0.', true)}
        </div>`;
}

export async function runReport() {
    const container = $('report-results');
    container.textContent = 'Calcul des indicateurs en cours...';

    try {
        const data = await api.fetchReport(state.view);
        unreachable = data.sites_non_atteignables || [];
        highlightUnreachableNodes(unreachable);
        container.innerHTML = renderReport(data, state.view);
    } catch (error) {
        console.error(error);
        container.innerHTML = `<span class="error-text">Erreur : ${escapeHtml(error.message)}</span>`;
    }
}

export const showUnreachable = () => highlightUnreachableNodes(unreachable);
