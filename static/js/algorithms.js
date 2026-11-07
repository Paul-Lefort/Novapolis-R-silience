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

        // On passe la vue active (?view=routier ou ?view=fibre) pour que le backend lise le bon CSV
        const response = await fetch(`/api/run-network/${algoName}?view=${currentView}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors du calcul");
        }

        const data = await response.json();
        console.log("Résultat du serveur :", data);

        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';

        // Affichage direct du chemin en vert sur la carte
        const pathNodes = data.path || [];
        if (typeof highlightPath === 'function') {
            highlightPath(pathNodes);
        }

        alert(`Chemin trouvé avec succès ! (${pathNodes.length} étapes, coût total : ${data.cost})`);

    } catch (error) {
        console.error("Erreur:", error);
        alert(`Erreur : ${error.message}`);
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}