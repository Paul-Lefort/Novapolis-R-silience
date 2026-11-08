import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de Floyd-Warshall")
    G, start, target = prepare_networkx_graph(graph_data, network_type="routier")

    if len(G.nodes) == 0:
        logger.error("[ALGO] Floyd-Warshall : Le graphe est vide.")
        raise ValueError("Le graphe est vide ou tous les sommets ont été exclus (travaux).")

    steps = [event("initialize", "Initialisation Floyd-Warshall", "Préparation du graphe orienté et calcul de toutes les paires.")]

    try:
        all_pairs = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))
        all_paths = dict(nx.all_pairs_dijkstra_path(G, weight="weight"))

        steps.append(event("complete", "Calculs terminés", "Matrice de toutes les paires calculée avec succès."))
        logger.info("[ALGO] Floyd-Warshall terminé avec succès.")

        path = []
        cost = 0
        if start is not None and target is not None:
            if start in all_paths and target in all_paths[start]:
                path = all_paths[start][target]
                cost = all_pairs[start][target]
            else:
                logger.warning(f"[ALGO] Floyd-Warshall : Aucun chemin entre {start} et {target}.")
                raise ValueError(f"Aucun chemin valide n'existe entre {start} et {target}.")

        return make_response(graph_data, steps, {
            "path": path,
            "cost": cost,
            "all_pairs_distances": {str(k): v for k, v in all_pairs.items()}
        })

    except Exception as exc:
        logger.error(f"[ALGO] Floyd-Warshall : Erreur critique -> {str(exc)}")
        raise ValueError(f"Erreur lors du calcul de Floyd-Warshall : {str(exc)}")