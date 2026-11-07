import networkx as nx
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    G, start, _ = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        raise ValueError(f"Le sommet de départ {start} est introuvable.")

    steps = []
    steps.append(event("initialize", "Initialisation BFS", f"Parcours en largeur à partir de {start}."))

    # Génération de l'arbre BFS via NetworkX
    bfs_edges = list(nx.bfs_edges(G, source=start))
    visited_nodes = [start] + [v for _, v in bfs_edges]

    steps.append(event("complete", "Parcours BFS terminé", f"{len(visited_nodes)} sommets visités."))

    return make_response(graph_data, steps, {
        "visited_nodes": visited_nodes,
        "bfs_edges": bfs_edges
    })