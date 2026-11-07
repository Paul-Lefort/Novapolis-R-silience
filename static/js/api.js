// api.js - Couche réseau : uniquement des appels HTTP, aucun accès au DOM

import { API } from './config.js';

const unwrap = (json) => json.result ?? json.data ?? json;

async function request(url, options, fallbackMessage) {
    const res = await fetch(url, options);
    if (!res.ok) {
        let detail;
        try { detail = (await res.json()).detail; } catch { /* corps non JSON */ }
        const message = Array.isArray(detail) ? detail.map((d) => d.msg).filter(Boolean).join(' ; ') : detail;
        throw new Error(typeof message === 'string' && message ? message : fallbackMessage);
    }
    return res;
}

async function requestJson(url, options, fallbackMessage) {
    const res = await request(url, options, fallbackMessage);
    return unwrap(await res.json());
}

/** GET toujours frais : jamais servi depuis le cache du navigateur. */
const getFresh = (url, msg) => {
    const sep = url.includes('?') ? '&' : '?';
    return requestJson(`${url}${sep}_t=${Date.now()}`, { cache: 'no-store' }, msg);
};

const postJson = (url, body, msg) =>
    requestJson(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
    }, msg);

const postForm = (url, formData, msg) =>
    requestJson(url, { method: 'POST', body: formData }, msg);

async function fetchCsv(url) {
    const sep = url.includes('?') ? '&' : '?';
    const res = await request(`${url}${sep}_t=${Date.now()}`, { cache: 'no-store' }, `Impossible de charger ${url}`);
    const text = await res.text();
    return Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;
}

// --- Réseau ---
export async function fetchNetwork() {
    const [sites, routes, fibre] = await Promise.all([
        fetchCsv(API.sites), fetchCsv(API.routes), fetchCsv(API.fibre),
    ]);
    return { sites, routes, fibre };
}

export const generateNetwork = (nbSites) =>
    postJson(`${API.generate}?nombre_sites=${encodeURIComponent(nbSites)}`, undefined, 'Erreur de génération');

export const importNetwork = (formData) =>
    postForm(API.importNetwork, formData, "Erreur lors de l'import");

export const downloadAll = () => { window.location.href = API.downloadAll; };
export const downloadFile = (filename) => { window.location.href = API.download(filename); };

// --- Algorithmes & analyses ---
export const runAlgorithm = (algo, view, payload) =>
    postJson(`${API.runAlgo(algo)}?${new URLSearchParams({ view })}`, payload, 'Erreur lors du calcul');

export const fetchReport = (view) =>
    getFresh(`${API.report}?${new URLSearchParams({ view })}`, 'Erreur serveur lors de la récupération du rapport');

export const computeIntervention = (formData) =>
    postForm(API.intervention, formData, "Erreur lors du calcul de l'intervention");

// --- Fibre ---
export const fetchAcm = (algo) =>
    getFresh(`${API.acm}?${new URLSearchParams({ algo })}`, "Erreur lors du calcul de l'ACM");

export const compareAcm = () =>
    getFresh(API.compare, 'Erreur lors de la comparaison');

export const simulateBreakdown = (u, v) => {
    const form = new FormData();
    form.append('u', u);
    form.append('v', v);
    return postForm(API.breakdown, form, 'Erreur de simulation de panne');
};
