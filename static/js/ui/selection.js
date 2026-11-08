// ui/selection.js - Sélection départ/arrivée sur la carte et synchronisation de l'interface

import { state } from '../state.js';
import { NEEDS_TARGET } from '../config.js';
import { $, parseId } from '../utils.js';
import { clearOverlays, resetMarkers, setMarkerRole } from '../map/highlights.js';

const sameText = (a, b) => String(a ?? '').toLowerCase() === String(b ?? '').toLowerCase();

export function refreshSelectionMarkers() {
    resetMarkers();
    clearOverlays();
    if (state.startNode !== null) setMarkerRole(state.startNode, 'start');
    if (state.targetNode !== null) setMarkerRole(state.targetNode, 'target');
}

export function updateSelectionUI() {
    const label = (node) => (node !== null ? node : 'Aucun');
    const set = (id, text) => { const el = $(id); if (el) el.textContent = text; };

    set('label-start', label(state.startNode));
    set('label-target', label(state.targetNode));
    set('inter-target', label(state.targetNode));
}

/**
 * Clic sur un sommet.
 * - Onglet Intervention : le départ vient de la liste, le clic bascule l'arrivée.
 * - Autres onglets : clic 1 = départ 🚗, clic 2 = arrivée 🏁, clic 3 = nouveau départ.
 */
export function handleNodeClick(nodeId) {
    if (state.activeTab === 'intervention') {
        state.targetNode = state.targetNode === nodeId ? null : nodeId;
    } else {
        const algo = $('algo-select')?.value || 'dijkstra';
        const needsTarget = NEEDS_TARGET.has(algo);

        if (state.startNode === null) {
            state.startNode = nodeId;
        } else if (state.startNode === nodeId && state.targetNode === null) {
            state.startNode = null;
        } else if (state.targetNode === null && needsTarget) {
            state.targetNode = nodeId;
        } else {
            state.startNode = nodeId;
            state.targetNode = null;
        }
    }
    refreshSelectionMarkers();
    updateSelectionUI();
}

/** Remplit la liste des casernes (ou, à défaut, de tous les sites). */
export function populateCasernes() {
    const select = $('inter-start-select');
    if (!select) return;

    const casernes = state.sites.filter((s) => sameText(s.type, 'caserne'));
    const source = casernes.length > 0 ? casernes : state.sites;

    select.replaceChildren(...source.map((s) => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = `🏢 ${s.nom || 'Caserne ' + s.id} (ID: ${s.id})`;
        return option;
    }));
}

export function onCaserneChange(value) {
    if (state.activeTab !== 'intervention') return;
    state.startNode = parseId(value);
    refreshSelectionMarkers();
    updateSelectionUI();
}
