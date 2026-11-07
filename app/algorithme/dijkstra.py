import networkx as nx
import logging
from .common import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")


def run(graph_data):
    """
    Exécute l'algorithme de Dijkstra avec le logger Uvicorn et gère l'absence de chemin sans erreur critique.
    """
    logger.info(
        f"[DEBUG DIJKSTRA] Début de l'exécution avec graph_data reçus : start={graph_data.get('start')}, target={graph_data.get('target')}"
    )

    # Pour le réseau routier, on utilise un DiGraph orienté pour respecter strictement les sens uniques
    G, start, target = prepare_networkx_graph(graph_data, network_type="routier")

    logger.info(
        f"[DEBUG DIJKSTRA] Graphe préparé -> Noeuds: {len(G.nodes)}, Arêtes: {len(G.edges)} | Start: {start}, Target: {target}"
    )

    if len(G.nodes) == 0:
        logger.error("[DEBUG DIJKSTRA] ERREUR : Le graphe est vide ou tous les sommets ont été exclus.")
        raise ValueError("Le graphe est vide ou tous les sommets ont été exclus (travaux).")

    if start is None or target is None:
        logger.error("[DEBUG DIJKSTRA] ERREUR : Départ ou arrivée manquant.")
        raise ValueError("Dijkstra nécessite impérativement un sommet de départ et un sommet d'arrivée.")

    if start not in G:
        logger.warning(f"[DEBUG DIJKSTRA] ERREUR : Sommet de départ {start} introuvable.")
        raise ValueError(f"Le sommet de départ {start} est introuvable ou situé sur une route en travaux.")
    if target not in G:
        logger.warning(f"[DEBUG DIJKSTRA] ERREUR : Sommet d'arrivée {target} introuvable.")
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable ou situé sur une route en travaux.")

    steps = []
    steps.append(event("initialize", "Initialisation de Dijkstra",
                       f"Recherche du plus court chemin de {start} vers {target} en respectant les sens uniques."))

    try:
        logger.info(f"[DEBUG DIJKSTRA] Calcul du chemin le plus court de {start} à {target}...")
        # Utilisation des fonctions natives optimisées de NetworkX
        path = nx.shortest_path(G, source=start, target=target, weight="weight")
        length = nx.shortest_path_length(G, source=start, target=target, weight="weight")

        logger.info(f"[DEBUG DIJKSTRA] Succès ! Chemin trouvé : {path} (Coût : {length})")
        steps.append(event("complete", "Chemin optimal trouvé", f"Chemin calculé avec un coût total de {length}."))

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length
        })

    except nx.NetworkXNoPath:
        logger.warning(f"[DEBUG DIJKSTRA] Aucun chemin trouvé entre {start} et {target}.")
        steps.append(
            event("warning", "Aucun chemin trouvé", f"Aucun chemin valide n'existe entre {start} et {target}."))

        # On retourne une réponse valide (pas d'exception) indiquant l'absence de chemin
        return make_response(graph_data, steps, {
            "path": [],
            "cost": None,
            "message": f"Aucun chemin valide n'existe entre {start} et {target} en contournant les zones de travaux et en respectant les sens uniques."
        })

    except Exception as exc:
        logger.error(f"[DEBUG DIJKSTRA] ERREUR INATTENDUE : {str(exc)}")
        raise ValueError(f"Erreur lors du calcul de Dijkstra : {str(exc)}")