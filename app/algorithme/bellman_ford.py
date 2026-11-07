import networkx as nx
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    G, start, target = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        raise ValueError(f"Le sommet de départ {start} est introuvable.")
    if target and target not in G:
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable.")

    steps = []
    steps.append(event("initialize", "Initialisation Bellman-Ford", f"Calcul depuis {start} vers {target}."))

    try:
        # NetworkX gère nativement Bellman-Ford et la détection de cycles de poids négatifs
        path = nx.bellman_ford_path(G, source=start, target=target, weight="weight")
        length = nx.bellman_ford_path_length(G, source=start, target=target, weight="weight")

        steps.append(event("complete", "Calcul terminé", f"Chemin Bellman-Ford trouvé (coût : {length})."))

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length,
            "negative_cycle": False
        })
    except nx.NetworkXUnbounded:
        return make_response(graph_data, steps, {
            "path": [],
            "cost": None,
            "negative_cycle": True
        })
    except nx.NetworkXNoPath:
        raise ValueError("Aucun chemin valide trouvé via Bellman-Ford.")