import networkx as nx
# Assure-toi d'importer ta fonction prepare_networkx_graph depuis common (ou le module approprié)
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    # Pour le réseau routier, on utilise un DiGraph orienté pour respecter les sens uniques
    G, start, target = prepare_networkx_graph(graph_data, network_type="routier")

    if len(G.nodes) == 0:
        raise ValueError("Le graphe est vide ou tous les sommets ont été exclus (travaux).")

    steps = []
    steps.append(event("initialize", "Initialisation Floyd-Warshall", "Préparation du graphe orienté et filtrage des zones en travaux."))

    try:
        # NetworkX propose une fonction native et ultra-rapide pour Floyd-Warshall (toutes les paires)
        # Elle retourne un dictionnaire de dictionnaires : {u: {v: distance}}
        all_pairs = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))
        all_paths = dict(nx.all_pairs_dijkstra_path(G, weight="weight"))

        steps.append(event("complete", "Calculs terminés", "Matrice de toutes les paires de plus courts chemins calculée avec succès."))

        # Si un couple départ / arrivée est fourni, on isole ce chemin spécifique pour l'affichage visuel
        path = []
        cost = 0
        if start is not None and target is not None:
            if start in all_paths and target in all_paths[start]:
                path = all_paths[start][target]
                cost = all_pairs[start][target]
            else:
                raise ValueError(f"Aucun chemin valide n'existe entre {start} et {target} (en contournant les travaux).")

        return make_response(graph_data, steps, {
            "path": path,
            "cost": cost,
            # On retourne aussi toutes les distances si tu en as besoin dans l'interface
            "all_pairs_distances": {str(k): v for k, v in all_pairs.items()}
        })

    except Exception as exc:
        raise ValueError(f"Erreur lors du calcul de Floyd-Warshall : {str(exc)}")