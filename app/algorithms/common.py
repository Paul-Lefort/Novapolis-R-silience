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
    normalized_steps = [{"index": index, **step} for index, step in enumerate(steps)]
    return {
        "graph": graph,
        "steps": normalized_steps,
        "step_count": len(normalized_steps),
        "result": result
    }