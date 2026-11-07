// api.js - Gestion des requêtes, du cache, du chargement, export/import et onglets

let currentActiveTab = null;

function toggleSidebarTab(tabName) {
    const sidebar = document.getElementById('sidebar');
    const tabs = ['algo', 'export', 'import', 'stats'];

    const isAlreadyOpen = !sidebar.classList.contains('collapsed') && currentActiveTab === tabName;

    if (isAlreadyOpen) {
        sidebar.classList.add('collapsed');
        currentActiveTab = null;
    } else {
        sidebar.classList.remove('collapsed');
        tabs.forEach(t => {
            const el = document.getElementById(`tab-${t}`);
            if (el) {
                el.style.display = (t === tabName) ? 'block' : 'none';
            }
        });
        currentActiveTab = tabName;
    }
}

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

async function submitMultiFileImport() {
    const sitesInput = document.getElementById('import-sites').files[0];
    const routesInput = document.getElementById('import-routes').files[0];
    const fibreInput = document.getElementById('import-fibre').files[0];

    if (!sitesInput && !routesInput && !fibreInput) {
        alert("Veuillez sélectionner au moins un fichier CSV à importer.");
        return;
    }

    const formData = new FormData();
    if (sitesInput) formData.append('sites_file', sitesInput);
    if (routesInput) formData.append('routes_file', routesInput);
    if (fibreInput) formData.append('fibre_file', fibreInput);

    const statusEl = document.getElementById('import-status');
    if (statusEl) statusEl.innerText = "Envoi en cours...";

    try {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            overlay.style.opacity = '1';
        }
        setLoadingMessage("Import des fichiers sur le serveur...");

        const response = await fetch('/api/import/network', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors de l'import");
        }

        if (statusEl) statusEl.innerText = "Import réussi !";
        setTimeout(loadNetworkData, 600);

    } catch (error) {
        console.error("Erreur:", error);
        if (statusEl) statusEl.innerText = "Erreur lors de l'import.";
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
        alert("Erreur : " + error.message);
    }
}

async function loadPresetScenario(scenarioName) {
    const statusEl = document.getElementById('import-status');
    if (statusEl) statusEl.innerText = `Chargement du scénario ${scenarioName}...`;

    try {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            overlay.style.opacity = '1';
        }
        setLoadingMessage(`Génération et application du scénario ${scenarioName}...`);

        // On utilise la route de génération existante sur le serveur comme scénario par défaut
        const response = await fetch(`/api/generate?nombre_sites=120`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors du chargement du scénario");
        }

        if (statusEl) statusEl.innerText = "Scénario chargé avec succès !";
        setTimeout(loadNetworkData, 600);

    } catch (error) {
        console.error("Erreur:", error);
        if (statusEl) statusEl.innerText = "Erreur lors du chargement.";
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
        alert("Erreur : " + error.message);
    }
}

async function fetchNetworkReport() {
    const statsContainer = document.getElementById('stats-info');
    statsContainer.innerHTML = "Calcul des indicateurs en cours...";

    try {
        const response = await fetch('/api/analysis/report', { method: 'POST' });
        if (!response.ok) throw new Error("Erreur lors de la récupération du rapport");

        const data = await response.json();

        statsContainer.innerHTML = `
            <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; border: 1px solid #dadce0;">
                <p><b>Casernes de référence :</b> ${data.casernes_reference.join(', ')}</p>
                <p><b>Sites accessibles :</b> ${data.nb_sites_accessibles}</p>
                <p><b>Composantes fibre :</b> ${data.nb_composantes_fibre}</p>
                <p><b>Cycles orientés (routes) :</b> ${data.cycles_orientes ? '⚠️ Présents' : '✅ Aucun'}</p>
                <p><b>Sites isolés :</b> ${data.sites_isoles.length}</p>
                <p><b>Non atteignables :</b> ${data.sites_non_atteignables.length}</p>
            </div>
        `;
    } catch (error) {
        console.error(error);
        statsContainer.innerHTML = `<span style="color: red;">Erreur : ${error.message}</span>`;
    }
}