import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de Dijkstra")
    G, start, target = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        logger.error(f"[ALGO] Dijkstra : départ {start} introuvable.")
        raise ValueError(f"Le sommet de départ {start} est introuvable.")
    if target and target not in G:
        logger.error(f"[ALGO] Dijkstra : arrivée {target} introuvable.")
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable.")

    steps = [event("initialize", "Initialisation Dijkstra", f"Calcul depuis {start} vers {target}.")]

    try:
        path = nx.dijkstra_path(G, source=start, target=target, weight="weight")
        length = nx.dijkstra_path_length(G, source=start, target=target, weight="weight")

        steps.append(event("complete", "Calcul terminé", f"Chemin trouvé (coût : {length})."))
        logger.info(f"[ALGO] Dijkstra réussi (Coût: {length}).")

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length
        })
    except nx.NetworkXNoPath:
        logger.warning(f"[ALGO] Dijkstra : Aucun chemin entre {start} et {target}.")
        raise ValueError("Aucun chemin valide trouvé via Dijkstra.")
    except Exception as exc:
        logger.error(f"[ALGO] Dijkstra : Erreur inattendue -> {str(exc)}")
        raise ValueError(f"Erreur lors du calcul de Dijkstra : {str(exc)}")