// config.js - Constantes partagées par toute l'application

/** Algorithmes qui nécessitent un sommet d'arrivée. */
export const NEEDS_TARGET = new Set(['dijkstra', 'bellman_ford', 'floyd_warshall', 'bfs']);

export const DEFAULT_SITE_COUNT = 120;

export const NODE_COLORS = { routier: '#4285F4', fibre: '#0b8043' };
export const CASERNE_COLOR = '#e8710a';

export const MAP_DEFAULTS = { center: [48.8566, 2.3522], zoom: 10 };

export const API = {
    sites: '/api/sites',
    routes: '/api/routes',
    fibre: '/api/fibre',
    generate: '/api/generate',
    importNetwork: '/api/import/network',
    runAlgo: (algo) => `/api/run-network/${encodeURIComponent(algo)}`,
    report: '/api/resilience/report',
    intervention: '/api/resilience/intervention',
    compareAlgos: '/api/resilience/compare-algos',
    negativeTests: '/api/resilience/negative-cycle-tests',
    scenarios: '/api/resilience/scenarios',
    fibreTies: '/api/resilience/fibre-ties',
    acm: '/api/fibre/acm',
    compare: '/api/fibre/comparer',
    breakdown: '/api/fibre/simuler-panne-troncon',
    downloadAll: '/api/download/all',
    download: (filename) => `/api/download/${filename}`,
};

/** Menus qui ont besoin de plus de largeur (tableaux). */
export const WIDE_TABS = new Set(['intervention', 'resilience', 'circuits']);
