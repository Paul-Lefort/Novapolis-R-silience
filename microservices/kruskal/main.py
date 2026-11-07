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
    parent={n:n for n in nodes}; rank={n:0 for n in nodes}
    def find(x):
        if parent[x]!=x: parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra==rb: return False
        if rank[ra]<rank[rb]: ra,rb=rb,ra
        parent[rb]=ra
        if rank[ra]==rank[rb]: rank[ra]+=1
        return True
    chosen=[]; total=0; steps=[]
    ordered=sorted(edges,key=lambda e:(e["weight"],e["id"]))
    steps.append(event("initialize","Tri des arêtes",
        "Kruskal trie toutes les arêtes par poids croissant avant de les examiner.",
        selected_edges=[],active_edge=None,total_weight=0,sorted_edges=[e["id"] for e in ordered]))
    for e in ordered:
        ok=union(e["source"],e["target"])
        if ok: chosen.append(e["id"]); total+=e["weight"]
        steps.append(event("accept" if ok else "reject",
            f"Arête {e['source']} — {e['target']} {'retenue' if ok else 'rejetée'}",
            f"Poids {e['weight']:g}. " + ("Elle relie deux composantes différentes : on l'ajoute à l'arbre." if ok else "Ses extrémités sont déjà reliées : l'ajouter créerait un cycle."),
            current_edge=e["id"],active_edge=e["id"],selected_edges=chosen.copy(),
            total_weight=total,components={n:find(n) for n in nodes}))
    return make_response(graph,steps,{"selected_edges":chosen,"total_weight":total,
        "is_spanning_tree":len(chosen)==max(0,len(nodes)-1)})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - kruskal", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "kruskal"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
