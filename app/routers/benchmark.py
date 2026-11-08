import time
import logging
import networkx as nx
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, Optional

from app.algorithme.helper import load_networkx_graph_from_csv

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

@router.get("/run")
def run_platform_benchmark(view: str = Query("routier")) -> Dict[str, Any]:
    logger.info(f"[BENCHMARK] Démarrage des mesures de performance sur la vue : '{view}'")

    try:
        G = load_networkx_graph_from_csv(view)
    except Exception as e:
        logger.error(f"[BENCHMARK] Échec du chargement du graphe : {str(e)}")
        raise HTTPException(status_code=500, detail="Impossible de charger le graphe pour le benchmark.")

    nodes = list(G.nodes())
    node_count, edge_count = len(nodes), G.number_of_edges()

    if node_count < 2:
        logger.warning("[BENCHMARK] Pas assez de sommets.")
        return {"result": {"error": "Pas assez de sommets pour benchmarker"}}

    source, target = nodes[0], nodes[-1]
    repetitions = 5

    def measure(algo_name: str, func, *args, **kwargs) -> Optional[float]:
        times = []
        for i in range(repetitions):
            t0 = time.perf_counter()
            try:
                func(*args, **kwargs)
            except nx.NetworkXNoPath:
                if i == 0: logger.warning(f"[BENCHMARK] {algo_name} : Aucun chemin entre {source} et {target}.")
                break
            except Exception as e:
                logger.error(f"[BENCHMARK] {algo_name} : Erreur ({str(e)})")
                break
            times.append((time.perf_counter() - t0) * 1000)

        if not times: return None
        return round(sum(times) / len(times), 4)

    metrics = {
        "Dijkstra": measure("Dijkstra", nx.dijkstra_path, G, source, target, weight='weight'),
        "Bellman-Ford": measure("Bellman-Ford", nx.bellman_ford_path, G, source, target, weight='weight'),
        "BFS": measure("BFS", nx.shortest_path, G, source, target),
        "DFS": measure("DFS", list, nx.dfs_edges(G, source))
    }

    if node_count <= 250:
        metrics["Floyd-Warshall"] = measure("Floyd-Warshall", dict, nx.floyd_warshall(G, weight='weight'))
    else:
        metrics["Floyd-Warshall"] = None

    logger.info("[BENCHMARK] Mesures terminées.")
    return {"result": {"node_count": node_count, "edge_count": edge_count, "metrics": metrics}}