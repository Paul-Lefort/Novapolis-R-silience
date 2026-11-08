import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de Bellman-Ford")
    G, start, target = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        logger.error(f"[ALGO] Bellman-Ford : départ {start} introuvable.")
        raise ValueError(f"Le sommet de départ {start} est introuvable.")
    if target and target not in G:
        logger.error(f"[ALGO] Bellman-Ford : arrivée {target} introuvable.")
        raise ValueError(f"Le sommet d'arrivée {target} est introuvable.")

    steps = [event("initialize", "Initialisation Bellman-Ford", f"Calcul depuis {start} vers {target}.")]

    try:
        path = nx.bellman_ford_path(G, source=start, target=target, weight="weight")
        length = nx.bellman_ford_path_length(G, source=start, target=target, weight="weight")

        steps.append(event("complete", "Calcul terminé", f"Chemin trouvé (coût : {length})."))
        logger.info(f"[ALGO] Bellman-Ford réussi (Coût: {length}).")

        return make_response(graph_data, steps, {
            "path": path,
            "cost": length,
            "negative_cycle": False
        })
    except nx.NetworkXUnbounded:
        logger.warning("[ALGO] Bellman-Ford : Cycle de poids négatif détecté !")
        return make_response(graph_data, steps, {
            "path": [],
            "cost": None,
            "negative_cycle": True
        })
    except nx.NetworkXNoPath:
        logger.warning(f"[ALGO] Bellman-Ford : Aucun chemin entre {start} et {target}.")
        raise ValueError("Aucun chemin valide trouvé via Bellman-Ford.")