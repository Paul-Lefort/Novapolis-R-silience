// main.js - Point d'entrée principal et gestion des états globaux

let map = null;
let edgeLayer = null, arrowLayer = null, nodeLayer = null, legendEl = null;
let sitesData = [], routesData = [], fibreData = [];
let arrowData = [];
let currentView = 'routier';

// États pour les algorithmes
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

function onAlgoChange() {
    const algoName = document.getElementById('algo-select').value;
    const targetContainer = document.getElementById('target-container');
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall', 'bfs'].includes(algoName);

    if (targetContainer) {
        targetContainer.style.display = needsTarget ? 'block' : 'none';
    }
    if (!needsTarget) {
        selectedTargetNode = null;
        updateSelectionUI();
    }
}

function strEquals(str1, str2) {
    return String(str1 || '').toLowerCase() === String(str2 || '').toLowerCase();
}

// Remplissage automatique de la liste déroulante des casernes pour le menu Intervention
function populateCasernesDropdowns() {
    const selectEl = document.getElementById('inter-start-select');
    if (!selectEl) return;

    const casernes = sitesData.filter(s => strEquals(s.type, 'caserne'));
    const sourceList = casernes.length > 0 ? casernes : sitesData;

    selectEl.innerHTML = '';
    sourceList.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.text = `🏢 ${s.nom || 'Caserne ' + s.id} (ID: ${s.id})`;
        selectEl.appendChild(option);
    });
}

// Changement manuel de la caserne dans le menu Intervention
function onCaserneSelectChange(nodeId) {
    if (currentActiveTab === 'intervention') {
        selectedStartNode = isNaN(nodeId) ? nodeId : Number(nodeId);
        refreshVisualMarkers();
        updateSelectionUI();
    }
}

// Clic sur un sommet de la carte : comportement dynamique selon l'onglet actif
function handleNodeClick(nodeId) {
    const activeTab = (typeof currentActiveTab !== 'undefined') ? currentActiveTab : 'algo';

    if (activeTab === 'intervention') {
        // Mode Intervention : Départ verrouillé sur le select, le clic définit uniquement l'Arrivée
        if (selectedTargetNode === nodeId) {
            selectedTargetNode = null;
        } else {
            selectedTargetNode = nodeId;
        }
    } else {
        // Mode Algorithmes (ou autre) : Clic libre (Clic 1 = Départ 🚗, Clic 2 = Arrivée 🏁, Clic 3 = Reset)
        const algoName = document.getElementById('algo-select')?.value || 'dijkstra';
        const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall', 'bfs'].includes(algoName);

        if (selectedStartNode === null) {
            selectedStartNode = nodeId;
        } else if (selectedStartNode === nodeId && selectedTargetNode === null) {
            selectedStartNode = null;
        } else if (selectedTargetNode === null && needsTarget) {
            selectedTargetNode = nodeId;
        } else {
            selectedStartNode = nodeId;
            selectedTargetNode = null;
        }
    }

    refreshVisualMarkers();
    updateSelectionUI();
}

function refreshVisualMarkers() {
    resetAllMarkersIcons();
    if (selectedStartNode !== null) {
        setNodeMarkerIcon(selectedStartNode, 'car');
    }
    if (selectedTargetNode !== null) {
        setNodeMarkerIcon(selectedTargetNode, 'flag');
    }
}

function updateSelectionUI() {
    const startEl = document.getElementById('label-start');
    const targetEl = document.getElementById('label-target');
    const interTarget = document.getElementById('inter-target');

    const startVal = selectedStartNode !== null ? selectedStartNode : "Aucun";
    const targetVal = selectedTargetNode !== null ? selectedTargetNode : "Aucun";

    if (startEl) startEl.innerText = startVal;
    if (targetEl) targetEl.innerText = targetVal;
    if (interTarget) interTarget.innerText = targetVal;
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