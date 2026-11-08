// features/intervention.js - Onglet « Itinéraires de secours » (module 2)

import { state } from '../state.js';
import { $ } from '../utils.js';
import * as api from '../api.js';
import { highlightPath } from '../map/highlights.js';
import { arrows, badge, errorHtml, esc, num, table, withUnit, yesNo } from '../ui/render.js';

const ALGOS = {
    dijkstra: 'Dijkstra (référence)',
    bellman_ford: 'Bellman-Ford',
    floyd_warshall: 'Floyd-Warshall',
    bfs_min_arcs: 'BFS (min. arcs)',
};
const CRITERES = { temps_normal: 'durée normale', temps_pointe: 'durée en pointe', distance: 'distance' };
const STATUTS = {
    inchange: 'Trajet inchangé',
    degrade: 'Trajet dégradé',
    devenu_inaccessible: 'Devenu inaccessible',
    inaccessible_des_le_depart: 'Inaccessible dès le départ',
};

const row = (label, value) => `<tr><td>${label}</td><td>${value}</td></tr>`;
const list = (items) => (items.length ? items.join('<br>') : '<i>aucune</i>');

export function renderResult(d) {
    const { avant_perturbation: av, apres_perturbation: ap, degradation: deg, unite: u } = d;
    const cost = (r) => (r.accessible ? withUnit(r.cost, u) : '<b class="danger">Inaccessible</b>');
    const arcs = (r) => (r.accessible ? r.nb_arcs : '—');
    const both = av.accessible && ap.accessible;

    const fermetures = d.fermetures.map((f) => `${esc(f.u)} → ${esc(f.v)} <span class="muted">(${esc(f.origine)})</span>`);
    const coupant = d.fermetures_sur_trajet_initial.map((f) => `${esc(f.u)} → ${esc(f.v)}`);
    const rencontrees = ap.fermetures_rencontrees.map((f) => `${esc(f.u)} → ${esc(f.v)} <span class="muted">(${esc(f.statut)})</span>`);
    const samePath = av.accessible && ap.accessible && av.path.join() === ap.path.join();

    return `
        <div class="card stack">
            <div class="card-header">
                <b class="text-blue">Fiche d'intervention</b>
                ${badge(ap.accessible, 'ACCESSIBLE', 'INACCESSIBLE')}
            </div>
            <div class="text-sm">Caserne <b>${esc(d.start)}</b> → site <b>${esc(d.target)}</b><br>
                <span class="muted">${esc(ALGOS[d.algo])} · critère : ${esc(CRITERES[d.critere])}</span></div>

            <table class="kv">
                ${row('Coût avant perturbation', cost(av))}
                ${row('Coût après perturbation', cost(ap))}
                ${row('Nombre d\'arcs (avant / après)', `${arcs(av)} / ${arcs(ap)}`)}
                ${both ? `<tr class="${deg.retard_absolu > 0 ? 'danger' : ''}"><td>Retard absolu</td><td>${deg.retard_absolu > 0 ? '+' : ''}${withUnit(deg.retard_absolu, u)}</td></tr>
                          <tr class="${deg.retard_absolu > 0 ? 'danger' : ''}"><td>Retard relatif</td><td>${deg.retard_relatif_pct > 0 ? '+' : ''}${num(deg.retard_relatif_pct)} %</td></tr>` : ''}
                ${row('Statut', esc(STATUTS[deg.statut] ?? '—'))}
            </table>

            ${ap.accessible ? `<div class="path-box"><b>Chemin retenu :</b><br><span class="text-blue">${arrows(ap.path)}</span></div>` : ''}
            ${av.accessible && !samePath ? `<div class="path-box"><b>Chemin avant perturbation :</b><br>${arrows(av.path)}</div>` : ''}

            <div class="text-xs">
                <b>Fermetures appliquées (${fermetures.length})</b><br>${list(fermetures)}
                ${coupant.length ? `<br><b class="danger">Fermetures sur le trajet initial :</b><br>${list(coupant)}` : ''}
                ${d.arcs_introuvables.length ? `<br><span class="muted">Arcs absents du graphe : ${d.arcs_introuvables.map(([a, b]) => `${esc(a)}→${esc(b)}`).join(', ')}</span>` : ''}
                ${rencontrees.length ? `<br><b>Arcs dégradés sur le chemin retenu :</b><br>${list(rencontrees)}` : ''}
            </div>
            ${ap.remarque ? `<div class="alert alert-ko">${esc(ap.remarque)}</div>` : ''}
            <div class="notion">Un chemin de coût minimal ne garantit pas une intervention réaliste : voir « Limites » dans le menu Résilience.</div>
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
    formData.append('view', 'routier');
    formData.append('algo', $('inter-algo').value);
    formData.append('critere', $('inter-critere').value);

    const file = $('inter-scenario-file').files[0];
    const manualArcs = $('inter-manual-arcs').value;
    if (file) formData.append('scenario_file', file);
    if (manualArcs) formData.append('manual_arcs', manualArcs);

    try {
        const data = await api.computeIntervention(formData);
        if (!data.apres_perturbation) {
            container.innerHTML = `<span class="error-text">${esc(data.message || 'Aucun résultat.')}</span>`;
            return;
        }
        if (data.apres_perturbation.accessible) highlightPath(data.apres_perturbation.path);
        container.innerHTML = renderResult(data);
    } catch (error) {
        console.error(error);
        container.innerHTML = errorHtml(error);
    }
}

// ---------- Comparaison des algorithmes sur la même instance ----------

export function renderComparison(d) {
    const u = d.unite;
    const cell = (r) => ({
        ok: withUnit(r.cost, u),
        inaccessible: 'Inaccessible',
        moins_infini: '<b class="danger">−∞</b>',
        ignore: '<span class="muted">Ignoré</span>',
    }[r.statut]);

    const rows = d.resultats.map((r) => [
        esc(ALGOS[r.algo] ?? r.algo), cell(r), r.accessible ? r.nb_arcs : '—', r.temps_ms == null ? '—' : num(r.temps_ms, 2),
    ]);
    const remarques = d.resultats.filter((r) => r.remarque).map((r) => `<div class="text-xs muted">${esc(ALGOS[r.algo])} : ${esc(r.remarque)}</div>`).join('');

    return `
        <div class="card stack">
            <b class="text-blue">Comparaison sur la même instance</b>
            <div class="text-xs muted">${esc(d.start)} → ${esc(d.target)} · ${d.nb_sommets} sommets, ${d.nb_arcs} arcs · ${esc(CRITERES[d.critere])}</div>
            ${table(['Algorithme', `Coût (${u})`, 'Arcs', 'ms'], rows)}
            <div class="text-sm">Mêmes coûts : ${yesNo(d.couts_identiques || !d.resultats.some((r) => r.accessible))}
                · Mêmes chemins : ${yesNo(d.chemins_identiques)}</div>
            <div class="notion">Plusieurs plus courts chemins de même coût peuvent exister : seuls les coûts doivent coïncider. Le BFS minimise les arcs, donc son coût peut être supérieur.</div>
            ${remarques}
        </div>`;
}

export async function runComparison() {
    const container = $('compare-results');

    if (state.startNode === null || state.targetNode === null) {
        alert('Veuillez sélectionner une caserne (départ) et un site (arrivée).');
        return;
    }
    container.textContent = 'Comparaison des algorithmes...';

    try {
        container.innerHTML = renderComparison(
            await api.compareAlgorithms(state.startNode, state.targetNode, $('inter-critere').value));
    } catch (error) {
        console.error(error);
        container.innerHTML = errorHtml(error);
    }
}

