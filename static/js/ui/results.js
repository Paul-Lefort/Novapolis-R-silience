// ui/results.js - Remise à zéro des zones de résultats (rapport, intervention, fibre)

import { clearOverlays } from '../map/highlights.js';

/** À appeler quand le réseau ou la vue change : les anciens résultats ne sont plus valables. */
export function clearResults() {
    document.querySelectorAll('.results').forEach((el) => {
        el.textContent = el.dataset.placeholder ?? '';
    });
    clearOverlays();
}
