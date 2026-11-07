// features/intervention.js - Onglet « Calcul d'intervention » (caserne -> site, avec perturbations)

import { state } from '../state.js';
import { $, escapeHtml } from '../utils.js';
import * as api from '../api.js';
import { highlightPath } from '../map/highlights.js';

const badge = (accessible) => accessible
    ? '<span class="badge badge-ok">ACCESSIBLE</span>'
    : '<span class="badge badge-ko">INACCESSIBLE</span>';

const costCell = (r) => (r.accessible ? `${r.cost} min/km (${r.nb_arcs} arcs)` : 'Inaccessible');

function renderResult(data) {
    const { avant_perturbation: avant, apres_perturbation: apres, degradation: deg } = data;
    const showDelay = apres.accessible && avant.accessible;

    return `
        <div class="card stack">
            <div class="card-header">
                <b class="text-blue">Fiche d'intervention</b>
                ${badge(apres.accessible)}
            </div>

            <div class="text-sm">
                <p><b>Trajet :</b> Caserne ${escapeHtml(state.startNode)} -> Site ${escapeHtml(state.targetNode)}</p>
                <p><b>Arcs fermés appliqués :</b> ${data.arcs_fermes_appliques.length}</p>
            </div>

            <hr class="divider">

            <div class="text-sm">
                <b class="muted">Bilan du retard :</b>
                <table class="kv">
                    <tr><td>Coût initial :</td><td>${costCell(avant)}</td></tr>
                    <tr><td>Coût sous perturbation :</td><td>${costCell(apres)}</td></tr>
                    ${showDelay ? `
                        <tr class="danger"><td>Retard absolu :</td><td>+${deg.retard_absolu} min/km</td></tr>
                        <tr class="danger"><td>Retard relatif :</td><td>+${deg.retard_relatif_pct}%</td></tr>` : ''}
                </table>
            </div>

            ${apres.accessible ? `
                <div class="path-box">
                    <b>Chemin retenu :</b><br>
                    <span class="text-blue">${apres.path.map(escapeHtml).join(' -> ')}</span>
                </div>` : ''}
        </div>`;
}

export async function runIntervention() {
    const container = $('intervention-results');

    if (state.startNode === null || state.targetNode === null) {
        alert('Veuillez sélectionner une caserne (départ) et un site (arrivée) sur la carte.');
        container.innerHTML = '<span class="error-text">Veuillez choisir un départ et une arrivée.</span>';
        return;
    }
    container.textContent = "Calcul du trajet d'intervention en cours...";

    const formData = new FormData();
    formData.append('start', state.startNode);
    formData.append('target', state.targetNode);
    formData.append('view', state.view);

    const file = $('inter-scenario-file').files[0];
    const manualArcs = $('inter-manual-arcs').value;
    if (file) formData.append('scenario_file', file);
    if (manualArcs) formData.append('manual_arcs', manualArcs);

    try {
        const data = await api.computeIntervention(formData);
        if (!data.apres_perturbation) {
            container.innerHTML = `<span class="error-text">${escapeHtml(data.message || 'Aucun résultat.')}</span>`;
            return;
        }
        if (data.apres_perturbation.accessible) highlightPath(data.apres_perturbation.path);
        container.innerHTML = renderResult(data);
    } catch (error) {
        console.error(error);
        container.innerHTML = `<span class="error-text">Erreur : ${escapeHtml(error.message)}</span>`;
    }
}
