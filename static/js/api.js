// api.js - Gestion des requêtes, du cache et du chargement des données CSV

async function submitGeneration() {
    const nbSites = document.getElementById('nombre-sites-input').value;
    closeModal();
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'flex';
    overlay.style.opacity = '1';
    setLoadingMessage(`Génération de ${nbSites} sites...`);

    try {
        const response = await fetch(`/api/download/all?nombre_sites=${nbSites}&_t=${Date.now()}`);
        if (!response.ok) throw new Error("Erreur de génération");
        setTimeout(loadNetworkData, 800);
    } catch (error) {
        console.error("Erreur:", error);
        setLoadingMessage("Erreur lors de la génération.", true);
        setTimeout(() => { window.location.reload(true); }, 1500);
    }
}

async function loadNetworkData() {
    try {
        sitesData = [];
        routesData = [];
        fibreData = [];
        arrowData = [];

        const parse = async (url, msg) => {
            setLoadingMessage(msg);
            const separator = url.includes('?') ? '&' : '?';
            const res = await fetch(`${url}${separator}_t=${Date.now()}`, { cache: 'no-store' });
            const text = await res.text();
            return Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;
        };

        sitesData = await parse('/api/sites', "Chargement des sites...");
        routesData = await parse('/api/routes', "Chargement des routes...");
        fibreData = await parse('/api/fibre', "Chargement de la fibre...");

        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.style.display = 'none', 300);
        }

        renderGraph(currentView, true);
    } catch (error) {
        console.error("Erreur de chargement:", error);
        setLoadingMessage("Erreur lors de la récupération des CSV.", true);
    }
}