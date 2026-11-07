// api.js - Gestion des requêtes, du cache, du chargement, export/import et onglets

let currentActiveTab = null;

// Dans api.js -> toggleSidebarTab

function toggleSidebarTab(tabName) {
    const sidebar = document.getElementById('sidebar');
    const tabs = ['algo', 'intervention', 'export', 'import', 'stats'];

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

        // Adaptation contextuelle de la sélection au changement d'onglet
        if (tabName === 'intervention') {
            const selectEl = document.getElementById('inter-start-select');
            if (selectEl && selectEl.value) {
                selectedStartNode = isNaN(selectEl.value) ? selectEl.value : Number(selectEl.value);
            }
        }
        if (typeof refreshVisualMarkers === 'function') {
            refreshVisualMarkers();
        }
        if (typeof updateSelectionUI === 'function') {
            updateSelectionUI();
        }
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

    const activeView = (typeof currentView !== 'undefined' && currentView) ? currentView : 'routier';

    try {
        const response = await fetch(`/api/analysis/report?view=${activeView}`, {
            method: 'GET'
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur serveur lors de la récupération du rapport");
        }

        const responseData = await response.json();
        const data = responseData.result || responseData.data || responseData;

        const casernes = data.casernes_reference || [];
        const sitesIsoles = data.sites_isoles || [];
        const nonAtteignables = data.sites_non_atteignables || [];

        if (typeof highlightUnreachableNodes === 'function') {
            highlightUnreachableNodes(nonAtteignables);
        }

        const listIsoles = sitesIsoles.length > 0
            ? `<b style="color: #ea4335;">${sitesIsoles.join(', ')}</b>`
            : '<i>Aucun</i>';

        const listNonAtteignables = nonAtteignables.length > 0
            ? `<b style="color: #ea4335;">${nonAtteignables.join(', ')}</b><br>
               <button onclick="highlightUnreachableNodes([${nonAtteignables.join(',')}])" style="margin-top: 6px; padding: 4px 10px; font-size: 11px; background: #ea4335; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                   📍 Afficher les ${nonAtteignables.length} sites en rouge
               </button>`
            : '<i>Tous les sites sont couverts !</i>';

        statsContainer.innerHTML = `
            <div style="background: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #dadce0; display: flex; flex-direction: column; gap: 10px;">
                <p style="margin: 0; font-size: 11px; color: #5f6368;"><b>Vue analysée :</b> ${activeView.toUpperCase()}</p>

                <div style="border-bottom: 1px solid #eee; padding-bottom: 6px;">
                    <b style="color: #1a73e8;">1. Accessibilité des secours (BFS)</b><br>
                    <span style="font-size: 12px;">Casernes détectées : <b>${casernes.join(', ') || 'Aucune'}</b></span><br>
                    <span style="font-size: 12px;">Sites couverts : <b>${data.nb_sites_accessibles ?? 0}</b></span>
                </div>

                <div style="border-bottom: 1px solid #eee; padding-bottom: 6px;">
                    <b style="color: #1a73e8;">2. Connexité Fibre (DFS)</b><br>
                    <span style="font-size: 12px;">Composantes connexes : <b>${data.nb_composantes_fibre ?? 0}</b></span>
                </div>

                <div style="border-bottom: 1px solid #eee; padding-bottom: 6px;">
                    <b style="color: #1a73e8;">3. Itinéraire min. arcs (BFS)</b><br>
                    <span style="font-size: 11px; color: #5f6368;">Sélectionnez <b>BFS</b> dans l'onglet <b>Algorithmes 🚀</b> pour tracer l'itinéraire minimisant le nombre de sauts.</span>
                </div>

                <div style="border-bottom: 1px solid #eee; padding-bottom: 6px;">
                    <b style="color: #1a73e8;">4. Cycles orientés (DFS)</b><br>
                    <span style="font-size: 12px;">Statut : ${data.cycles_orientes ? '⚠️ <b style="color:#d93025;">Cycles détectés</b>' : '✅ <b style="color:#188038;">Graphe Acyclique (DAG)</b>'}</span>
                </div>

                <div>
                    <b style="color: #1a73e8;">5. Défaut de couverture & Isolation</b><br>
                    <span style="font-size: 12px;">Sites non atteignables : <b>${nonAtteignables.length}</b></span><br>
                    <div style="font-size: 11px; margin-top: 2px;">${listNonAtteignables}</div>
                    <span style="font-size: 12px; margin-top: 6px; display: block;">Sites isolés (degré 0) : ${listIsoles}</span>
                </div>
            </div>
        `;
    } catch (error) {
        console.error(error);
        statsContainer.innerHTML = `<span style="color: #d93025; font-weight: 500;">Erreur : ${error.message}</span>`;
    }
}

async function lancerCalculIntervention() {
    const resultsContainer = document.getElementById('intervention-results');
    resultsContainer.innerHTML = "Calcul du trajet d'intervention en cours...";

    if (selectedStartNode === null || selectedTargetNode === null) {
        alert("Veuillez sélectionner une caserne (départ 🚗) et un site (arrivée 🏁) sur la carte.");
        resultsContainer.innerHTML = `<span style="color: #d93025; font-size: 12px;">Veuillez choisir un départ et une arrivée.</span>`;
        return;
    }

    const fileInput = document.getElementById('inter-scenario-file').files[0];
    const manualArcs = document.getElementById('inter-manual-arcs').value;

    const formData = new FormData();
    formData.append('start', selectedStartNode);
    formData.append('target', selectedTargetNode);
    formData.append('view', currentView);

    if (fileInput) {
        formData.append('scenario_file', fileInput);
    }
    if (manualArcs) {
        formData.append('manual_arcs', manualArcs);
    }

    try {
        const response = await fetch('/api/analysis/calcul-intervention', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Erreur lors du calcul de l'intervention");
        }

        const responseData = await response.json();
        const data = responseData.result || responseData;

        const avant = data.avant_perturbation;
        const apres = data.apres_perturbation;
        const deg = data.degradation;

        if (apres.accessible && typeof highlightPath === 'function') {
            highlightPath(apres.path);
        }

        const isAccessible = apres.accessible;
        const badgeStatut = isAccessible
            ? `<span style="background: #e6f4ea; color: #137333; padding: 2px 8px; border-radius: 4px; font-weight: 600;">ACCESSIBLE</span>`
            : `<span style="background: #fce8e6; color: #c5221f; padding: 2px 8px; border-radius: 4px; font-weight: 600;">INACCESSIBLE</span>`;

        resultsContainer.innerHTML = `
            <div style="background: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #dadce0; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b style="font-size: 13px; color: #1a73e8;">Fiche d'intervention</b>
                    ${badgeStatut}
                </div>

                <div style="font-size: 12px; line-height: 1.4;">
                    <p style="margin: 0;"><b>Trajet :</b> Caserne ${selectedStartNode} ➔ Site ${selectedTargetNode}</p>
                    <p style="margin: 2px 0 0 0;"><b>Arcs fermés appliqués :</b> ${data.arcs_fermes_appliques.length}</p>
                </div>

                <hr style="border: none; border-top: 1px solid #eee; margin: 4px 0;">

                <div style="font-size: 12px;">
                    <b style="color: #5f6368;">Bilan du retard :</b>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 11px;">
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 3px 0;">Coût initial :</td>
                            <td style="text-align: right; font-weight: 600;">${avant.accessible ? `${avant.cost} min/km (${avant.nb_arcs} arcs)` : 'Inaccessible'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 3px 0;">Coût sous perturbation :</td>
                            <td style="text-align: right; font-weight: 600;">${apres.accessible ? `${apres.cost} min/km (${apres.nb_arcs} arcs)` : 'Inaccessible'}</td>
                        </tr>
                        ${isAccessible && avant.accessible ? `
                            <tr style="border-bottom: 1px solid #eee;">
                                <td style="padding: 3px 0; color: #d93025;">Retard absolu :</td>
                                <td style="text-align: right; font-weight: 600; color: #d93025;">+${deg.retard_absolu} min/km</td>
                            </tr>
                            <tr>
                                <td style="padding: 3px 0; color: #d93025;">Retard relatif :</td>
                                <td style="text-align: right; font-weight: 600; color: #d93025;">+${deg.retard_relatif_pct}%</td>
                            </tr>
                        ` : ''}
                    </table>
                </div>

                ${isAccessible ? `
                    <div style="background: #f8f9fa; padding: 6px; border-radius: 4px; font-size: 11px; margin-top: 4px;">
                        <b>Chemin retenu :</b><br>
                        <span style="color: #1a73e8;">${apres.path.join(' ➔ ')}</span>
                    </div>
                ` : ''}
            </div>
        `;

    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = `<span style="color: #d93025; font-size: 12px;">Erreur : ${error.message}</span>`;
    }
}
// api.js (extrait de loadNetworkData)

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

        // Remplir le menu déroulant des casernes
        populateCasernesDropdowns();

    } catch (error) {
        console.error("Erreur de chargement:", error);
        setLoadingMessage("Erreur lors de la récupération des CSV.", true);
    }
}