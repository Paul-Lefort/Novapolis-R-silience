import networkx as nx
from .common import prepare_networkx_graph, event, make_response


def run(graph_data):
    # Les algorithmes de MST (Kruskal/Prim) s'appliquent par défaut au réseau fibre (non orienté)
    G, start, _ = prepare_networkx_graph(graph_data, network_type="fibre")

    if len(G.nodes) == 0:
        raise ValueError("Le graphe est vide.")

    steps = []
    steps.append(event("initialize", "Initialisation de Kruskal",
                       "Préparation du graphe non orienté (hors maintenance/déploiement)."))

    try:
        # Utilisation de NetworkX pour Kruskal (génère un ensemble d'arêtes)
        mst_edges = list(nx.minimum_spanning_edges(G, algorithm="kruskal", weight="weight", data=True))

        # Reconstruction du chemin ou de la liste des arêtes du MST pour l'affichage
        path_nodes = []
        total_weight = 0
        for u, v, data in mst_edges:
            total_weight += data.get("weight", 0)
            if u not in path_nodes: path_nodes.append(u)
            if v not in path_nodes: path_nodes.append(v)

        steps.append(event("complete", "MST Kruskal calculé",
                           f"Arbre couvrant minimum trouvé avec un poids total de {total_weight}."))

        return make_response(graph_data, steps, {
            "path": path_nodes,
            "cost": total_weight,
            "mst_edges": [{"source": u, "target": v, "weight": d.get("weight")} for u, v, d in mst_edges]
        })
    except Exception as exc:
        raise ValueError(f"Erreur lors du calcul de Kruskal : {str(exc)}")