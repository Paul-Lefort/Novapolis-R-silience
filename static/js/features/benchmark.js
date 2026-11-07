// features/benchmark.js - Module d'exécution des benchmarks intégrés
import { state } from '../state.js';
import { $, escapeHtml } from '../utils.js';
import { showOverlay, hideOverlay } from '../ui/overlay.js';

export async function runPlatformBenchmark() {
    const container = $('benchmark-results');
    if (!container) return;

    showOverlay("Suspension de l'affichage... Mesure des algorithmes en cours...");
    container.textContent = "Exécution des benchmarks en cours...";

    try {
        const res = await fetch(`/api/benchmark/run?view=${state.view}`);
        if (!res.ok) throw new Error("Erreur lors de l'exécution du benchmark");

        const json = await res.json();
        const data = json.result;

        if (data.error) {
            container.innerHTML = `<span class="error-text">${escapeHtml(data.error)}</span>`;
            return;
        }

        const metrics = data.metrics;
        let rowsHtml = '';
        for (const [algo, timeMs] of Object.entries(metrics)) {
            const val = timeMs !== null ? `${timeMs} ms` : 'Exclu (trop grand, O(V^3))';
            rowsHtml += `<tr><td><b>${escapeHtml(algo)}</b></td><td style="text-align:right;">${escapeHtml(val)}</td></tr>`;
        }

        container.innerHTML = `
            <div class="card stack text-sm mt-md" style="background: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #dadce0;">
                <b class="text-blue">Rapport de Performance</b>
                <p style="margin: 4px 0;">Sommets analysés ($V$) : <b>${data.node_count}</b></p>
                <p style="margin: 4px 0;">Arêtes analysées ($E$) : <b>${data.edge_count}</b></p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 8px;">
                    ${rowsHtml}
                </table>
                <div class="alert alert-ok mt-sm" style="font-size: 11px;">
                    Mesures réalisées sur 5 répétitions (graine fixe, affichage Leaflet mis en pause).
                </div>
            </div>
        `;
    } catch (error) {
        console.error(error);
        container.innerHTML = `<span class="error-text">Erreur : ${escapeHtml(error.message)}</span>`;
    } finally {
        hideOverlay();
    }
}