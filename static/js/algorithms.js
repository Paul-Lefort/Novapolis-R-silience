// algorithms.js - Logique d'exécution des algorithmes sur le réseau

async function runSelectedAlgorithm() {
    const algoName = document.getElementById('algo-select').value;
    const needsTarget = ['dijkstra', 'bellman_ford', 'floyd_warshall'].includes(algoName);

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
        setLoadingMessage(`Exécution de ${algoName} via le serveur...`);

        const res = await fetch(`/api/run-network/${algoName}?view=${currentView}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Erreur lors du calcul");
        }

        const responseData = await res.json();
        console.log("Résultat du serveur :", responseData);

        // Extraction du payload depuis make_response (data, result, payload ou racine)
        const resultPayload = responseData.result || responseData.data || responseData.payload || responseData;

        // Récupération des sommets du chemin
        const rawPath = resultPayload.path || responseData.path || [];
        const pathNodes = rawPath.map(id => isNaN(id) ? String(id) : Number(id));

        // Récupération du coût et du message
        const cost = resultPayload.cost ?? responseData.cost ?? null;
        const message = resultPayload.message || responseData.message;

        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';

        if (pathNodes.length === 0 || cost === null || cost === undefined) {
            const errorMsg = message || `Aucun chemin valide n'existe entre ces sommets en respectant les contraintes.`;
            alert(`⚠️ ${errorMsg}`);
        } else {
            if (typeof highlightPath === 'function') {
                highlightPath(pathNodes);
            }
            const displayCost = typeof cost === 'number' ? cost.toFixed(2) : cost;
            alert(`Chemin trouvé avec succès ! (${pathNodes.length} étapes, coût total : ${displayCost})`);
        }

    } catch (error) {
        console.error("Erreur:", error);
        alert(`Erreur : ${error.message}`);
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}