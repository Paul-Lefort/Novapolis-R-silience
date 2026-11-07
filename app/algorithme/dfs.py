import networkx as nx
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    G, start, _ = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        raise ValueError(f"Le sommet de départ {start} est introuvable.")

    steps = []
    steps.append(event("initialize", "Initialisation DFS", f"Parcours en profondeur à partir de {start}."))

    dfs_edges = list(nx.dfs_edges(G, source=start))
    visited_nodes = [start] + [v for _, v in dfs_edges]

    steps.append(event("complete", "Parcours DFS terminé", f"{len(visited_nodes)} sommets visités."))

    return make_response(graph_data, steps, {
        "visited_nodes": visited_nodes,
        "dfs_edges": dfs_edges
    })