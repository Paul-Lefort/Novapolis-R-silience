import time
import networkx as nx
from fastapi import APIRouter, Query
from app.routers.api import load_networkx_graph_from_csv

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.get("/run")
def run_platform_benchmark(view: str = Query("routier")):
    """
    Exécute les mesures de performance (Dijkstra, Bellman-Ford, BFS, DFS, Floyd-Warshall)
    sur le réseau actif sans perturber le rendu Leaflet.
    """
    G = load_networkx_graph_from_csv(view)
    nodes = list(G.nodes())
    if len(nodes) < 2:
        return {"result": {"error": "Pas assez de sommets pour benchmarker"}}

    source = nodes[0]
    target = nodes[-1]
    repetitions = 5

    def measure(func, *args, **kwargs):
        times = []
        for _ in range(repetitions):
            t0 = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                pass
            times.append((time.perf_counter() - t0) * 1000)  # en millisecondes
        return round(sum(times) / len(times), 4)

    # Mesures
    t_dijkstra = measure(nx.dijkstra_path, G, source, target, weight='weight')
    t_bellman = measure(nx.bellman_ford_path, G, source, target, weight='weight')
    t_bfs = measure(nx.shortest_path, G, source, target)
    t_dfs = measure(list, nx.dfs_edges(G, source))

    # Floyd-Warshall (limité si le graphe est trop grand pour éviter le freeze)
    t_fw = None
    if len(nodes) <= 250:
        t_fw = measure(dict, nx.floyd_warshall(G, weight='weight'))

    return {
        "result": {
            "node_count": len(nodes),
            "edge_count": G.number_of_edges(),
            "metrics": {
                "Dijkstra": t_dijkstra,
                "Bellman-Ford": t_bellman,
                "BFS": t_bfs,
                "DFS": t_dfs,
                "Floyd-Warshall": t_fw
            }
        }
    }