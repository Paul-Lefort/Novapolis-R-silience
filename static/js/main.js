// main.js - Point d'entrée principal de l'application

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
        // 1er clic : Définir le départ (Voiture)
        selectedStartNode = nodeId;
        setNodeMarkerIcon(nodeId, 'car');
    } else if (selectedStartNode === nodeId && selectedTargetNode === null) {
        // Re-clic sur le départ sans arrivée : Effacer tout
        selectedStartNode = null;
        resetAllMarkersIcons();
    } else if (selectedTargetNode === null && needsTarget) {
        // 2ème clic : Définir l'arrivée (Drapeau)
        selectedTargetNode = nodeId;
        setNodeMarkerIcon(nodeId, 'flag');
    } else {
        // 3ème clic (ou 2ème si l'algorithme n'a pas besoin de cible) : Réinitialisation complète
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

// Modification visuelle des marqueurs (à lier avec graphRender.js)
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

// Exécution de l'algorithme sélectionné via l'API
async function runSelectedAlgorithm() {
    const algoName = document.getElementById('algo-select').value;
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall'].includes(algoName);

    if (!selectedStartNode) {
        alert("Veuillez sélectionner un sommet de départ 🚗 sur la carte.");
        return;
    }
    if (needsTarget && !selectedTargetNode) {
        alert("Veuillez sélectionner un sommet d'arrivée 🏁 sur la carte pour cet algorithme.");
        return;
    }

    // Construction du payload à partir des données actuelles du graphe
    const nodes = sitesData.map(s => s.id);
    const rawEdges = currentView === 'fibre' ? fibreData : routesData;
    const edges = rawEdges.map((r, index) => ({
        id: `e${index}`,
        source: r.u,
        target: r.v,
        weight: Number(r.distance_km ?? r.cost ?? r.temps_normal ?? 1)
    }));

    const payload = {
        graph: {
            nodes: nodes,
            edges: edges,
            start: isNaN(selectedStartNode) ? selectedStartNode : Number(selectedStartNode),
            target: selectedTargetNode !== null ? (isNaN(selectedTargetNode) ? selectedTargetNode : Number(selectedTargetNode)) : undefined
        }
    };

    try {
        setLoadingMessage(`Exécution de ${algoName}...`);
        const response = await fetch(`/api/run/${algoName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors du calcul de l'algorithme");
        }

        const data = await response.json();
        console.log("Résultat de l'algorithme :", data);

        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';

        alert(`Algorithme ${algoName} exécuté avec succès ! (${data.step_count} étapes générées)`);

    } catch (error) {
        console.error("Erreur:", error);
        alert(`Erreur : ${error.message}`);
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadNetworkData();
});