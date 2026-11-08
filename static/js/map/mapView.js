// map/mapView.js - Initialisation de la carte et rendu du graphe (arcs, flèches, sommets, légende)

import { state } from '../state.js';
import { CASERNE_COLOR, MAP_DEFAULTS, NODE_COLORS } from '../config.js';
import { $, escapeHtml } from '../utils.js';

const ARROW_COLOR = '#ff5722';
const ARROW_HIDE_THRESHOLD = 400; // au-delà, on masque les flèches en dézoomant
const HOUSE_SVG = '<svg viewBox="0 0 24 24" fill="#fff"><path d="M12 3 2 12h3v8h5v-5h4v5h5v-8h3z"/></svg>';

let legendEl = null;
let legendView = 'routier';
let legendUnreachable = false;
let onNodeClick = () => {};

export function initMap(nodeClickHandler) {
    onNodeClick = nodeClickHandler;

    const map = L.map('network-container', {
        preferCanvas: true,
        attributionControl: false,
        minZoom: 3,
        maxZoom: 19,
        zoomSnap: 0.25,
    }).setView(MAP_DEFAULTS.center, MAP_DEFAULTS.zoom);

    state.map = map;
    for (const name of ['edges', 'arrows', 'nodes', 'casernes', 'path', 'unreachable']) {
        state.layers[name] = L.layerGroup().addTo(map);
    }

    map.on('zoomend', drawArrows);

    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = () => {
        legendEl = L.DomUtil.create('div', 'legend');
        return legendEl;
    };
    legend.addTo(map);
}

// ---------- Styles ----------

function edgeStyle(kind, statut) {
    let color = NODE_COLORS[kind], weight = 3, dashArray = null;
    if (kind === 'routier') {
        if (statut === 'saturé') { color = '#ea4335'; weight = 4; }
        else if (statut === 'travaux') { color = '#f9ab00'; dashArray = '6, 6'; }
    } else {
        weight = 2.5;
        if (statut === 'en_maintenance') { color = '#f9ab00'; dashArray = '6, 6'; }
        else if (statut === 'deploiement') { color = '#9aa0a6'; dashArray = '2, 6'; }
    }
    return { color, weight, dashArray, opacity: 0.8 };
}

const kmLine = (row) => (row.distance_km != null ? `${escapeHtml(row.distance_km)} km<br>` : '');

const TOOLTIPS = {
    routier: (r) =>
        `<b>Route ${escapeHtml(r.u)} ➔ ${escapeHtml(r.v)}</b><br>${kmLine(r)}` +
        `Normal : ${escapeHtml(r.temps_normal)} min<br>Pointe : ${escapeHtml(r.temps_pointe)} min<br>` +
        `Statut : ${escapeHtml(r.statut)}`,
    fibre: (r) =>
        `<b>Fibre entre ${escapeHtml(r.u)} et ${escapeHtml(r.v)}</b><br>${kmLine(r)}` +
        `Coût : ${escapeHtml(r.cost)} k€<br>Statut : ${escapeHtml(r.statut)}`,
};

// ---------- Index des positions ----------

function buildPositions() {
    state.positions = new Map();
    const bounds = [];
    for (const site of state.sites) {
        const lat = site.latitude ?? site.lat;
        const lon = site.longitude ?? site.lon ?? site.x;
        if (lat == null || lon == null) continue;
        state.positions.set(String(site.id), [lat, lon]);
        bounds.push([lat, lon]);
    }
    return bounds;
}

// ---------- Arcs ----------

/** Dessine les arcs d'un type ; renvoie le nombre d'arcs effectivement tracés. */
function drawEdges(rows, kind) {
    const directed = kind === 'routier';
    const existing = directed ? new Set(rows.map((r) => `${r.u}_${r.v}`)) : null;
    let count = 0;

    for (const row of rows) {
        const from = state.positions.get(String(row.u));
        const to = state.positions.get(String(row.v));
        if (!from || !to) continue;
        count++;

        const style = edgeStyle(kind, row.statut);
        const line = L.polyline([from, to], style)
            .bindTooltip(TOOLTIPS[kind](row), { direction: 'top', sticky: true });
        line.on('mouseover', () => line.setStyle({ weight: style.weight + 2, opacity: 1 }));
        line.on('mouseout', () => line.setStyle(style));
        state.layers.edges.addLayer(line);

        // Flèche uniquement si l'arc n'a pas de sens inverse
        if (directed && !existing.has(`${row.v}_${row.u}`)) {
            state.arrows.push({ from, to });
        }
    }
    return count;
}

