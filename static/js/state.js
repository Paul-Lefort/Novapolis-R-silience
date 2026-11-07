// state.js - État global unique de l'application (remplace les `let` globaux)

export const state = {
    // Carte Leaflet
    map: null,
    layers: { edges: null, arrows: null, nodes: null, casernes: null, path: null, unreachable: null },

    // Données du réseau
    sites: [],
    routes: [],
    fibre: [],

    // Index dérivés (clés = String(id))
    positions: new Map(), // id -> [lat, lon]
    markers: new Map(),   // id -> L.CircleMarker
    arrows: [],           // flèches des arcs à sens unique

    // Interface
    view: 'routier',      // 'routier' | 'fibre'
    activeTab: null,      // onglet actif de la sidebar

    // Sélection sur la carte
    startNode: null,
    targetNode: null,
};
