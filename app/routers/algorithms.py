
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/algorithms", tags=["Algorithms"])

SERVICES = {
    "dfs": os.getenv("DFS_URL", "http://dfs:8000"),
    "bfs": os.getenv("BFS_URL", "http://bfs:8000"),
    "dijkstra": os.getenv("DIJKSTRA_URL", "http://dijkstra:8000"),
    "bellman_ford": os.getenv(
        "BELLMAN_FORD_URL", "http://bellman_ford:8000"
    ),
    "floyd_warshall": os.getenv(
        "FLOYD_WARSHALL_URL", "http://floyd_warshall:8000"
    ),
    "kruskal": os.getenv("KRUSKAL_URL", "http://kruskal:8000"),
    "prim": os.getenv("PRIM_URL", "http://prim:8000"),
}


class AlgorithmRequest(BaseModel):
    graph: dict


@router.post("/{algorithm}")
async def run_algorithm(algorithm: str, request: AlgorithmRequest):
    if algorithm not in SERVICES:
        raise HTTPException(
            status_code=404,
            detail=f"Algorithme inconnu : {algorithm}"
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{SERVICES[algorithm]}/run",
                json=request.model_dump()
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Le microservice a mis trop de temps à répondre."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=f"Le microservice {algorithm} est indisponible."
        )
