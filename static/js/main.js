// main.js - Point d'entrée principal et gestion des états globaux

let map = null;
let edgeLayer = null, arrowLayer = null, nodeLayer = null, legendEl = null;
let sitesData = [], routesData = [], fibreData = [];
let arrowData = [];
let currentView = 'routier';

// États pour les algorithmes (Sélection interactive)
let selectedStartNode = null;
let selectedTargetNode = null;

function setLoadingMessage(msg, isError = false) {
    const el = document.getElementById('loading-msg');
    if (el) {
        el.innerText = msg;
        if (isError) el.style.color = '#d93025';
    }
}

function openModal() {
    const modal = document.getElementById('generate-modal');
    if (modal) modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('generate-modal');
    if (modal) modal.style.display = 'none';
}

function switchView(type) {
    ['routier', 'fibre'].forEach(t => {
        const btn = document.getElementById('btn-' + t);
        if (btn) btn.classList.toggle('active', t === type);
    });
    currentView = type;
    if (typeof renderGraph === 'function') {
        renderGraph(type);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');

    setTimeout(() => {
        if (typeof map !== 'undefined' && map !== null) {
            map.invalidateSize();
        }
    }, 300);
}

// Adaptation de l'interface selon l'algorithme choisi
function onAlgoChange() {
    const algoName = document.getElementById('algo-select').value;
    const targetContainer = document.getElementById('target-container');
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall'].includes(algoName);

    if (targetContainer) {
        targetContainer.style.display = needsTarget ? 'block' : 'none';
    }
    if (!needsTarget) {
        selectedTargetNode = null;
        updateSelectionUI();
    }
}

// Logique de clic cyclique sur un nœud (Départ 🚗 ➔ Arrivée 🏁 ➔ Rien)
function handleNodeClick(nodeId) {
    const algoName = document.getElementById('algo-select').value;
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall'].includes(algoName);

    if (selectedStartNode === null) {
        selectedStartNode = nodeId;
        setNodeMarkerIcon(nodeId, 'car');
    } else if (selectedStartNode === nodeId && selectedTargetNode === null) {
        selectedStartNode = null;
        resetAllMarkersIcons();
    } else if (selectedTargetNode === null && needsTarget) {
        selectedTargetNode = nodeId;
        setNodeMarkerIcon(nodeId, 'flag');
    } else {
        selectedStartNode = null;
        selectedTargetNode = null;
        resetAllMarkersIcons();
    }

    updateSelectionUI();
}

function updateSelectionUI() {
    const startEl = document.getElementById('label-start');
    const targetEl = document.getElementById('label-target');
    if (startEl) startEl.innerText = selectedStartNode !== null ? selectedStartNode : "Aucun";
    if (targetEl) targetEl.innerText = selectedTargetNode !== null ? selectedTargetNode : "Aucun";
}

function setNodeMarkerIcon(nodeId, type) {
    if (typeof updateMarkerVisual === 'function') {
        updateMarkerVisual(nodeId, type);
    }
}

function resetAllMarkersIcons() {
    if (typeof resetMarkersVisual === 'function') {
        resetMarkersVisual();
    }
}

window.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadNetworkData();
});