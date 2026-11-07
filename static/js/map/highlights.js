// map/highlights.js - Surbrillance des chemins, sommets sélectionnés et sites non atteignables

import { state } from '../state.js';
import { setLegendUnreachable, getCurvedPath } from './mapView.js';

const PATH_STYLE = { color: '#00E676', weight: 6, opacity: 0.95 };

const MARKER_ROLES = {
    start: { fillColor: '#1a73e8', color: '#ffffff', radius: 10, weight: 3 },
    target: { fillColor: '#d93025', color: '#ffffff', radius: 10, weight: 3 },
};

/** Trace une liste de segments [[u, v], ...]. */
export function highlightSegments(pairs) {
    const layer = state.layers.path;
    layer.clearLayers();

    for (const [u, v] of pairs) {
        const from = state.positions.get(String(u));
        const to = state.positions.get(String(v));
        if (!from || !to) continue;

        // Récupère la courbure exacte décidée lors du rendu
        const curvature = state.edgeCurvatures.get(`${state.view}_${u}_${v}`) || 0;
        const pathCoords = curvature === 0 ? [from, to] : getCurvedPath(from, to, curvature);

        layer.addLayer(L.polyline(pathCoords, PATH_STYLE));
    }
}

/** Trace un chemin donné comme suite de sommets [a, b, c, ...]. */
export function highlightPath(nodeIds) {
    if (!nodeIds || nodeIds.length < 2) {
        state.layers.path.clearLayers();
        return;
    }
    highlightSegments(nodeIds.slice(0, -1).map((id, i) => [id, nodeIds[i + 1]]));
}

export function highlightUnreachableNodes(nodeIds) {
    const layer = state.layers.unreachable;
    layer.clearLayers();

    for (const id of nodeIds || []) {
        const pos = state.positions.get(String(id));
        if (!pos) continue;

        L.circleMarker(pos, {
            radius: 11, fillColor: '#EA4335', color: '#ffffff', weight: 3, fillOpacity: 0.95, interactive: false,
        }).addTo(layer);
    }
    setLegendUnreachable(layer.getLayers().length > 0);
}

export function setMarkerRole(nodeId, role) {
    state.markers.get(String(nodeId))?.setStyle(MARKER_ROLES[role]);
}

export function resetMarkers() {
    for (const marker of state.markers.values()) marker.setStyle(marker.baseStyle);
}

export function clearOverlays() {
    state.layers.path?.clearLayers();
    state.layers.unreachable?.clearLayers();
    setLegendUnreachable(false);
}