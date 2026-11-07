(() => {
    "use strict";

    const $ = (id) => document.getElementById(id);
    const state = {
        response: null,
        index: 0,
        timer: null,
        overlay: null,
        edgeById: new Map(),
        nodeById: new Map()
    };

    const algorithmSelect = $("algorithm-select");
    const weightSelect = $("algorithm-weight");
    const startSelect = $("algorithm-start");
    const range = $("algorithm-step-range");

    function stopPlayback() {
        if (state.timer) window.clearInterval(state.timer);
        state.timer = null;
        const play = $("algorithm-play");
        if (play) play.textContent = "▶ Lecture";
    }

    function refreshOptions() {
        const api = window.NovapolisGraph;
        if (!api) return;
        const view = api.getCurrentView();
        const options = view === "fibre"
            ? [["distance_km", "Distance (km)"], ["cost", "Coût (€)"]]
            : view === "routier"
                ? [["distance_km", "Distance (km)"], ["temps_normal", "Temps normal (min)"], ["temps_pointe", "Temps de pointe (min)"]]
                : [["distance_km", "Distance (km)"]];
        const previous = weightSelect.value;
        weightSelect.innerHTML = "";
        options.forEach(([value, label]) => weightSelect.add(new Option(label, value)));
        if (options.some(([value]) => value === previous)) weightSelect.value = previous;

        const sites = api.getSites() || [];
        const previousStart = startSelect.value;
        startSelect.innerHTML = "";
        sites.forEach(site => {
            const id = String(site.id);
            startSelect.add(new Option(`${site.nom || "Site"} (${id})`, id));
        });
        if (sites.some(site => String(site.id) === previousStart)) startSelect.value = previousStart;
    }

    function buildGraph() {
        const api = window.NovapolisGraph;
        const sites = api.getSites() || [];
        const view = api.getCurrentView();
        const rows = [];
        if (view !== "fibre") rows.push(...(api.getRoutes() || []).map((e, i) => ({...e, __kind:"route", __index:i})));
        if (view !== "routier") rows.push(...(api.getFibre() || []).map((e, i) => ({...e, __kind:"fibre", __index:i})));

        const nodes = sites.map(s => String(s.id));
        const nodeSet = new Set(nodes);
        const weightField = weightSelect.value;
        const edges = [];
        const edgeIds = new Set();

        rows.forEach((row, index) => {
            const source = String(row.u);
            const target = String(row.v);
            if (!nodeSet.has(source) || !nodeSet.has(target)) return;
            const rawWeight = row[weightField];
            const weight = Number(rawWeight);
            if (rawWeight === null || rawWeight === undefined || rawWeight === "" || !Number.isFinite(weight)) return;

            let id = `${row.__kind}-${row.id ?? row.__index ?? index}`;
            if (edgeIds.has(id)) id = `${id}-${index}`;
            edgeIds.add(id);
            edges.push({id, source, target, weight});
        });

        if (!nodes.length) throw new Error("Aucun site disponible dans les données chargées.");
        if (!edges.length) throw new Error(`Aucune liaison exploitable avec le poids « ${weightField} » dans cette vue.`);
        const graph = {directed:false, nodes, edges};
        if (startSelect.value) graph.start = startSelect.value;
        return graph;
    }

    async function runAlgorithm() {
        stopPlayback();
        $("algorithm-error").textContent = "";
        $("algorithm-run").disabled = true;
        $("algorithm-run").textContent = "Calcul en cours…";
        try {
            refreshOptions();
            const graph = buildGraph();
            const algorithm = algorithmSelect.value;
            const response = await fetch(`/api/algorithms/${encodeURIComponent(algorithm)}`, {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({graph})
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                const detail = payload.detail || payload.message || `Erreur HTTP ${response.status}`;
                throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
            }
            if (!Array.isArray(payload.steps) || !payload.steps.length) {
                throw new Error("La réponse du serveur ne contient aucune étape.");
            }
            state.response = payload;
            state.index = 0;
            range.disabled = false;
            range.min = "0";
            range.max = String(payload.steps.length - 1);
            range.value = "0";
            $("algorithm-result-json").textContent = JSON.stringify(payload.result, null, 2);
            renderStep();
        } catch (error) {
            console.error("Démonstration :", error);
            $("algorithm-error").textContent = error.message || "Impossible de lancer la démonstration.";
        } finally {
            $("algorithm-run").disabled = false;
            $("algorithm-run").textContent = "Lancer la démonstration";
        }
    }

    function ensureOverlay() {
        if (state.overlay) return state.overlay;
        const map = window.NovapolisGraph.getMap();
        state.overlay = L.layerGroup().addTo(map);
        return state.overlay;
    }

    function clearOverlay() {
        ensureOverlay().clearLayers();
        state.edgeById.clear();
        state.nodeById.clear();
    }

    function sitePositions() {
        const api = window.NovapolisGraph;
        const positions = new Map();
        (api.getSites() || []).forEach(site => {
            const p = api.getPosition(site);
            if (p) positions.set(String(site.id), p);
        });
        return positions;
    }

    function drawAlgorithmOverlay(step) {
        clearOverlay();
        const api = window.NovapolisGraph;
        const positions = sitePositions();
        const allEdges = [];
        if (api.getCurrentView() !== "fibre") allEdges.push(...(api.getRoutes() || []).map((e,i)=>({...e,__kind:"route",__index:i})));
        if (api.getCurrentView() !== "routier") allEdges.push(...(api.getFibre() || []).map((e,i)=>({...e,__kind:"fibre",__index:i})));

        const activeId = step.active_edge == null ? null : String(step.active_edge);
        if (activeId) {
            const edge = allEdges.find((e,i) => `${e.__kind}-${e.id ?? e.__index ?? i}` === activeId);
            if (edge) {
                const a = positions.get(String(edge.u)), b = positions.get(String(edge.v));
                if (a && b) {
                    L.polyline([a,b], {color:"#fbbc04", weight:8, opacity:1, lineCap:"round"})
                        .addTo(state.overlay).bringToFront();
                }
            }
        }

        const visited = step.visited && typeof step.visited === "object" ? step.visited : {};
        Object.entries(visited).forEach(([id, yes]) => {
            if (!yes || !positions.has(String(id))) return;
            L.circleMarker(positions.get(String(id)), {
                radius:8, color:"#fff", weight:2, fillColor:"#34a853", fillOpacity:1
            }).addTo(state.overlay);
        });

        [step.current_node, step.candidate_node].forEach((id, i) => {
            if (id == null || !positions.has(String(id))) return;
            L.circleMarker(positions.get(String(id)), {
                radius:i===0 ? 11 : 9, color:"#fff", weight:2,
                fillColor:i===0 ? "#fbbc04" : "#a142f4", fillOpacity:1
            }).addTo(state.overlay);
        });

        // Pour les arbres couvrants, garder visibles les arêtes déjà sélectionnées.
        const selectedIds = new Set();
        if (state.response && state.response.steps) {
            for (let i=0; i<=state.index; i++) {
                const s = state.response.steps[i];
                if ((s.type === "add_edge") && s.active_edge != null) selectedIds.add(String(s.active_edge));
            }
        }
        selectedIds.forEach(id => {
            const edge = allEdges.find((e,i) => `${e.__kind}-${e.id ?? e.__index ?? i}` === id);
            if (!edge) return;
            const a = positions.get(String(edge.u)), b = positions.get(String(edge.v));
            if (a && b) L.polyline([a,b], {color:"#34a853", weight:6, opacity:.95}).addTo(state.overlay);
        });
    }

    function renderDetails(step) {
        const box = $("algorithm-step-details");
        const parts = [];
        if (step.iteration != null) parts.push(`<div><b>Itération :</b> ${step.iteration}</div>`);
        if (step.queue) parts.push(`<div><b>File BFS :</b> ${step.queue.map(escapeHtml).join(" → ") || "vide"}</div>`);
        if (step.distances) {
            parts.push("<div><b>Distances :</b></div>");
            parts.push("<table><tbody>" + Object.entries(step.distances).map(([k,v]) =>
                `<tr><th>${escapeHtml(k)}</th><td>${v == null ? "∞" : escapeHtml(v)}</td></tr>`
            ).join("") + "</tbody></table>");
        }
        if (step.matrix) {
            parts.push("<div><b>Matrice des distances :</b></div>");
            parts.push("<table><tbody>" + step.matrix.map((row,i) =>
                `<tr><th>${i}</th>${row.map(v=>`<td>${v == null ? "∞" : escapeHtml(v)}</td>`).join("")}</tr>`
            ).join("") + "</tbody></table>");
        }
        if (step.visited) {
            const done = Object.entries(step.visited).filter(([,v])=>v).map(([k])=>k);
            parts.push(`<div><b>Sommets visités :</b> ${done.map(escapeHtml).join(", ") || "aucun"}</div>`);
        }
        if (step.active_edge != null) parts.push(`<div><b>Arête active :</b> ${escapeHtml(step.active_edge)}</div>`);
        box.innerHTML = parts.join("");
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
    }

    function pedagogicalComment(step) {
        const algorithm = algorithmSelect.value;
        const type = step.type;
        const comments = {
            dfs: {
                initialize: "DFS démarre au sommet choisi. Il explore une branche aussi loin que possible avant de revenir en arrière.",
                visit: "Le sommet courant est traité. L'algorithme examine maintenant ses voisins.",
                discover: "Un voisin non visité est découvert : DFS descend dans cette branche. L'arête violette/jaune indique le lien examiné.",
                check: "Ce voisin a déjà été visité : DFS ignore cette liaison pour éviter de revisiter le même sommet.",
                complete: "Toutes les branches accessibles ont été explorées. Le parcours en profondeur est terminé."
            },
            bfs: {
                initialize: "BFS initialise une file FIFO. Les sommets seront explorés dans l'ordre de leur découverte, niveau par niveau.",
                visit: "Le sommet en tête de file est retiré puis exploré. Ses voisins seront ajoutés à la fin de la file.",
                discover: "Le voisin est marqué comme visité dès sa découverte puis ajouté à la file : cela évite de l'ajouter plusieurs fois.",
                check: "Le sommet voisin est déjà connu. BFS ne le remet pas dans la file.",
                complete: "La file est vide : tous les sommets accessibles depuis le départ ont été parcourus."
            },
            dijkstra: {
                initialize: "La distance du sommet de départ vaut zéro. Toutes les autres distances commencent à l'infini.",
                pop: "Dijkstra choisit le sommet dont la distance provisoire est la plus faible. Avec des poids non négatifs, cette distance est définitive.",
                relax: "La distance obtenue en passant par le sommet courant est meilleure : la distance et le prédécesseur sont mis à jour.",
                check: "Le chemin passant par cette arête n'améliore pas la distance connue.",
                complete: "Les plus courts chemins depuis le sommet de départ ont été calculés."
            },
            "bellman-ford": {
                initialize: "Toutes les distances sont initialisées à l'infini, sauf celle du sommet de départ qui vaut zéro.",
                iteration: "Une itération examine les arcs et propage les améliorations de distance. Il faut au plus |V|-1 itérations en l'absence de cycle négatif accessible.",
                check: "L'algorithme teste si le passage par cette arête permet de réduire la distance du sommet cible.",
                relax: "La distance est améliorée. Le prédécesseur est actualisé pour mémoriser le chemin trouvé.",
                skip: "Aucun raccourci n'est trouvé sur cet arc pendant cette itération.",
                early_stop: "Aucune distance n'a changé pendant l'itération : poursuivre ne pourrait rien améliorer.",
                negative_cycle: "Une amélioration reste possible après les itérations normales : un cycle négatif accessible existe.",
                complete: "Aucun cycle négatif accessible n'a été détecté depuis le sommet de départ."
            },
            "floyd-warshall": {
                initialize: "La matrice commence avec zéro sur la diagonale, les poids directs entre voisins et l'infini ailleurs.",
                relax: "L'algorithme compare le chemin direct i → j au chemin i → k → j. La matrice est mise à jour si le passage par k est plus court."
            },
            kruskal: {
                initialize: "Kruskal trie les arêtes par poids croissant. Il va construire une forêt sans créer de cycle.",
                add_edge: "Cette arête relie deux composantes différentes : elle peut être ajoutée sans créer de cycle.",
                skip_edge: "Cette arête relierait deux sommets déjà connectés : l'ajouter créerait un cycle, elle est donc rejetée."
            },
            prim: {
                initialize: "Prim commence par un sommet puis agrandit progressivement l'arbre en choisissant l'arête la moins coûteuse vers un nouveau sommet.",
                add_edge: "Cette arête est la moins coûteuse parmi celles qui relient l'arbre courant à un sommet extérieur. Elle rejoint l'arbre couvrant."
            }
        };
        return (comments[algorithm] && comments[algorithm][type]) || "Observez l'état courant et l'arête mise en évidence. L'explication de l'algorithme précise l'opération effectuée à cette étape.";
    }

    function resolutionRows() {
        if (!state.response) return [];
        return state.response.steps.map((step, index) => ({
            etape: index + 1,
            action: step.title || step.type || "Étape",
            evenement: step.type || "",
            sommet: step.current_node ?? "",
            candidat: step.candidate_node ?? "",
            arete: step.active_edge ?? "",
            iteration: step.iteration ?? "",
            explication: step.explanation || "",
            etat: JSON.stringify({
                distances: step.distances,
                visited: step.visited,
                queue: step.queue,
                matrix: step.matrix,
                parent: step.parent
            }, null, 0)
        }));
    }

    function csvEscape(value) {
        return '"' + String(value ?? "").replace(/"/g, '""') + '"';
    }

    function downloadResolutionCSV() {
        const rows = resolutionRows();
        if (!rows.length) return;
        const columns = Object.keys(rows[0]);
        const csv = [columns.map(csvEscape).join(";"), ...rows.map(row => columns.map(key => csvEscape(row[key])).join(";"))].join("\r\n");
        const blob = new Blob(["\uFEFF" + csv], {type:"text/csv;charset=utf-8;"});
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `novapolis-${algorithmSelect.value}-resolution.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function openResolutionTable() {
        const rows = resolutionRows();
        if (!rows.length) return;
        const tab = window.open("", "_blank");
        if (!tab) {
            $("algorithm-error").textContent = "Le navigateur a bloqué le nouvel onglet. Autorisez les fenêtres contextuelles pour afficher le tableau.";
            return;
        }
        const title = `Résolution ${algorithmSelect.value} — Novapolis`;
        const headers = Object.keys(rows[0]);
        const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
        const table = `<table><thead><tr>${headers.map(h=>`<th>${escape(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(row=>`<tr>${headers.map(h=>`<td>${escape(row[h])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
        tab.document.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><style>body{font:14px Arial,sans-serif;color:#202124;margin:28px}h1{font-size:22px}p{color:#5f6368}.actions{display:flex;gap:8px;margin:18px 0}button{padding:9px 13px;border:1px solid #dadce0;border-radius:7px;background:#f8f9fa;cursor:pointer}table{border-collapse:collapse;width:100%;font-size:12px}th,td{border:1px solid #dadce0;padding:8px;text-align:left;vertical-align:top;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#f1f3f4;position:sticky;top:0}tr:nth-child(even){background:#fafafa}@media print{.actions{display:none}body{margin:8mm}th{position:static}}</style></head><body><h1>${escape(title)}</h1><p>${rows.length} étapes — généré depuis la démonstration exécutée dans Novapolis.</p><div class="actions"><button onclick="window.print()">Imprimer / Enregistrer en PDF</button><button id="csv">Télécharger CSV</button></div>${table}<script>document.getElementById('csv').addEventListener('click',()=>{const a=document.createElement('a');a.href=${JSON.stringify('data:text/csv;charset=utf-8,' + encodeURIComponent('\uFEFF' + [headers.join(';'), ...rows.map(r=>headers.map(h=>csvEscape(r[h])).join(';'))].join('\r\n')))};a.download=${JSON.stringify(`novapolis-${algorithmSelect.value}-resolution.csv`)};a.click()})</script></body></html>`);
        tab.document.close();
    }

    function renderStep() {
        if (!state.response) return;
        const steps = state.response.steps;
        const step = steps[state.index];
        $("algorithm-step-title").textContent = step.title || step.type || "Étape";
        $("algorithm-step-count").textContent = `${state.index + 1} / ${steps.length}`;
        $("algorithm-step-explanation").textContent = step.explanation || "Aucune explication disponible.";
        const comment = $("algorithm-step-comment");
        if (comment) comment.innerHTML = `<strong>À comprendre</strong><span>${escapeHtml(pedagogicalComment(step))}</span>`;
        $("algorithm-open-table").disabled = false;
        $("algorithm-export-csv").disabled = false;
        range.value = String(state.index);
        $("algorithm-first").disabled = state.index === 0;
        $("algorithm-prev").disabled = state.index === 0;
        $("algorithm-next").disabled = state.index >= steps.length - 1;
        $("algorithm-last").disabled = state.index >= steps.length - 1;
        renderDetails(step);
        drawAlgorithmOverlay(step);
        if (state.index >= steps.length - 1) stopPlayback();
    }

    function goTo(index) {
        if (!state.response) return;
        state.index = Math.max(0, Math.min(state.response.steps.length - 1, index));
        renderStep();
    }

    function togglePlayback() {
        if (!state.response) return;
        if (state.timer) { stopPlayback(); return; }
        if (state.index >= state.response.steps.length - 1) goTo(0);
        $("algorithm-play").textContent = "Ⅱ Pause";
        state.timer = window.setInterval(() => {
            if (!state.response || state.index >= state.response.steps.length - 1) {
                stopPlayback();
                return;
            }
            goTo(state.index + 1);
        }, 850);
    }

    function init() {
        if (!algorithmSelect) return;
        $("algorithm-run").addEventListener("click", runAlgorithm);
        $("algorithm-open-table").addEventListener("click", openResolutionTable);
        $("algorithm-export-csv").addEventListener("click", downloadResolutionCSV);
        algorithmSelect.addEventListener("change", () => {
            const needsStart = !["kruskal","floyd-warshall"].includes(algorithmSelect.value);
            startSelect.disabled = !needsStart;
            if (state.response) { stopPlayback(); $("algorithm-open-table").disabled = true; $("algorithm-export-csv").disabled = true; }
        });
        weightSelect.addEventListener("change", () => { if (state.response) stopPlayback(); });
        range.addEventListener("input", () => { stopPlayback(); goTo(Number(range.value)); });
        $("algorithm-first").addEventListener("click", () => { stopPlayback(); goTo(0); });
        $("algorithm-prev").addEventListener("click", () => { stopPlayback(); goTo(state.index - 1); });
        $("algorithm-next").addEventListener("click", () => { stopPlayback(); goTo(state.index + 1); });
        $("algorithm-last").addEventListener("click", () => { stopPlayback(); goTo(state.response ? state.response.steps.length - 1 : 0); });
        $("algorithm-play").addEventListener("click", togglePlayback);
        refreshOptions();
        startSelect.disabled = ["kruskal","floyd-warshall"].includes(algorithmSelect.value);
        $("algorithm-open-table").disabled = true;
        $("algorithm-export-csv").disabled = true;
        window.addEventListener("resize", () => {
            if (state.overlay && state.response) drawAlgorithmOverlay(state.response.steps[state.index]);
        });
    }

    window.AlgorithmDemo = {refreshOptions, run:runAlgorithm};
    window.addEventListener("DOMContentLoaded", init);
})();
