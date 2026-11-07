import math

def prepare_graph(graph):
    if not isinstance(graph, dict):
        raise ValueError("Le graphe doit être un objet JSON.")
    if graph.get("directed", False):
        raise ValueError("Novapolis accepte uniquement les graphes non orientés.")
    nodes = list(dict.fromkeys(graph.get("nodes") or []))
    if len(nodes) < 1:
        raise ValueError("Le graphe doit contenir au moins un sommet.")
    raw_edges = graph.get("edges") or []
    adjacency = {node: [] for node in nodes}
    edges = []
    seen_ids = set()
    for index, edge in enumerate(raw_edges):
        u, v = edge.get("source"), edge.get("target")
        if u not in adjacency or v not in adjacency:
            raise ValueError(f"L'arête {index} référence un sommet absent du graphe.")
        if u == v:
            # Les boucles sont admises dans la structure, mais n'aident pas les parcours/MST.
            pass
        if "weight" not in edge or edge["weight"] is None:
            raise ValueError(f"Le poids de l'arête {index} est obligatoire.")
        try:
            weight = float(edge["weight"])
        except (TypeError, ValueError):
            raise ValueError(f"Poids invalide pour l'arête {index}.")
        if not math.isfinite(weight):
            raise ValueError(f"Le poids de l'arête {index} doit être fini.")
        eid = str(edge.get("id", f"e{index}"))
        if eid in seen_ids:
            raise ValueError(f"Identifiant d'arête dupliqué : {eid}")
        seen_ids.add(eid)
        item = {"id": eid, "source": u, "target": v, "weight": weight}
        edges.append(item)
        adjacency[u].append((v, eid, weight))
        adjacency[v].append((u, eid, weight))
    return nodes, adjacency, edges

def event(kind, title, explanation, **state):
    return {"type": kind, "title": title, "explanation": explanation, **state}

def make_response(graph, steps, result):
    # Chaque événement décrit un état cumulatif, directement exploitable par le frontend.
    normalized_steps = []
    for index, step in enumerate(steps):
        normalized_steps.append({"index": index, **step})
    return {
        "graph": graph,
        "steps": normalized_steps,
        "step_count": len(normalized_steps),
        "result": result
    }

def edge_map(edges):
    return {e["id"]: e for e in edges}


import math

def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj: raise ValueError("Indiquez un sommet de départ existant dans 'start'.")
    if any(e["weight"] < 0 for e in edges):
        raise ValueError("Dijkstra exige des poids positifs ou nuls.")
    dist = {n: math.inf for n in nodes}; prev = {n: None for n in nodes}
    dist[start] = 0; settled = set(); selected_edges = []; steps = []
    steps.append(event("initialize", "Initialisation des distances",
        f"La distance de {start} vaut 0 ; toutes les autres distances valent l'infini.",
        current_node=start, distances={n: (0 if n == start else None) for n in nodes},
        predecessors=prev.copy(), settled=[], selected_edges=[], active_edge=None))
    while len(settled) < len(nodes):
        candidates = [n for n in nodes if n not in settled]
        u = min(candidates, key=lambda n: dist[n])
        if dist[u] == math.inf: break
        settled.add(u)
        steps.append(event("settle", f"Sommet {u} fixé",
            f"{u} possède la plus petite distance provisoire ({dist[u]:g}) parmi les sommets non fixés. Sa distance devient définitive.",
            current_node=u, distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
            predecessors=prev.copy(), settled=list(settled), selected_edges=selected_edges.copy(),
            active_edge=None))
        for v, eid, w in adj[u]:
            if v in settled: continue
            alt = dist[u] + w
            if alt < dist[v]:
                old = dist[v]; dist[v] = alt; prev[v] = u; selected_edges.append(eid)
                steps.append(event("relax", f"Amélioration de la distance de {v}",
                    f"En passant par {u}, on obtient {dist[u]:g} + {w:g} = {alt:g}, meilleur que {old if math.isfinite(old) else '∞'}. Le prédécesseur de {v} devient {u}.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
                    predecessors=prev.copy(), settled=list(settled), selected_edges=selected_edges.copy()))
            else:
                steps.append(event("no_improvement", f"Pas d'amélioration pour {v}",
                    f"Le trajet via {u} donne {alt:g}, ce qui ne bat pas la distance actuelle de {v}.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
                    predecessors=prev.copy(), settled=list(settled), selected_edges=selected_edges.copy()))
    paths = {}
    for target in nodes:
        path=[]; cur=target
        while cur is not None:
            path.append(cur); cur=prev[cur]
        paths[target] = list(reversed(path)) if dist[target] < math.inf else []
    return make_response(graph, steps, {"distances":{n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
        "predecessors":prev, "paths":paths})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - dijkstra", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "dijkstra"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
