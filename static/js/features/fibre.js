// features/fibre.js - Onglet « Conception réseau fibre » : ACM (Kruskal / Prim), coûts égaux, panne de tronçon

import { $ } from '../utils.js';
import * as api from '../api.js';
import { highlightSegments } from '../map/highlights.js';
import { switchView } from '../ui/sidebar.js';
import { state } from '../state.js';
import { errorHtml, esc, fold, idList, table, withUnit, yesNo } from '../ui/render.js';

const results = () => $('fibre-acm-results');
const KE = 'k€';

function showError(error) {
    console.error(error);
    results().innerHTML = errorHtml(error);
}

// ---------- ACM ----------

export function renderAcm(d) {
    const edges = table(['U', 'V', `Coût (${KE})`, 'Statut'],
        d.edges_acm.map((e) => [esc(e.u), esc(e.v), withUnit(e.cost, '', 2), esc(e.statut)]));

    const orphans = d.composantes_non_raccordees;
    const groups = orphans.filter((c) => c.length > 1);
    const singles = orphans.length - groups.length;
    const orphanList = groups.map((c) => `<div class="text-xs"><b>${c.length}</b> sites : ${idList(c, 10)}</div>`).join('') +
        (singles ? `<div class="text-xs"><b>${singles}</b> site(s) sans aucune liaison fibre</div>` : '');
    const connectivity = d.est_connexe
        ? '<div class="alert alert-ok">Réseau connexe : arbre couvrant minimal complet.</div>'
        : `<div class="alert alert-ko">Réseau non connexe : forêt couvrante de ${d.nb_composantes} composantes.</div>
           ${fold(`Composantes non raccordées (${orphans.length})`, orphanList)}`;

    return `
        <div class="card">
            <b class="text-green">Conception réseau fibre (${esc(d.algo.toUpperCase())})</b>
            <p class="text-sm">Coût total minimal : <b>${withUnit(d.cost_total, KE)}</b></p>
            <p class="text-sm">Tronçons retenus : <b>${d.nb_edges_acm}</b></p>
            ${connectivity}
            ${fold(`Tronçons choisis (${d.nb_edges_acm})`, edges)}
        </div>`;
}

export async function runAcm() {
    const algo = $('acm-algo-select').value;
    if (state.view !== 'fibre') switchView('fibre');
    results().textContent = `Calcul de l'arbre couvrant minimal (${algo.toUpperCase()})...`;

    try {
        const data = await api.fetchAcm(algo);
        // Chaque arête de l'ACM est un segment indépendant (et non un chemin continu)
        highlightSegments(data.edges_acm.map((e) => [e.u, e.v]));
        results().innerHTML = renderAcm(data);
    } catch (error) {
        showError(error);
    }
}

// ---------- Comparaison Kruskal / Prim ----------

export async function runCompare() {
    results().textContent = 'Comparaison de Kruskal et Prim...';

    try {
        const { kruskal, prim, coherence_cout_total: same } = await api.compareAcm();
        results().innerHTML = `
            <div class="card text-sm">
                <b class="text-blue">Comparaison Kruskal vs Prim</b>
                ${table(['Algorithme', `Coût total (${KE})`, 'Tronçons'], [
                    ['Kruskal', withUnit(kruskal.cost_total, ''), kruskal.nb_edges_acm],
                    ['Prim', withUnit(prim.cost_total, ''), prim.nb_edges_acm],
                ])}
                <div class="status-line ${same ? 'ok' : 'danger'}">
                    ${same ? 'Coûts totaux identiques' : 'Divergence de coûts détectée'}
                </div>
            </div>`;
    } catch (error) {
        showError(error);
    }
}

// ---------- Coûts égaux : plusieurs ACM possibles ----------

export function renderTies(d) {
    const examples = d.exemples.map((x) => [
        `${esc(x.arete_hors_arbre.u)}–${esc(x.arete_hors_arbre.v)} (${x.arete_hors_arbre.cost})`,
        `${esc(x.remplace.u)}–${esc(x.remplace.v)} (${x.remplace.cost})`,
    ]);

    return `
        <div class="card stack">
            <b class="text-blue">Coûts égaux et arbres couvrants multiples</b>
            <div class="text-sm">
                Plusieurs ACM de même coût : ${yesNo(d.plusieurs_acm_possibles)}<br>
                Échanges possibles sans changer le coût : <b>${d.nb_echanges_possibles}</b><br>
                Coûts apparaissant plusieurs fois : <b>${d.nb_couts_dupliques}</b> valeur(s) sur ${d.nb_aretes} tronçons<br>
                Kruskal et Prim retournent les mêmes tronçons : ${yesNo(d.kruskal_prim_memes_aretes)}
            </div>
            ${examples.length ? fold('Exemples d\'échanges', table(['Tronçon hors arbre', 'Peut remplacer'], examples)) : ''}
            <div class="notion">Si une arête hors de l'arbre coûte autant que la plus chère des arêtes du chemin qui la relie dans l'arbre,
                on peut les échanger : l'arbre change, pas le coût. Kruskal et Prim peuvent donc choisir des arbres différents,
                mais leur coût total est toujours égal.</div>
        </div>`;
}

export async function runTies() {
    results().textContent = 'Analyse des coûts égaux...';
    try {
        results().innerHTML = renderTies(await api.fetchFibreTies());
    } catch (error) {
        showError(error);
    }
}

// ---------- Panne de tronçon ----------

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
        const [eu, ev] = [esc(u), esc(v)];

        if (!data.impact_acm) {
            results().innerHTML = `
                <div class="card card-soft text-sm">
                    Le tronçon (${eu}, ${ev}) ne fait pas partie de l'arbre couvrant minimal initial.
                    Aucun impact sur le réseau principal.
                </div>`;
        } else if (data.raccordement_possible) {
            const s = data.troncon_secours;
            results().innerHTML = `
                <div class="card text-sm">
                    <b class="danger">Panne sur le tronçon (${eu}, ${ev})</b><br>
                    - Tronçon de secours : <b>${esc(s.u)} – ${esc(s.v)}</b><br>
                    - Coût du raccordement : <b>${withUnit(s.cost, KE)}</b><br>
                    - Surcoût induit : <b>+${withUnit(data.surcout, KE)}</b><br>
                    - Nouveau coût total : <b>${withUnit(data.nouveau_cout_total, KE)}</b>
                </div>`;
        } else {
            results().innerHTML = `
                <div class="alert alert-ko">
                    Panne critique : aucun tronçon alternatif pour reconnecter le réseau.
                </div>`;
        }
    } catch (error) {
        showError(error);
    }
}
