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
    arcs = [(u,v,e["weight"],e["id"]) for e in edges for u,v in [(e["source"],e["target"]),(e["target"],e["source"])]]
    dist={n:math.inf for n in nodes}; prev={n:None for n in nodes}; dist[start]=0; steps=[]
    steps.append(event("initialize","Initialisation",
        f"La distance de départ {start} vaut 0 ; les autres distances sont infinies.",
        current_node=start, distances={n:(0 if n==start else None) for n in nodes},
        predecessors=prev.copy(), active_edge=None, iteration=0))
    for i in range(len(nodes)-1):
        changed=False
        for u,v,w,eid in arcs:
            if dist[u] < math.inf and dist[u]+w < dist[v]:
                old=dist[v]; dist[v]=dist[u]+w; prev[v]=u; changed=True
                steps.append(event("relax","Distance améliorée",
                    f"Itération {i+1} : le trajet via {u} donne {dist[u]:g} + ({w:g}) = {dist[v]:g}, meilleur que {old if math.isfinite(old) else '∞'}.",
                    current_node=u,candidate_node=v,active_edge=eid,
                    distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
                    predecessors=prev.copy(),iteration=i+1))
            else:
                steps.append(event("check","Arête vérifiée",
                    f"Itération {i+1} : le passage de {u} vers {v} ne permet pas de réduire la distance.",
                    current_node=u,candidate_node=v,active_edge=eid,
                    distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
                    predecessors=prev.copy(),iteration=i+1))
        if not changed: break
    negative = any(dist[u] < math.inf and dist[u]+w < dist[v] for u,v,w,eid in arcs)
    steps.append(event("complete","Cycle négatif détecté" if negative else "Calcul terminé",
        "Une amélioration reste possible : un cycle de poids négatif est accessible." if negative else "Aucune amélioration supplémentaire : les distances sont stabilisées.",
        distances={n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
        predecessors=prev.copy(),active_edge=None))
    return make_response(graph,steps,{"distances":{n:(dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
        "predecessors":prev,"negative_cycle":negative})

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Novapolis - bellman_ford", version="1.0.0")

class RunRequest(BaseModel):
    graph: dict[str, Any]

@app.get("/health")
def health():
    return {"status": "ok", "algorithm": "bellman_ford"}

@app.post("/run")
def execute(request: RunRequest):
    try:
        return run(request.graph)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
