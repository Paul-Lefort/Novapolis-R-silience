import networkx as nx
from .common import prepare_networkx_graph, event, make_response

def run(graph_data):
    # Pour le réseau routier, on utilise un DiGraph orienté pour respecter strictement les sens uniques
    # (Pour la fibre, change network_type en "fibre" si besoin)
    G, start, target = prepare_networkx_graph(graph_data, network_type="routier")

    if len(G.nodes) == 0:
        raise ValueError("Le graphe est vide ou tous les sommets ont été exclus (travaux).")

    if start is None or target is None:
        raise ValueError("Dijkstra nécessite impérativement un sommet de départ et un sommet d'arrivée.")

    if start not in G:
        raise ValueError(f"Le sommet de départ {start} est introuvable ou situé sur une route en travaux.")
    if target not in G:
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable ou situé sur une route en travaux.")

    steps = []
    steps.append(event("initialize", "Initialisation de Dijkstra", f"Recherche du plus court chemin de {start} vers {target} en respectant les sens uniques."))

    try:
        # Utilisation des fonctions natives optimisées de NetworkX
        path = nx.shortest_path(G, source=start, target=target, weight="weight")
        length = nx.shortest_path_length(G, source=start, target=target, weight="weight")

        steps.append(event("complete", "Chemin optimal trouvé", f"Chemin calculé avec un coût total de {length}."))

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length
        })

    except nx.NetworkXNoPath:
        raise ValueError(f"Aucun chemin valide n'existe entre {start} et {target} en contournant les zones de travaux et en respectant les sens uniques.")
    except Exception as exc:
        raise ValueError(f"Erreur lors du calcul de Dijkstra : {str(exc)}")