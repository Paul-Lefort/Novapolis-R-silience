from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.algorithms.dfs import run as dfs
from app.algorithms.bfs import run as bfs
from app.algorithms.dijkstra import run as dijkstra
from app.algorithms.bellman_ford import run as bellman_ford
from app.algorithms.floyd_warshall import run as floyd_warshall
from app.algorithms.kruskal import run as kruskal
from app.algorithms.prim import run as prim

router = APIRouter(prefix="/api/algorithms", tags=["Algorithms"])

ALGORITHMS = {
    "dfs": dfs,
    "bfs": bfs,
    "dijkstra": dijkstra,
    "bellman-ford": bellman_ford,
    "floyd-warshall": floyd_warshall,
    "kruskal": kruskal,
    "prim": prim,
}


class AlgorithmRequest(BaseModel):
    graph: dict


@router.post("/{algorithm}")
def run_algorithm(algorithm: str, request: AlgorithmRequest):
    runner = ALGORITHMS.get(algorithm)
    if runner is None:
        raise HTTPException(status_code=404, detail=f"Algorithme inconnu : {algorithm}")

    try:
        return runner(request.graph)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Graphe invalide : {exc}")
