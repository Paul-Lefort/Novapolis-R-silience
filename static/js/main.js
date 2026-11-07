// main.js - Point d'entrée : initialisation et câblage des événements (délégation via data-action)

import { initMap } from './map/mapView.js';
import { openModal, closeModal } from './ui/overlay.js';
import { handleNodeClick, onCaserneChange } from './ui/selection.js';
import { switchView, toggleTab } from './ui/sidebar.js';
import * as dataset from './features/dataset.js';
import * as algorithms from './features/algorithms.js';
import * as intervention from './features/intervention.js';
import * as fibre from './features/fibre.js';
import * as report from './features/report.js';
import * as negativeCycles from './features/negativeCycles.js';
import * as benchmark from './features/benchmark.js';

// data-action="..." -> handler (reçoit l'élément cliqué)
const clickActions = {
    'open-modal': openModal,
    'close-modal': closeModal,
    'submit-generation': dataset.submitGeneration,
    'toggle-tab': (el) => toggleTab(el.dataset.tab),
    'switch-view': (el) => switchView(el.dataset.view),
    'run-algo': algorithms.runSelectedAlgorithm,
    'run-intervention': intervention.runIntervention,
    'run-acm': fibre.runAcm,
    'compare-acm': fibre.runCompare,
    'simulate-breakdown': fibre.runBreakdown,
    'download-zip': dataset.downloadZip,
    'download-file': (el) => dataset.downloadSingle(el.dataset.file),
    'import-files': dataset.submitImport,
    'load-preset': (el) => dataset.loadPresetScenario(el.dataset.scenario),
    'run-report': report.runReport,
    'show-unreachable': report.showUnreachable,
    'run-negative-cycles': negativeCycles.runNegativeCycleCheck,
    'run-platform-benchmark': benchmark.runPlatformBenchmark,
};

// data-change="..." -> handler (reçoit l'élément modifié)
const changeActions = {
    'algo-changed': algorithms.onAlgoChange,
    'caserne-changed': (el) => onCaserneChange(el.value),
};

function bindEvents() {
    document.addEventListener('click', (e) => {
        const el = e.target.closest('[data-action]');
        if (el) clickActions[el.dataset.action]?.(el);
    });
    document.addEventListener('change', (e) => {
        const el = e.target.closest('[data-change]');
        if (el) changeActions[el.dataset.change]?.(el);
    });
}

initMap(handleNodeClick);
bindEvents();
dataset.loadNetworkData();
