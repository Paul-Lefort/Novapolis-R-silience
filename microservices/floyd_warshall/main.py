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
    d={u:{v:(0 if u==v else math.inf) for v in nodes} for u in nodes}
    nxt={u:{v:None for v in nodes} for u in nodes}
    for e in edges:
        u,v,w=e["source"],e["target"],e["weight"]
        d[u][v]=d[v][u]=min(d[u][v],w); nxt[u][v]=v; nxt[v][u]=u
    def snapshot(): return {u:{v:(d[u][v] if math.isfinite(d[u][v]) else None) for v in nodes} for u in nodes}
    steps=[event("initialize","Matrice initiale",
        "La diagonale vaut 0, les arêtes portent leurs poids et les autres couples valent l'infini.",
        distances=snapshot(),intermediate=None,active_edge=None)]
    for k in nodes:
        steps.append(event("intermediate",f"Sommet intermédiaire : {k}",
            f"On teste maintenant tous les chemins passant éventuellement par {k}.",
            distances=snapshot(),intermediate=k,active_edge=None))
        for i in nodes:
            for j in nodes:
                if d[i][k] < math.inf and d[k][j] < math.inf and d[i][k]+d[k][j] < d[i][j]:
                    old=d[i][j]; d[i][j]=d[i][k]+d[k][j]; nxt[i][j]=nxt[i][k]
                    steps.append(event("update",f"Chemin {i} → {j} amélioré",
                        f"Passer par {k} coûte {d[i][k]:g} + {d[k][j]:g} = {d[i][j]:g}, au lieu de {old if math.isfinite(old) else '∞'}.",
                        current_node=i,candidate_node=j,intermediate=k,distances=snapshot(),active_edge=None))
    negative=[n for n in nodes if d[n][n]<0]
    steps.append(event("complete","Calcul terminé",
        "La matrice finale est construite." + (" Un cycle négatif existe." if negative else ""),
        distances=snapshot(),negative_cycle_nodes=negative,active_edge=None))
    return make_response(graph,steps,{"distances":snapshot(),"negative_cycle":bool(negative)})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - floyd_warshall", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "floyd_warshall"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
