// features/report.js - Onglet « Diagnostic & accessibilité » (BFS / DFS, module 1)

import { $ } from '../utils.js';
import * as api from '../api.js';
import { highlightPath, highlightUnreachableNodes } from '../map/highlights.js';
import { esc, errorHtml, fold, idList } from '../ui/render.js';

let lastReport = null;

const block = (title, body, notion, last = false) =>
    `<div class="report-block${last ? ' last' : ''}"><b class="text-blue">${title}</b><br>${body}` +
    `<div class="notion">Notion : ${notion}</div></div>`;

const line = (text) => `<div class="text-sm">${text}</div>`;

function fibreComponents(components) {
    const groups = components.filter((c) => c.length > 1);
    const singles = components.length - groups.length;
    const list = groups.slice(0, 10)
        .map((c, i) => `<div class="text-xs">#${i + 1} · <b>${c.length}</b> sites : ${idList(c, 10)}</div>`)
        .join('');
    return line(`Composantes connexes : <b>${components.length}</b>`) +
        (groups.length ? fold('Détail des composantes', list + (groups.length > 10 ? `<div class="text-xs muted">… et ${groups.length - 10} autres</div>` : '')) : '') +
        (singles ? line(`dont <b>${singles}</b> site(s) sans liaison fibre`) : '');
}

export function renderReport(d) {
    const nonAtteignables = d.sites_non_atteignables;
    const cycle = d.cycle_sens_uniques;

    const unreachableHtml = nonAtteignables.length
        ? `<b class="danger">${idList(nonAtteignables)}</b><br>
           <button class="btn btn-sm btn-block mt-sm" data-action="show-unreachable">Afficher sur la carte</button>`
        : '<i>Tous les sites sont couverts.</i>';

    const cycleHtml = cycle
        ? `Circuit de sens uniques : <b class="danger">${cycle.map(esc).join(' → ')}</b><br>
           <button class="btn btn-sm btn-block mt-sm" data-action="show-cycle">Afficher le circuit</button>`
        : 'Circuit de sens uniques : <b class="ok">aucun</b>';

    return `
        <div class="card stack">
            ${d.avertissement ? `<div class="alert alert-ko">${esc(d.avertissement)}</div>` : ''}

            ${block('1. Accessibilité depuis les casernes (BFS)',
                line(`Casernes (sources) : <b>${idList(d.casernes_reference) || 'aucune'}</b>`) +
                line(`Sites couverts : <b>${d.nb_sites_accessibles} / ${d.nb_sites}</b>`),
                'accessibilité depuis une ou plusieurs sources, en suivant le sens des routes. Différente de la connexité ordinaire ' +
                `(${d.nb_composantes_faibles} composante(s), sens ignoré) et de la connexité forte (${d.nb_composantes_fortes} composante(s), tout sommet atteint tout autre).`)}

            ${block('2. Connexité de la fibre (DFS)', fibreComponents(d.composantes_fibre),
                'connexité ordinaire du graphe fibre, non orienté.')}

            ${block('3. Itinéraire minimisant les arcs (BFS)',
                '<span class="text-xs muted">Choisissez <b>BFS</b> dans l\'onglet Algorithmes pour tracer l\'itinéraire.</span>',
                'plus court chemin en nombre d\'arcs, sans tenir compte des durées.')}

            ${block('4. Cycles orientés (DFS)',
                line(`Boucles aller-retour (double sens) : <b>${d.cycle_aller_retour ? 'oui' : 'non'}</b>`) +
                `<div class="text-sm">${cycleHtml}</div>` +
                line(`Arcs à sens unique : <b>${d.nb_arcs_sens_uniques}</b>`),
                'cycle orienté du graphe routier (arc retour vers un sommet en cours de visite). Un double sens forme déjà un cycle u → v → u : ' +
                'on cherche donc aussi un circuit formé uniquement de sens uniques.')}

            ${block('5. Sites isolés et non atteignables',
                line(`Non atteignables par les pompiers : <b>${nonAtteignables.length}</b>`) +
                `<div class="text-xs">${unreachableHtml}</div>` +
                line(`Isolés sur le réseau routier (degré 0) : ${d.sites_isoles.length ? `<b class="danger">${idList(d.sites_isoles)}</b>` : '<i>aucun</i>'}`) +
                line(`Isolés sur la fibre : ${d.sites_isoles_fibre.length ? `<b>${d.sites_isoles_fibre.length}</b>` : '<i>aucun</i>'}`),
                'non atteignable = inaccessible depuis toutes les casernes en suivant le sens des routes ; isolé = aucun arc entrant ni sortant.', true)}
        </div>`;
}

export async function runReport() {
    const container = $('report-results');
    container.textContent = 'Calcul des indicateurs en cours...';

    try {
        lastReport = await api.fetchReport();
        highlightUnreachableNodes(lastReport.sites_non_atteignables);
        container.innerHTML = renderReport(lastReport);
    } catch (error) {
        console.error(error);
        container.innerHTML = errorHtml(error);
    }
}

export const showUnreachable = () => lastReport && highlightUnreachableNodes(lastReport.sites_non_atteignables);
export const showCycle = () => lastReport?.cycle_sens_uniques && highlightPath(lastReport.cycle_sens_uniques);

