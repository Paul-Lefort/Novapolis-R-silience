import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de Kruskal (Fibre)")
    G, start, _ = prepare_networkx_graph(graph_data, network_type="fibre")

    if len(G.nodes) == 0:
        logger.error("[ALGO] Kruskal : Le graphe est vide.")
        raise ValueError("Le graphe est vide.")

    steps = [event("initialize", "Initialisation de Kruskal", "Préparation du graphe non orienté.")]

    try:
        mst_edges = list(nx.minimum_spanning_edges(G, algorithm="kruskal", weight="weight", data=True))

        path_nodes = []
        total_weight = 0
        for u, v, data in mst_edges:
            total_weight += data.get("weight", 0)
            if u not in path_nodes: path_nodes.append(u)
            if v not in path_nodes: path_nodes.append(v)

        steps.append(event("complete", "MST Kruskal calculé", f"Poids total de {total_weight}."))
        logger.info(f"[ALGO] Kruskal terminé. Poids total : {total_weight}")

        return make_response(graph_data, steps, {
            "path": path_nodes,
            "cost": total_weight,
            "mst_edges": [{"source": u, "target": v, "weight": d.get("weight")} for u, v, d in mst_edges]
        })
    except Exception as exc:
        logger.error(f"[ALGO] Kruskal : Erreur critique -> {str(exc)}")
        raise ValueError(f"Erreur lors du calcul de Kruskal : {str(exc)}")