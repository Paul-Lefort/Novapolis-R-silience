import logging
import networkx as nx
from .helper import prepare_networkx_graph, event, make_response

logger = logging.getLogger("uvicorn.error")

def run(graph_data):
    logger.info("[ALGO] Lancement de BFS")
    G, start, _ = prepare_networkx_graph(graph_data, "routier")

    if start not in G:
        logger.error(f"[ALGO] BFS : sommet de départ {start} introuvable.")
        raise ValueError(f"Le sommet de départ {start} est introuvable.")

    steps = [event("initialize", "Initialisation BFS", f"Parcours en largeur à partir de {start}.")]

    bfs_edges = list(nx.bfs_edges(G, source=start))
    visited_nodes = [start] + [v for _, v in bfs_edges]

    steps.append(event("complete", "Parcours BFS terminé", f"{len(visited_nodes)} sommets visités."))
    logger.info(f"[ALGO] BFS terminé avec succès. {len(visited_nodes)} sommets visités.")

    return make_response(graph_data, steps, {
        "visited_nodes": visited_nodes,
        "bfs_edges": bfs_edges
    })