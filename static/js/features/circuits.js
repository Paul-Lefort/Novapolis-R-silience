// features/circuits.js - Onglet « Circuits absorbants » (module 3)

import { $ } from '../utils.js';
import * as api from '../api.js';
import { badge, errorHtml, esc, num, table, yesNo } from '../ui/render.js';

const LABELS = { fini: 'fini', moins_infini: '−∞', inaccessible: 'inaccessible' };

function distanceCell(dist) {
    if (dist.etat === 'fini') return num(dist.valeur);
    if (dist.etat === 'moins_infini') return '<b class="danger" title="Peut être diminuée indéfiniment">−∞</b>';
    return '<span class="muted">∞</span>';
}

export function renderTest(t) {
    const rows = Object.keys(t.bellman_ford.distances).map((node) => {
        const bf = t.bellman_ford.distances[node];
        const fw = t.floyd_warshall.distances[node];
        const expected = t.attendu.etats[node];
        const ok = bf.etat === expected && fw.etat === expected;
        return [`<b>${esc(node)}</b>`, distanceCell(bf), distanceCell(fw),
            `${LABELS[expected]} ${ok ? '<span class="ok">✓</span>' : '<span class="danger">✗</span>'}`];
    });

    const arcs = t.aretes.map((a) => `${esc(a.u)}→${esc(a.v)} (${a.poids})`).join(', ');
    const circuit = t.circuit_trouve ? `<div class="text-xs">Circuit trouvé : <b>${t.circuit_trouve.map(esc).join(' → ')}</b></div>` : '';

    return `
        <div class="card stack">
            <div class="card-header"><b class="text-blue">${esc(t.titre)}</b>${badge(t.reussi, 'RÉUSSI', 'ÉCHEC')}</div>
            <div class="text-xs muted">${esc(t.description)}</div>
            <div class="text-xs"><b>Source :</b> ${esc(t.source)} · <b>Arcs :</b> ${arcs}</div>
            ${table(['Sommet', 'Bellman-Ford', 'Floyd-Warshall', 'Attendu'], rows)}
            <div class="text-sm">Circuit absorbant dans le graphe : ${yesNo(t.circuit_existe)}<br>
                Accessible depuis la source : Bellman-Ford ${yesNo(t.bellman_ford.circuit_accessible)}
                · Floyd-Warshall ${yesNo(t.floyd_warshall.circuit_accessible)}</div>
            ${circuit}
        </div>`;
}

export async function runCircuitTests() {
    const container = $('circuit-results');
    container.textContent = 'Exécution des tests...';

    try {
        const { tests, tous_reussis: allPassed } = await api.runCircuitTests();
        container.innerHTML =
            `<div class="text-sm ${allPassed ? 'ok' : 'danger'}"><b>${allPassed ? 'Tous les tests sont réussis.' : 'Au moins un test a échoué.'}</b></div>` +
            tests.map(renderTest).join('') +
            '<div class="notion">Une distance « −∞ » n\'est jamais affichée comme un nombre fini : elle peut être diminuée indéfiniment en tournant dans le circuit.</div>';
    } catch (error) {
        console.error(error);
        container.innerHTML = errorHtml(error);
    }
}
