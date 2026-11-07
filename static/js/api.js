// api.js - Gestion des requêtes, du cache, du chargement, de l'export et de l'import

async function submitGeneration() {
    const nbSites = document.getElementById('nombre-sites-input').value;
    closeModal();
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
    }
    setLoadingMessage(`Génération de ${nbSites} sites sur le serveur...`);

    try {
        const response = await fetch(`/api/generate?nombre_sites=${nbSites}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur de génération");
        }

        setLoadingMessage("Génération réussie, rechargement du réseau...");
        setTimeout(loadNetworkData, 800);
    } catch (error) {
        console.error("Erreur:", error);
        setLoadingMessage("Erreur lors de la génération.", true);
        setTimeout(() => {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.style.display = 'none';
        }, 2000);
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
            if (!res.ok) throw new Error(`Impossible de charger ${url}`);
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

// ==================== EXPORT & IMPORT ====================

function downloadZipArchive() {
    window.location.href = '/api/download/all';
}

function downloadSingle(filename) {
    window.location.href = `/api/download/${filename}`;
}

function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file) return;

    const statusEl = document.getElementById('import-status');
    if (statusEl) statusEl.innerText = `Fichier sélectionné : ${file.name}`;

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const parsedData = Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;

        alert(`Fichier ${file.name} analysé avec succès (${parsedData.length} lignes) !`);

        if (file.name.includes('sites')) {
            sitesData = parsedData;
        } else if (file.name.includes('routes')) {
            routesData = parsedData;
        } else if (file.name.includes('fibre')) {
            fibreData = parsedData;
        }

        if (typeof renderGraph === 'function') {
            renderGraph(currentView, true);
        }
    };
    reader.readAsText(file);
}