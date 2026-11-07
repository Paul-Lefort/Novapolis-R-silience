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
    if not nodes: raise ValueError("Le graphe est vide.")
    start=graph.get("start",nodes[0])
    if start not in adj: raise ValueError("Sommet de départ inconnu.")
    visited={start}; chosen=[]; total=0; steps=[]
    steps.append(event("start",f"Départ depuis {start}",
        "L'arbre couvrant commence avec le seul sommet de départ.",
        current_node=start,visited=list(visited),selected_edges=[],active_edge=None,total_weight=0))
    while len(visited)<len(nodes):
        candidates=[]
        for u in visited:
            for v,eid,w in adj[u]:
                if v not in visited: candidates.append((w,str(eid),u,v,eid))
        if not candidates:
            steps.append(event("disconnected","Graphe non connexe",
                "Aucune arête ne relie l'arbre courant aux sommets restants. Un arbre couvrant unique n'existe pas.",
                visited=list(visited),selected_edges=chosen.copy(),active_edge=None,total_weight=total))
            break
        w,_,u,v,eid=min(candidates)
        chosen.append(eid); total+=w; visited.add(v)
        steps.append(event("select_edge",f"Ajout de {u} — {v}",
            f"Parmi les arêtes reliant l'arbre aux sommets non visités, celle-ci a le poids minimal ({w:g}). On l'ajoute.",
            current_node=v,candidate_node=v,active_edge=eid,visited=list(visited),
            selected_edges=chosen.copy(),total_weight=total))
    return make_response(graph,steps,{"selected_edges":chosen,"total_weight":total,
        "is_spanning_tree":len(chosen)==max(0,len(nodes)-1)})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - prim", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "prim"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
