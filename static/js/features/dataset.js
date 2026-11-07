// features/dataset.js - Chargement, génération, import et export du réseau

import { state } from '../state.js';
import { DEFAULT_SITE_COUNT } from '../config.js';
import { $ } from '../utils.js';
import * as api from '../api.js';
import { renderGraph } from '../map/mapView.js';
import { closeModal, hideOverlay, setLoadingMessage, showOverlay } from '../ui/overlay.js';
import { populateCasernes, refreshSelectionMarkers } from '../ui/selection.js';
import { clearResults } from '../ui/results.js';

export async function loadNetworkData() {
    try {
        setLoadingMessage('Chargement du réseau...');
        const { sites, routes, fibre } = await api.fetchNetwork();
        Object.assign(state, { sites, routes, fibre });

        hideOverlay({ fade: true });
        renderGraph(state.view, { fit: true });
        refreshSelectionMarkers();
        populateCasernes();
        clearResults();
    } catch (error) {
        console.error('Erreur de chargement:', error);
        setLoadingMessage('Erreur lors de la récupération des CSV.', true);
    }
}

export async function submitGeneration() {
    const nbSites = $('nombre-sites-input').value;
    closeModal();
    showOverlay(`Génération de ${nbSites} sites sur le serveur...`);

    try {
        await api.generateNetwork(nbSites);
        setLoadingMessage('Génération réussie, rechargement du réseau...');
        setTimeout(loadNetworkData, 800);
    } catch (error) {
        console.error('Erreur:', error);
        setLoadingMessage('Erreur lors de la génération.', true);
        setTimeout(hideOverlay, 2000);
    }
}

export async function submitImport() {
    const files = {
        sites_file: $('import-sites').files[0],
        routes_file: $('import-routes').files[0],
        fibre_file: $('import-fibre').files[0],
    };
    if (!Object.values(files).some(Boolean)) {
        alert('Veuillez sélectionner au moins un fichier CSV à importer.');
        return;
    }

    const formData = new FormData();
    for (const [key, file] of Object.entries(files)) if (file) formData.append(key, file);

    const status = $('import-status');
    status.textContent = 'Envoi en cours...';
    showOverlay("Import des fichiers sur le serveur...");

    try {
        await api.importNetwork(formData);
        status.textContent = 'Import réussi !';
        setTimeout(loadNetworkData, 600);
    } catch (error) {
        console.error('Erreur:', error);
        status.textContent = "Erreur lors de l'import.";
        hideOverlay();
        alert('Erreur : ' + error.message);
    }
}

export async function loadPresetScenario(name) {
    const status = $('import-status');
    status.textContent = `Chargement du scénario ${name}...`;
    showOverlay(`Génération et application du scénario ${name}...`);

    try {
        await api.generateNetwork(DEFAULT_SITE_COUNT);
        status.textContent = 'Scénario chargé avec succès !';
        setTimeout(loadNetworkData, 600);
    } catch (error) {
        console.error('Erreur:', error);
        status.textContent = 'Erreur lors du chargement.';
        hideOverlay();
        alert('Erreur : ' + error.message);
    }
}

export const downloadZip = api.downloadAll;
export const downloadSingle = api.downloadFile;
