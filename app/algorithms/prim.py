import heapq

from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start") or nodes[0]
    if start not in adj:
        raise ValueError("Sommet de départ invalide.")

    visited = {n: False for n in nodes}
    forest = []
    steps = []
    total_weight = 0.0

    # Prim est relancé depuis chaque sommet non visité pour gérer les graphes
    # déconnectés : le résultat est alors une forêt couvrante minimale.
    component_starts = [start] + [node for node in nodes if node != start]

    steps.append(event(
        "initialize", "Initialisation Prim",
        f"Départ depuis {start}. Le calcul couvrira aussi les autres composantes."
    ))

    for component_start in component_starts:
        if visited[component_start]:
            continue

        visited[component_start] = True
        pq = []
        for v, eid, weight in adj[component_start]:
            heapq.heappush(pq, (weight, component_start, v, eid))

        if component_start != start:
            steps.append(event(
                "new_component", "Nouvelle composante",
                f"Le sommet {component_start} appartient à une composante non encore visitée.",
                current_node=component_start
            ))

        while pq:
            weight, u, v, eid = heapq.heappop(pq)
            if visited[v]:
                steps.append(event(
                    "skip_edge", "Arête ignorée",
                    f"L'arête {eid} mène à un sommet déjà intégré.",
                    current_node=u, candidate_node=v, active_edge=eid
                ))
                continue

            visited[v] = True
            edge_result = {
                "id": eid, "source": u, "target": v, "weight": weight
            }
            forest.append(edge_result)
            total_weight += weight
            steps.append(event(
                "add_edge", "Arête ajoutée à la forêt",
                f"Ajout de {eid} ({u} - {v}), poids {weight:g}.",
                current_node=u, candidate_node=v, active_edge=eid,
                visited=visited.copy()
            ))

            for nxt, nxt_eid, nxt_weight in adj[v]:
                if not visited[nxt]:
                    heapq.heappush(pq, (nxt_weight, v, nxt, nxt_eid))

    return make_response(graph, steps, {
        "mst": forest,
        "total_weight": total_weight,
        "is_spanning_tree": len(forest) == max(0, len(nodes) - 1)
    })
