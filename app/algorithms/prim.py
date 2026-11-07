import heapq
from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start") or nodes[0]
    if start not in adj:
        raise ValueError("Sommet de départ invalide.")

    visited = {n: False for n in nodes}
    mst = []
    pq = []
    steps = []

    visited[start] = True
    for v, eid, w in adj[start]:
        heapq.heappush(pq, (w, start, v, eid))

    steps.append(event("initialize", "Initialisation Prim", f"Départ depuis {start}."))

    while pq:
        w, u, v, eid = heapq.heappop(pq)
        if visited[v]:
            continue
        visited[v] = True
        mst.append({"id": eid, "source": u, "target": v, "weight": w})
        steps.append(event("add_edge", "Arête ajoutée au MST", f"Ajout de {eid} ({u} - {v}).", active_edge=eid))

        for nxt, nxt_eid, nxt_w in adj[v]:
            if not visited[nxt]:
                heapq.heappush(pq, (nxt_w, v, nxt, nxt_eid))

    return make_response(graph, steps, {"mst": mst, "total_weight": sum(e["weight"] for e in mst)})