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


from collections import deque

def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")
    queue = deque([start]); visited = {start}; order = []; explored = []; steps = []
    steps.append(event("enqueue", f"{start} ajouté à la file",
        f"On initialise BFS avec {start}. La file contient les sommets à traiter.",
        current_node=start, queue=list(queue), visited=[], explored_edges=[],
        active_edge=None, traversal_order=[]))
    while queue:
        u = queue.popleft(); order.append(u)
        steps.append(event("dequeue_visit", f"Visite de {u}",
            f"{u} est retiré de la file puis marqué comme traité. BFS explore les voisins par niveaux.",
            current_node=u, queue=list(queue), visited=order.copy(),
            explored_edges=explored.copy(), active_edge=None,
            traversal_order=order.copy()))
        for v, eid, weight in adj[u]:
            if v not in visited:
                visited.add(v); queue.append(v); explored.append(eid)
                steps.append(event("discover", f"{v} découvert depuis {u}",
                    f"L'arête {u} — {v} (poids {weight:g}) mène à un sommet inédit. On le marque et on l'ajoute à la fin de la file.",
                    current_node=u, candidate_node=v, queue=list(queue),
                    visited=order.copy(), explored_edges=explored.copy(),
                    active_edge=eid, traversal_order=order.copy()))
            else:
                steps.append(event("skip", f"{v} déjà découvert",
                    f"Le sommet {v} a déjà été découvert ; il n'est pas ajouté une seconde fois à la file.",
                    current_node=u, candidate_node=v, queue=list(queue),
                    visited=order.copy(), explored_edges=explored.copy(),
                    active_edge=eid, traversal_order=order.copy()))
    return make_response(graph, steps, {"traversal_order": order, "visited": order,
        "unvisited_nodes": [n for n in nodes if n not in visited]})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - bfs", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "bfs"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
