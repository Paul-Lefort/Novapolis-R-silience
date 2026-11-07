import heapq
import math
from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")

    dist = {n: math.inf for n in nodes}
    prev = {n: None for n in nodes}
    dist[start] = 0
    pq = [(0, start)]
    steps = []

    steps.append(event("initialize", "Initialisation Dijkstra", f"Distance de départ {start} à 0.", current_node=start,
                       distances={n: 0 if n == start else None for n in nodes}))

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        steps.append(
            event("pop", "Extraction du min", f"Sommet {u} extrait avec une distance de {d:g}.", current_node=u,
                  distances={n: (dist[n] if math.isfinite(dist[n]) else None) for n in nodes}))

        for v, eid, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
                steps.append(event("relax", "Distance améliorée", f"Via {u}, distance de {v} réduite à {dist[v]:g}.",
                                   current_node=u, candidate_node=v, active_edge=eid,
                                   distances={n: (dist[n] if math.isfinite(dist[n]) else None) for n in nodes}))
            else:
                steps.append(event("check", "Arête vérifiée", f"Pas d'amélioration pour {v} via {u}.", current_node=u,
                                   candidate_node=v, active_edge=eid))

    steps.append(event("complete", "Dijkstra Terminé", "Plus courts chemins calculés.",
                       distances={n: (dist[n] if math.isfinite(dist[n]) else None) for n in nodes}))
    return make_response(graph, steps, {"distances": {n: (dist[n] if math.isfinite(dist[n]) else None) for n in nodes},
                                        "predecessors": prev})