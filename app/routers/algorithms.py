from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import des algorithmes Python
from app.algorithms.dfs import run as dfs
from app.algorithms.bfs import run as bfs
from app.algorithms.dijkstra import run as dijkstra
from app.algorithms.bellman_ford import run as bellman_ford
from app.algorithms.floyd_warshall import run as floyd_warshall
from app.algorithms.kruskal import run as kruskal
from app.algorithms.prim import run as prim

router = APIRouter(
    prefix="/api/algorithms",
    tags=["Algorithms"]
)


class AlgorithmRequest(BaseModel):
    graph: dict


# Association entre les noms des algorithmes et leurs fonctions
ALGORITHMS = {
    "dfs": dfs,
    "bfs": bfs,
    "dijkstra": dijkstra,
    "bellman_ford": bellman_ford,
    "floyd_warshall": floyd_warshall,
    "kruskal": kruskal,
    "prim": prim,
}


@router.post("/{algorithm}")
def run_algorithm(algorithm: str, request: AlgorithmRequest):

    if algorithm not in ALGORITHMS:
        raise HTTPException(
            status_code=404,
            detail=f"Algorithme inconnu : {algorithm}"
        )

    try:
        algorithm_function = ALGORITHMS[algorithm]

        result = algorithm_function(request.graph)

        return {
            "algorithm": algorithm,
            "result": result
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de l'exécution de {algorithm} : {str(e)}"
        )
