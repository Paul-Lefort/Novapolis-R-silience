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
        if w < dist[j][i]:
            dist[j][i] = w

    steps = []
    steps.append(event("initialize", "Initialisation Floyd-Warshall", "Matrice des distances initialisée."))

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    steps.append(
                        event("relax", "Chemin amélioré", f"Passage par {nodes[k]} améliore {nodes[i]} -> {nodes[j]}."))

    return make_response(graph, steps, {"distances": dist, "nodes": nodes})