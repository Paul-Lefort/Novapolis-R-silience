import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Optional

from app.algorithme.helper import load_networkx_graph_from_csv, parse_node_id
from app.algorithme import bellman_ford, bfs, dfs, dijkstra, floyd_warshall, kruskal, prim

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api", tags=["API Graphes"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class RunRequest(BaseModel):
    graph: Optional[dict[str, Any]] = None
    start: Optional[Any] = None
    target: Optional[Any] = None

@router.get("/sites")
def get_root_sites():
    file_path = BASE_DIR / "sites.csv"
    logger.info(f"[API] Requête /sites - Fichier existe: {file_path.exists()}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier sites.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")

@router.get("/routes")
def get_root_routes():
    file_path = BASE_DIR / "routes.csv"
    logger.info(f"[API] Requête /routes - Fichier existe: {file_path.exists()}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier routes.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")

@router.get("/fibre")
def get_root_fibre():
    file_path = BASE_DIR / "fibre.csv"
    logger.info(f"[API] Requête /fibre - Fichier existe: {file_path.exists()}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier fibre.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")

@router.post("/run-network/{algo_name}")
def run_network_algorithm_generic(algo_name: str, request: RunRequest, view: str = Query("routier")):
    logger.info(f"[API] POST /run-network/{algo_name}?view={view}")
    try:
        # Extraction sécurisée des paramètres
        graph_data = request.graph or {}
        start = parse_node_id(request.start if request.start is not None else graph_data.get("start"))
        target = parse_node_id(request.target if request.target is not None else graph_data.get("target"))

        # Si le front-end ne fournit pas le graphe complet dans le JSON, on le charge depuis le CSV
        G = load_networkx_graph_from_csv(view)

        if start is not None and start not in G:
            logger.warning(f"[API] Sommet de départ {start} introuvable.")
            raise HTTPException(status_code=400, detail=f"Sommet de départ {start} introuvable ou en travaux.")
        if target is not None and target not in G:
            logger.warning(f"[API] Sommet d'arrivée {target} introuvable.")
            raise HTTPException(status_code=400, detail=f"Sommet d'arrivée {target} introuvable ou en travaux.")

        # Préparation du payload pour les algos
        prepared_graph = {
            "nodes": list(G.nodes),
            "edges": [{"source": u, "target": v, "weight": data.get("weight", 1), "statut": data.get("statut", "")}
                      for u, v, data in G.edges(data=True)],
            "start": start,
            "target": target,
            "network_type": view  # <--- AJOUT ICI
        }

        # Délégation au module métier correspondant
        algos_map = {
            "bellman_ford": bellman_ford,
            "bfs": bfs,
            "dfs": dfs,
            "dijkstra": dijkstra,
            "floyd_warshall": floyd_warshall,
            "kruskal": kruskal,
            "prim": prim
        }

        if algo_name not in algos_map:
            logger.error(f"[API] Algorithme inconnu : {algo_name}")
            raise HTTPException(status_code=404, detail=f"Algorithme {algo_name} inconnu.")

        return algos_map[algo_name].run(prepared_graph)

    except HTTPException as he:
        raise he
    except Exception as exc:
        logger.error(f"[API] Erreur inattendue dans /run-network/{algo_name} : {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))