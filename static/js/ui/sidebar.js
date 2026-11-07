// ui/sidebar.js - Menu latéral : onglets, repli et changement de vue

import { state } from '../state.js';
import { $, parseId } from '../utils.js';
import { renderGraph } from '../map/mapView.js';
import { refreshSelectionMarkers, updateSelectionUI } from './selection.js';
import { clearResults } from './results.js';

export function toggleTab(name) {
    const sidebar = $('sidebar');
    const alreadyOpen = !sidebar.classList.contains('collapsed') && state.activeTab === name;

    if (alreadyOpen) {
        sidebar.classList.add('collapsed');
        state.activeTab = null;
    } else {
        sidebar.classList.remove('collapsed');
        document.querySelectorAll('.sidebar-tab-content').forEach((panel) => {
            panel.hidden = panel.id !== `tab-${name}`;
        });
        state.activeTab = name;

        if (name === 'intervention') {
            const value = $('inter-start-select')?.value;
            if (value) state.startNode = parseId(value);
        }
        refreshSelectionMarkers();
        updateSelectionUI();
    }

    document.querySelectorAll('[data-action="toggle-tab"]').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.tab === state.activeTab);
    });

    // La carte change de largeur : on la recalcule après la transition CSS
    setTimeout(() => state.map?.invalidateSize(), 300);
}

export function switchView(view) {
    document.querySelectorAll('.view-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    renderGraph(view);
    refreshSelectionMarkers(); // renderGraph recrée les marqueurs : on réapplique 🚗 / 🏁
    clearResults();            // les résultats affichés concernaient l'autre vue
}
