import networkx as nx
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    G, start, target = prepare_networkx_graph(graph_data, "routier")

    steps = []
    steps.append(event("initialize", "Initialisation Floyd-Warshall", "Calcul des plus courts chemins pour toutes les paires."))

    # Calcul global via NetworkX
    try:
        lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))
        paths = dict(nx.all_pairs_dijkstra_path(G, weight="weight"))

        path = paths.get(start, {}).get(target, []) if (start and target) else []
        cost = lengths.get(start, {}).get(target, None) if (start and target) else None

        steps.append(event("complete", "Calcul matriciel terminé", "Matrice des distances calculée avec succès."))

        return make_response(graph_data, steps, {
            "path": path,
            "cost": cost,
            "all_lengths": lengths
        })
    except Exception as e:
        raise ValueError(f"Erreur Floyd-Warshall : {str(e)}")