import math

from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    dist = [[math.inf] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0

    for edge in edges:
        u, v, w = edge["source"], edge["target"], edge["weight"]
        i, j = node_to_idx[u], node_to_idx[v]
        if w < dist[i][j]:
            dist[i][j] = w
            dist[j][i] = w

    def visible_matrix():
        return [[value if math.isfinite(value) else None for value in row]
                for row in dist]

    steps = [event(
        "initialize", "Initialisation Floyd-Warshall",
        "Matrice des distances initialisée.",
        matrix=visible_matrix()
    )]

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] != math.inf and dist[k][j] != math.inf:
                    candidate = dist[i][k] + dist[k][j]
                    if candidate < dist[i][j]:
                        old = dist[i][j]
                        dist[i][j] = candidate
                        steps.append(event(
                            "relax", "Chemin amélioré",
                            f"Passage par {nodes[k]} améliore {nodes[i]} → {nodes[j]} "
                            f"(ancienne distance : {old}, nouvelle : {candidate}).",
                            pivot_node=nodes[k],
                            current_node=nodes[i],
                            candidate_node=nodes[j],
                            matrix=visible_matrix()
                        ))

    return make_response(graph, steps, {
        "distances": visible_matrix(),
        "nodes": nodes
    })
