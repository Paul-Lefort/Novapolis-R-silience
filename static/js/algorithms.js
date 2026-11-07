// algorithms.js
async function runSelectedAlgorithm() {
    const algoName = document.getElementById('algo-select').value;
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall', 'bfs'].includes(algoName);

    if (selectedStartNode === null) {
        alert("Veuillez sélectionner un sommet de départ 🚗 sur la carte.");
        return;
    }
    if (needsTarget && selectedTargetNode === null) {
        alert("Veuillez sélectionner un sommet d'arrivée 🏁 sur la carte.");
        return;
    }

    const payload = {
        start: isNaN(selectedStartNode) ? selectedStartNode : Number(selectedStartNode),
        target: selectedTargetNode !== null ? (isNaN(selectedTargetNode) ? selectedTargetNode : Number(selectedTargetNode)) : undefined
    };

    try {
        setLoadingMessage(`Exécution de ${algoName}...`);

        const response = await fetch(`/api/pathfinding/run-algo?algo=${algoName}&view=${currentView}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors du calcul");
        }

        const responseData = await response.json();
        const data = responseData.result || responseData;

        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';

        const pathNodes = (data.path || []).map(id => isNaN(id) ? String(id) : Number(id));
        const cost = data.cost;
        const nbArcs = data.nb_arcs || 0;

        if (!data.accessible || pathNodes.length === 0) {
            alert(`⚠️ Aucun chemin valide n'existe entre ces sommets.`);
        } else {
            if (typeof highlightPath === 'function') {
                highlightPath(pathNodes);
            }
            alert(`[${algoName.toUpperCase()}] Chemin trouvé ! (${nbArcs} arcs, coût/durée : ${cost})`);
        }

    } catch (error) {
        console.error("Erreur:", error);
        alert(`Erreur : ${error.message}`);
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}