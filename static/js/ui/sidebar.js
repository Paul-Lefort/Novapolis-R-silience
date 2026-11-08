// ui/sidebar.js - Menu latéral : onglets, repli et changement de vue

import { state } from '../state.js';
import { WIDE_TABS } from '../config.js';
import { $, parseId } from '../utils.js';
import { renderGraph } from '../map/mapView.js';
import { refreshSelectionMarkers, updateSelectionUI } from './selection.js';
import { clearResults } from './results.js';

export function toggleTab(name) {
    const sidebar = $('sidebar');
    const alreadyOpen = !sidebar.classList.contains('collapsed') && state.activeTab === name;

    if (alreadyOpen) {
        sidebar.classList.add('collapsed');
        sidebar.classList.remove('wide');
        state.activeTab = null;
    } else {
        sidebar.classList.remove('collapsed');
        document.querySelectorAll('.sidebar-tab-content').forEach((panel) => {
            panel.hidden = panel.id !== `tab-${name}`;
        });
        state.activeTab = name;
        sidebar.classList.toggle('wide', WIDE_TABS.has(name));

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

/** keepResults : conserve les zones de résultats (ex. affichage d'un scénario sur la carte). */
export function switchView(view, { keepResults = false } = {}) {
    document.querySelectorAll('.view-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    renderGraph(view);
    refreshSelectionMarkers(); // renderGraph recrée les marqueurs : on réapplique 🚗 / 🏁
    if (!keepResults) clearResults(); // les résultats affichés concernaient l'autre vue
}
