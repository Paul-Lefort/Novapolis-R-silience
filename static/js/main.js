// main.js - Point d'entrée principal de l'application

let map = null;
let edgeLayer = null, arrowLayer = null, nodeLayer = null, legendEl = null;
let sitesData = [], routesData = [], fibreData = [];
let arrowData = [];
let currentView = 'routier';

function setLoadingMessage(msg, isError = false) {
    const el = document.getElementById('loading-msg');
    if (el) {
        el.innerText = msg;
        if (isError) el.style.color = '#d93025';
    }
}

function openModal() {
    document.getElementById('generate-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('generate-modal').classList.remove('active');
}

function switchView(type) {
    ['routier', 'fibre', 'both'].forEach(t => {
        const btn = document.getElementById(t === 'both' ? 'btn-both' : 'btn-' + t);
        if (btn) btn.classList.toggle('active', t === type);
    });
    renderGraph(type);
}

window.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadNetworkData();
});