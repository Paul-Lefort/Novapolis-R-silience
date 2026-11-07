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


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")
    visited, order, explored, steps = set(), [], [], []
    steps.append(event("start", f"Départ depuis {start}",
        f"On initialise le parcours en profondeur (DFS) au sommet {start}.",
        current_node=start, visited=[], explored_edges=[], active_edge=None,
        traversal_order=[]))
    def visit(u):
        visited.add(u); order.append(u)
        steps.append(event("visit", f"Visite du sommet {u}",
            f"Le sommet {u} est marqué comme visité et ajouté à l'ordre du parcours.",
            current_node=u, visited=list(order), explored_edges=explored.copy(),
            active_edge=None, traversal_order=order.copy()))
        for v, eid, weight in adj[u]:
            if v not in visited:
                steps.append(event("inspect_edge", f"Examen de l'arête {u} — {v}",
                    f"On examine l'arête de poids {weight:g}. Le sommet {v} n'a pas encore été visité : on descend dans cette branche.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    visited=list(order), explored_edges=explored.copy(),
                    traversal_order=order.copy()))
                explored.append(eid)
                visit(v)
            else:
                steps.append(event("skip_edge", f"Arête vers {v} ignorée",
                    f"Le sommet {v} est déjà visité ; DFS ne le revisite pas.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    visited=list(order), explored_edges=explored.copy(),
                    traversal_order=order.copy()))
        steps.append(event("backtrack", f"Retour depuis {u}",
            f"Tous les voisins accessibles depuis {u} ont été examinés. Le parcours revient au sommet précédent.",
            current_node=u, visited=list(order), explored_edges=explored.copy(),
            active_edge=None, traversal_order=order.copy()))
    visit(start)
    return make_response(graph, steps, {"traversal_order": order, "visited": order,
        "unvisited_nodes": [n for n in nodes if n not in visited]})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - dfs", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "dfs"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