function drawArrows() {
    const { map, arrows, layers } = state;
    layers.arrows.clearLayers();
    if (arrows.length === 0) return;
    if (arrows.length > ARROW_HIDE_THRESHOLD && map.getZoom() < 12) return;

    const zoom = map.getZoom();
    for (const { from, to } of arrows) {
        const p1 = map.project(from, zoom), p2 = map.project(to, zoom);
        const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI;

        layers.arrows.addLayer(L.marker([(from[0] + to[0]) / 2, (from[1] + to[1]) / 2], {
            interactive: false,
            icon: L.divIcon({
                className: 'arrow-icon',
                iconSize: [18, 18],
                iconAnchor: [9, 9],
                html: `<div class="arrow-glyph" style="transform:rotate(${angle}deg);color:${ARROW_COLOR}">▶</div>`,
            }),
        }));
    }
}

// ---------- Légende ----------

export function setLegendUnreachable(visible) {
    legendUnreachable = visible;
    updateLegend();
}

function updateLegend(view = legendView) {
    legendView = view;
    if (!legendEl) return;

    const line = (color, label, dashed = false) =>
        `<div><i style="border-color:${color};${dashed ? 'border-top-style:dashed;' : ''}"></i>${label}</div>`;
    const dot = (cls, label) => `<div><span class="legend-dot ${cls}"></span>${label}</div>`;

    let html = '';
    if (view !== 'fibre') {
        html += line('#4285F4', 'Route ouverte') + line('#ea4335', 'Route saturée') + line('#f9ab00', 'Travaux / maintenance', true);
    }
    if (view !== 'routier') {
        html += line('#0b8043', 'Fibre active') + line('#9aa0a6', 'Fibre en déploiement', true);
    }
    html += dot('caserne', 'Caserne');
    if (legendUnreachable) html += dot('unreachable', 'Non atteignable par les pompiers');
    legendEl.innerHTML = html + '<div class="legend-note">▶ sens de la liaison</div>';
}

// ---------- Rendu complet ----------

export function renderGraph(view, { fit = false } = {}) {
    state.view = view;
    const { layers } = state;
    for (const name of ['edges', 'nodes', 'casernes', 'path', 'unreachable']) layers[name].clearLayers();
    legendUnreachable = false;
    state.arrows = [];
    state.markers = new Map();

    const bounds = buildPositions();

    let nbEdges = 0;
    if (view !== 'fibre') nbEdges += drawEdges(state.routes, 'routier');
    if (view !== 'routier') nbEdges += drawEdges(state.fibre, 'fibre');

    const nodeColor = NODE_COLORS[view === 'fibre' ? 'fibre' : 'routier'];
    for (const site of state.sites) {
        const pos = state.positions.get(String(site.id));
        if (!pos) continue;

        const isCaserne = String(site.type ?? '').toLowerCase() === 'caserne';
        const baseStyle = isCaserne
            ? { radius: 11, fillColor: CASERNE_COLOR, color: '#fff', weight: 3, fillOpacity: 1 }
            : { radius: 6, fillColor: nodeColor, color: '#fff', weight: 1.5, fillOpacity: 1 };

        const marker = L.circleMarker(pos, baseStyle)
            .bindTooltip(
                `<b>${escapeHtml(site.nom || 'Site ' + site.id)}</b><br>${escapeHtml(site.type)}<br>ID : ${escapeHtml(site.id)}`,
                { direction: 'top', sticky: true })
            .on('click', () => onNodeClick(site.id))
            .addTo(layers.nodes);

        marker.baseStyle = baseStyle; // style de repos, restauré après sélection
        state.markers.set(String(site.id), marker);

        if (isCaserne) {
            L.marker(pos, {
                interactive: false,
                keyboard: false,
                icon: L.divIcon({ className: 'caserne-glyph', iconSize: [22, 22], iconAnchor: [11, 11], html: HOUSE_SVG }),
            }).addTo(layers.casernes);
        }
    }

    drawArrows();
    updateLegend(view);

    if (fit && bounds.length > 0) state.map.fitBounds(bounds, { padding: [30, 30] });

    const summary = $('graph-summary');
    if (summary) summary.textContent = `${state.sites.length} sites & ${nbEdges} connexions`;
}
