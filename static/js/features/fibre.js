// features/fibre.js - Onglet « Conception réseau fibre » : ACM (Kruskal / Prim) et simulation de panne

import { $, escapeHtml } from '../utils.js';
import * as api from '../api.js';
import { highlightSegments } from '../map/highlights.js';
import { switchView } from '../ui/sidebar.js';
import { state } from '../state.js';

const results = () => $('fibre-acm-results');
const showError = (error) => {
    console.error(error);
    results().innerHTML = `<span class="error-text">Erreur : ${escapeHtml(error.message)}</span>`;
};

export async function runAcm() {
    const algo = $('acm-algo-select').value;
    if (state.view !== 'fibre') switchView('fibre');
    results().textContent = `Calcul de l'arbre couvrant minimal (${algo.toUpperCase()})...`;

    try {
        const data = await api.fetchAcm(algo);

        // Chaque arête de l'ACM est un segment indépendant (et non un chemin continu)
        highlightSegments(data.edges_acm.map((e) => [e.u, e.v]));

        const connectivity = data.est_connexe
            ? '<div class="alert alert-ok">Réseau totalement connexe : Arbre couvrant minimal complet.</div>'
            : `<div class="alert alert-ko">Réseau non connexe (${data.nb_composantes} composantes). Forêt couvrante calculée.</div>`;

        results().innerHTML = `
            <div class="card">
                <b class="text-green">Conception Réseau Fibre (${escapeHtml(data.algo.toUpperCase())})</b>
                <p class="text-sm">Coût total minimal : <b>${data.cost_total} k€</b></p>
                <p class="text-sm">Tronçons retenus : <b>${data.nb_edges_acm}</b></p>
                ${connectivity}
            </div>`;
    } catch (error) {
        showError(error);
    }
}

export async function runCompare() {
    results().textContent = 'Comparaison de Kruskal et Prim...';

    try {
        const { kruskal, prim, coherence_cout_total: same } = await api.compareAcm();
        results().innerHTML = `
            <div class="card text-sm">
                <b class="text-blue">Comparaison Kruskal vs Prim :</b><br>
                - Coût Kruskal : <b>${kruskal.cost_total} k€</b> (${kruskal.nb_edges_acm} tronçons)<br>
                - Coût Prim : <b>${prim.cost_total} k€</b> (${prim.nb_edges_acm} tronçons)<br>
                <div class="status-line ${same ? 'ok' : 'danger'}">
                    Statut : ${same ? 'Coûts totaux strictement identiques' : 'Divergence de coûts détectée'}
                </div>
            </div>`;
    } catch (error) {
        showError(error);
    }
}

export async function runBreakdown() {
    const u = $('panne-u').value.trim();
    const v = $('panne-v').value.trim();

    if (!u || !v) {
        alert('Veuillez saisir les deux sommets (U et V) du tronçon en panne.');
        return;
    }
    results().textContent = 'Calcul du raccordement de secours...';

    try {
        const data = await api.simulateBreakdown(u, v);
        const [eu, ev] = [escapeHtml(u), escapeHtml(v)];

        if (!data.impact_acm) {
            results().innerHTML = `
                <div class="card card-soft text-sm">
                    Le tronçon (${eu}, ${ev}) ne fait pas partie de l'Arbre Couvrant Minimal initial.
                    Aucun impact sur le réseau principal.
                </div>`;
        } else if (data.raccordement_possible) {
            const s = data.troncon_secours;
            results().innerHTML = `
                <div class="card text-sm">
                    <b class="danger">Panne sur le tronçon (${eu}, ${ev})</b><br>
                    - Tronçon de secours identifié : <b>${escapeHtml(s.u)} <-> ${escapeHtml(s.v)}</b><br>
                    - Coût de la réparation : <b>${s.cost} k€</b><br>
                    - Surcoût induit : <b>+${data.surcout} k€</b><br>
                    - Nouveau coût total du réseau : <b>${data.nouveau_cout_total} k€</b>
                </div>`;
        } else {
            results().innerHTML = `
                <div class="alert alert-ko">
                    Panne critique : Aucun tronçon alternatif disponible pour reconnecter le réseau.
                </div>`;
        }
    } catch (error) {
        showError(error);
    }
}
