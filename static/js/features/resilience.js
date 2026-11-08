// features/resilience.js - Onglet « Résilience et scénarios » (module 5)

import { $ } from '../utils.js';
import * as api from '../api.js';
import { CLOSED_STYLE, highlightSegments } from '../map/highlights.js';
import { switchView } from '../ui/sidebar.js';
import { errorHtml, esc, idList, num, table, yesNo } from '../ui/render.js';

const SHORT = { normal: 'Normale', axe_ferme: 'Axe fermé', panne_fibre: 'Panne fibre' };
let last = null;

export function renderScenarios(d) {
    const { unite: u, nb_demandes: n, casernes, types_sensibles_utilises: types, note_types_sensibles: note } = d.parametres;
    const [normal] = d.scenarios;

    const cellOf = (fn, tone) => d.scenarios.map((s, i) => {
        const value = fn(s);
        const text = value ?? '—';
        const worse = tone && i > 0 && fn(s) !== fn(normal) && typeof value === 'string';
        return worse ? `<b class="danger">${text}</b>` : text;
    });

    const rows = [
        ['Demandes évaluées', ...cellOf((s) => s.routier.nb_demandes)],
        ['Devenues inaccessibles', ...cellOf((s) => String(s.routier.nb_nouvellement_inaccessibles), true)],
        [`Retard moyen (${u})`, ...cellOf((s) => num(s.routier.retard_moyen), true)],
        [`Retard maximal (${u})`, ...cellOf((s) => num(s.routier.retard_max), true)],
        ['Retard moyen (%)', ...cellOf((s) => num(s.routier.retard_moyen_pct), true)],
        ['Sites sensibles accessibles', ...cellOf((s) => `${num(s.routier.part_sensibles_accessibles_pct, 1)} %`, true)],
        ['Composantes de fibre', ...cellOf((s) => String(s.fibre.nb_composantes), true)],
        ['Raccordement (k€)', ...cellOf((s) => (s.fibre.panne ? (s.fibre.raccordement_possible ? num(s.fibre.cout_raccordement) : 'impossible') : null))],
        ['Coût total ACM (k€)', ...cellOf((s) => num(s.fibre.cout_total_acm))],
    ];

    const details = d.scenarios.map((s, i) => {
        const showable = s.perturbation.arcs_routiers_fermes.length || s.perturbation.troncon_fibre;
        return `<div class="text-xs"><b>${esc(SHORT[s.id])}.</b> ${esc(s.description)}
            ${showable ? `<button class="btn btn-sm mt-sm" data-action="show-scenario" data-index="${i}">Voir sur la carte</button>` : ''}</div>`;
    }).join('');

    return `
        <div class="card stack">
            <b class="text-blue">Comparaison de trois scénarios</b>
            <div class="text-xs muted">${n} demandes · ${casernes.length} caserne(s) · sites sensibles : ${idList(types) || '—'}</div>
            ${note ? `<div class="alert alert-ko">${esc(note)}</div>` : ''}
            ${table(['Indicateur', ...d.scenarios.map((s) => esc(SHORT[s.id]))], rows)}
            ${details}
            <div class="text-sm">Scénario de référence inchangé après les calculs : ${yesNo(d.reference_inchangee)}</div>
        </div>`;
}

export async function runScenarios() {
    const container = $('scenario-results');
    container.textContent = 'Évaluation des scénarios...';

    try {
        last = await api.fetchScenarios({
            nb_demandes: $('res-nb').value,
            critere: $('res-critere').value,
            axe: $('res-axe').value.trim(),
            troncon: $('res-troncon').value.trim(),
            types_sensibles: $('res-types').value.trim(),
        });
        container.innerHTML = renderScenarios(last);
    } catch (error) {
        console.error(error);
        container.innerHTML = errorHtml(error);
    }
}

/** Montre la perturbation d'un scénario : arcs fermés en rouge pointillé, raccordement en vert. */
export function showScenario(index) {
    const s = last?.scenarios[Number(index)];
    if (!s) return;

    const { arcs_routiers_fermes: arcs, troncon_fibre: fibre } = s.perturbation;
    if (arcs.length) {
        switchView('routier', { keepResults: true });
        highlightSegments(arcs, { style: CLOSED_STYLE });
    } else if (fibre) {
        switchView('fibre', { keepResults: true });
        highlightSegments([[fibre.u, fibre.v]], { style: CLOSED_STYLE });
        const secours = s.fibre.troncon_secours;
        if (secours) highlightSegments([[secours.u, secours.v]], { append: true });
    }
}
