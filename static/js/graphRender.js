// graphRender.js - Gestion de la carte Leaflet, des styles et du rendu des graphes

const STYLES = {
    routier: { base: '#4285F4', label: 'Route' },
    fibre:   { base: '#0b8043', label: 'Fibre' }
};

let nodeMarkers = {};
let pathLayer = null;
let unreachableLayer = null;

function initMap() {
    map = L.map('network-container', {
        preferCanvas: true,
        attributionControl: false,
        minZoom: 3,
        maxZoom: 19,
        zoomSnap: 0.25
    }).setView([48.8566, 2.3522], 10);

    edgeLayer = L.layerGroup().addTo(map);
    arrowLayer = L.layerGroup().addTo(map);
    nodeLayer = L.layerGroup().addTo(map);
    pathLayer = L.layerGroup().addTo(map);
    unreachableLayer = L.layerGroup().addTo(map);

    map.on('zoomend', drawArrows);

    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = () => {
        legendEl = L.DomUtil.create('div', 'legend');
        return legendEl;
    };
    legend.addTo(map);
}

function edgeStyle(kind, statut) {
    let color = STYLES[kind].base, weight = 3, dash = null, opacity = 0.8;
    if (kind === 'routier') {
        if (statut === 'saturé') { color = '#ea4335'; weight = 4; }
        else if (statut === 'travaux') { color = '#f9ab00'; dash = '6, 6'; }
    } else {
        weight = 2.5;
        if (statut === 'en_maintenance') { color = '#f9ab00'; dash = '6, 6'; }
        else if (statut === 'deploiement') { color = '#9aa0a6'; dash = '2, 6'; }
    }
    return { color, weight, dashArray: dash, opacity };
}

function drawRouteEdges(rows, sitesMap) {
    let count = 0;
    const directedEdges = new Set(rows.map(r => `${String(r.u)}_${String(r.v)}`));

    rows.forEach(row => {
        const posU = sitesMap.get(row.u) || sitesMap.get(Number(row.u)) || sitesMap.get(String(row.u));
        const posV = sitesMap.get(row.v) || sitesMap.get(Number(row.v)) || sitesMap.get(String(row.v));
        if (!posU || !posV) return;
        count++;

        const style = edgeStyle('routier', row.statut);
        const line = L.polyline([posU, posV], style);

        const km = row.distance_km != null ? `${row.distance_km} km<br>` : '';
        line.bindPopup(`<b>Route ${row.u} ➔ ${row.v}</b><br>${km}Normal : ${row.temps_normal} min<br>Pointe : ${row.temps_pointe} min<br>Statut : ${row.statut}`);

        line.on('mouseover', () => line.setStyle({ weight: style.weight + 2, opacity: 1 }));
        line.on('mouseout', () => line.setStyle(style));
        edgeLayer.addLayer(line);

        const hasReverse = directedEdges.has(`${String(row.v)}_${String(row.u)}`);
        if (!hasReverse) {
            arrowData.push({ from: posU, to: posV, color: style.color });
        }
    });
    return count;
}

function drawFibreEdges(rows, sitesMap) {
    let count = 0;
    rows.forEach(row => {
        const posU = sitesMap.get(row.u) || sitesMap.get(Number(row.u)) || sitesMap.get(String(row.u));
        const posV = sitesMap.get(row.v) || sitesMap.get(Number(row.v)) || sitesMap.get(String(row.v));
        if (!posU || !posV) return;
        count++;

        const style = edgeStyle('fibre', row.statut);
        const line = L.polyline([posU, posV], style);

        const km = row.distance_km != null ? `${row.distance_km} km<br>` : '';
        line.bindPopup(`<b>Fibre entre ${row.u} et ${row.v}</b><br>${km}Coût : ${row.cost} k€<br>Statut : ${row.statut}`);

        line.on('mouseover', () => line.setStyle({ weight: style.weight + 2, opacity: 1 }));
        line.on('mouseout', () => line.setStyle(style));
        edgeLayer.addLayer(line);
    });
    return count;
}

