import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de DFS")
    G, start, _ = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        logger.error(f"[ALGO] DFS : sommet de départ {start} introuvable.")
        raise ValueError(f"Le sommet de départ {start} est introuvable.")

    steps = [event("initialize", "Initialisation DFS", f"Parcours en profondeur à partir de {start}.")]

    dfs_edges = list(nx.dfs_edges(G, source=start))
    visited_nodes = [start] + [v for _, v in dfs_edges]

    steps.append(event("complete", "Parcours DFS terminé", f"{len(visited_nodes)} sommets visités."))
    logger.info(f"[ALGO] DFS terminé avec succès. {len(visited_nodes)} sommets visités.")

    return make_response(graph_data, steps, {
        "visited_nodes": visited_nodes,
        "dfs_edges": dfs_edges
    })