import networkx as nx
from .common import prepare_networkx_graph, event, make_response


def run(graph_data):
    G, start, target = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        raise ValueError(f"Le sommet de départ {start} est introuvable ou exclu.")
    if target and target not in G:
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable ou exclu.")

    steps = []
    steps.append(
        event("initialize", "Initialisation Dijkstra", f"Recherche du plus court chemin depuis {start} vers {target}."))

    try:
        path = nx.shortest_path(G, source=start, target=target, weight="weight")
        length = nx.shortest_path_length(G, source=start, target=target, weight="weight")

        steps.append(event("complete", "Chemin optimal trouvé", f"Chemin trouvé avec un coût total de {length}."))

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length
        })
    except nx.NetworkXNoPath:
        raise ValueError(
            "Aucun chemin valide n'existe entre le départ et l'arrivée en contournant les zones de travaux.")