function drawArrows() {
    arrowLayer.clearLayers();
    if (arrowData.length === 0) return;
    if (arrowData.length > 400 && map.getZoom() < 12) return;

    arrowData.forEach(a => {
        const midLat = (a.from[0] + a.to[0]) / 2;
        const midLon = (a.from[1] + a.to[1]) / 2;

        const p1 = map.project(a.from, map.getZoom()), p2 = map.project(a.to, map.getZoom());
        const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI;

        const arrowColor = '#ff5722';

        arrowLayer.addLayer(L.marker([midLat, midLon], {
            interactive: false,
            icon: L.divIcon({
                className: 'arrow-icon',
                iconSize: [18, 18],
                iconAnchor: [9, 9],
                html: `<div style="transform:rotate(${angle}deg); color:${arrowColor}; font-size:14px; font-weight:900; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff, 0px 0px 4px rgba(0,0,0,0.5); text-align:center;">▶</div>`
            })
        }));
    });
}

function updateLegend(type) {
    if (!legendEl) return;
    const item = (c, label, dash) =>
        `<div><i style="border-color:${c};${dash ? 'border-top-style:dashed;' : ''}"></i>${label}</div>`;
    let html = '';
    if (type !== 'fibre') html += item('#4285F4', 'Route ouverte') + item('#ea4335', 'Route saturée') + item('#f9ab00', 'Travaux / maintenance', true);
    if (type !== 'routier') html += item('#0b8043', 'Fibre active') + item('#9aa0a6', 'Fibre en déploiement', true);
    legendEl.innerHTML = html + '<div style="color:#80868b">▶ sens de la liaison</div>';
}

function renderGraph(type, fit = false) {
    currentView = type;
    edgeLayer.clearLayers();
    nodeLayer.clearLayers();
    if (pathLayer) pathLayer.clearLayers();
    if (unreachableLayer) unreachableLayer.clearLayers();
    arrowData = [];
    nodeMarkers = {};

    const sitesMap = new Map();
    const bounds = [];
    sitesData.forEach(site => {
        const lat = site.latitude ?? site.lat;
        const lon = site.longitude ?? site.lon ?? site.x;
        if (lat == null || lon == null) return;
        sitesMap.set(site.id, [lat, lon]);
        sitesMap.set(String(site.id), [lat, lon]);
        sitesMap.set(Number(site.id), [lat, lon]);
        bounds.push([lat, lon]);
    });

    let nbEdges = 0;
    if (type !== 'fibre') nbEdges += drawRouteEdges(routesData, sitesMap);
    if (type !== 'routier') nbEdges += drawFibreEdges(fibreData, sitesMap);

    const nodeColor = type === 'fibre' ? STYLES.fibre.base : STYLES.routier.base;
    sitesData.forEach(site => {
        const pos = sitesMap.get(site.id);
        if (!pos) return;

        let marker = L.circleMarker(pos, {
            radius: 6, fillColor: nodeColor, color: '#fff', weight: 1.5, fillOpacity: 1
        });

        marker.bindPopup(`<b>${site.nom || 'Site ' + site.id}</b><br>${site.type || ''}<br>ID : ${site.id}`);

        marker.on('click', () => {
            if (typeof handleNodeClick === 'function') {
                handleNodeClick(site.id);
            }
        });

        nodeMarkers[site.id] = marker;
        nodeMarkers[String(site.id)] = marker;
        nodeMarkers[Number(site.id)] = marker;
        marker.addTo(nodeLayer);
    });

    drawArrows();
    updateLegend(type);

    if (fit && bounds.length > 0) map.fitBounds(bounds, { padding: [30, 30] });

    const stats = document.getElementById('stats-info');
    if (stats) stats.innerText = `${sitesData.length} sites & ${nbEdges} connexions`;
}

