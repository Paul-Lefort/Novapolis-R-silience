// features/algorithms.js - Onglet « Algorithmes de cheminement »

import { state } from '../state.js';
import { NEEDS_TARGET } from '../config.js';
import { $, parseId } from '../utils.js';
import * as api from '../api.js';
import { highlightPath, highlightSegments } from '../map/highlights.js';
import { hideOverlay, showOverlay } from '../ui/overlay.js';
import { refreshSelectionMarkers, updateSelectionUI } from '../ui/selection.js';

export function onAlgoChange() {
    const needsTarget = NEEDS_TARGET.has($('algo-select').value);
    $('target-container').hidden = !needsTarget;

    if (!needsTarget) {
        state.targetNode = null;
        refreshSelectionMarkers();
        updateSelectionUI();
    }
}

// ---------- Lecture des résultats (format de app/algorithme/*.run()) ----------

const fmtCost = (cost) => (cost == null ? 'n/a' : Number(cost).toFixed(2));
const NO_PATH = "⚠️ Aucun chemin valide n'existe entre ces sommets.";

/** Reconstruit le chemin start -> target à partir des arêtes (parent, enfant) d'un arbre de parcours. */
function pathFromTree(treeEdges, start, target) {
    const parent = new Map(treeEdges.map(([u, v]) => [String(v), u]));
    const path = [target];
    let current = target;

    while (String(current) !== String(start)) {
        const p = parent.get(String(current));
        if (p === undefined || path.length > treeEdges.length + 1) return [];
        path.push(p);
        current = p;
    }
    return path.reverse().map(parseId);
}

/**
 * Transforme la réponse brute en { error } ou { path | segments, message }.
 * - dijkstra / bellman_ford / floyd_warshall : { path, cost }
 * - bfs : { visited_nodes, bfs_edges }  -> chemin minimal en arcs reconstruit depuis l'arbre
 * - dfs : { visited_nodes, dfs_edges }  -> affichage de l'arbre de parcours
 */
function interpretResult(algo, data, start, target) {
    const label = algo.toUpperCase();

    if (algo === 'dfs') {
        const visited = data.visited_nodes ?? [];
        return {
            segments: data.dfs_edges ?? [],
            message: `[${label}] ${visited.length} sommets visités depuis ${start}.`,
        };
    }

    if (algo === 'bfs') {
        const path = pathFromTree(data.bfs_edges ?? [], start, target);
        if (path.length === 0) return { error: NO_PATH };
        return { path, message: `[${label}] Chemin trouvé ! (${path.length - 1} arcs, minimum possible)` };
    }

    if (data.negative_cycle) {
        return { error: '⚠️ Cycle de poids négatif détecté : aucun plus court chemin défini.' };
    }

    const path = (data.path ?? []).map(parseId);
    if (path.length === 0) return { error: data.message || NO_PATH };
    return {
        path,
        message: `[${label}] Chemin trouvé ! (${path.length - 1} arcs, coût : ${fmtCost(data.cost)})`,
    };
}

// ---------- Lancement ----------

export async function runSelectedAlgorithm() {
    const algo = $('algo-select').value;

    if (state.startNode === null) {
        alert('Veuillez sélectionner un sommet de départ 🚗 sur la carte.');
        return;
    }
    if (NEEDS_TARGET.has(algo) && state.targetNode === null) {
        alert("Veuillez sélectionner un sommet d'arrivée 🏁 sur la carte.");
        return;
    }

    let data;
    try {
        showOverlay(`Exécution de ${algo}...`);
        data = await api.runAlgorithm(algo, state.view, {
            start: state.startNode,
            target: state.targetNode ?? undefined,
        });
    } catch (error) {
        console.error('Erreur:', error);
        alert(`Erreur : ${error.message}`);
        return;
    } finally {
        hideOverlay();
    }

    const outcome = interpretResult(algo, data, state.startNode, state.targetNode);
    if (outcome.error) {
        alert(outcome.error);
        return;
    }

    if (outcome.segments) highlightSegments(outcome.segments);
    else highlightPath(outcome.path);
    alert(outcome.message);
}