function highlightPath(pathNodeIds) {
    if (!pathLayer) {
        pathLayer = L.layerGroup().addTo(map);
    }
    pathLayer.clearLayers();

    if (!pathNodeIds || pathNodeIds.length < 2) return;

    const sitesMap = new Map();
    sitesData.forEach(site => {
        const lat = site.latitude ?? site.lat;
        const lon = site.longitude ?? site.lon ?? site.x;
        if (lat != null && lon != null) {
            sitesMap.set(site.id, [lat, lon]);
            sitesMap.set(String(site.id), [lat, lon]);
            sitesMap.set(Number(site.id), [lat, lon]);
        }
    });

    for (let i = 0; i < pathNodeIds.length - 1; i++) {
        const u = pathNodeIds[i];
        const v = pathNodeIds[i + 1];

        const posU = sitesMap.get(u) || sitesMap.get(String(u)) || sitesMap.get(Number(u));
        const posV = sitesMap.get(v) || sitesMap.get(String(v)) || sitesMap.get(Number(v));

        if (posU && posV) {
            const pathLine = L.polyline([posU, posV], {
                color: '#00E676',
                weight: 6,
                opacity: 0.95
            });
            pathLayer.addLayer(pathLine);
        }
    }
}

// Surlignage en ROUGE des nœuds non atteignables
function highlightUnreachableNodes(nodeIds) {
    if (!unreachableLayer) {
        unreachableLayer = L.layerGroup().addTo(map);
    }
    unreachableLayer.clearLayers();

    if (!nodeIds || nodeIds.length === 0) return;

    const sitesMap = new Map();
    sitesData.forEach(site => {
        const lat = site.latitude ?? site.lat;
        const lon = site.longitude ?? site.lon ?? site.x;
        if (lat != null && lon != null) {
            sitesMap.set(site.id, [lat, lon]);
            sitesMap.set(String(site.id), [lat, lon]);
            sitesMap.set(Number(site.id), [lat, lon]);
        }
    });

    nodeIds.forEach(id => {
        const pos = sitesMap.get(id) || sitesMap.get(String(id)) || sitesMap.get(Number(id));
        if (pos) {
            const alertMarker = L.circleMarker(pos, {
                radius: 11,
                fillColor: '#EA4335',
                color: '#ffffff',
                weight: 3,
                fillOpacity: 0.95
            });

            alertMarker.bindTooltip(`⚠️ Non atteignable : ID ${id}`, {
                permanent: true,
                direction: 'top'
            });

            unreachableLayer.addLayer(alertMarker);
        }
    });
}

function updateMarkerVisual(nodeId, type) {
    const marker = nodeMarkers[nodeId] || nodeMarkers[String(nodeId)] || nodeMarkers[Number(nodeId)];
    if (!marker) return;

    if (type === 'car') {
        marker.setStyle({
            fillColor: '#1a73e8',
            color: '#ffffff',
            radius: 10,
            weight: 3
        });
        marker.bindTooltip("🚗 Départ", { permanent: true, direction: "top" }).openTooltip();
    } else if (type === 'flag') {
        marker.setStyle({
            fillColor: '#d93025',
            color: '#ffffff',
            radius: 10,
            weight: 3
        });
        marker.bindTooltip("🏁 Arrivée", { permanent: true, direction: "top" }).openTooltip();
    }
}

function resetMarkersVisual() {
    const defaultColor = currentView === 'fibre' ? STYLES.fibre.base : STYLES.routier.base;
    Object.keys(nodeMarkers).forEach(nodeId => {
        const marker = nodeMarkers[nodeId];
        if (marker) {
            marker.setStyle({
                fillColor: defaultColor,
                color: '#fff',
                radius: 6,
                weight: 1.5
            });
            marker.unbindTooltip();
        }
    });
    if (pathLayer) pathLayer.clearLayers();
    if (unreachableLayer) unreachableLayer.clearLayers();
}