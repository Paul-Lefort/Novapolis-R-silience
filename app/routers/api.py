import os
import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Optional
import networkx as nx

# Import des modules d'algorithmes locaux
from app.algorithme import (
    bellman_ford,
    bfs,
    dfs,
    dijkstra,
    floyd_warshall,
    kruskal,
    prim
)

router = APIRouter(prefix="/api", tags=["API Graphes"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class RunRequest(BaseModel):
    graph: Optional[dict[str, Any]] = None
    start: Optional[Any] = None
    target: Optional[Any] = None


def load_networkx_graph_from_csv(view: str = "routier"):
    """
    Charge directement le CSV depuis le disque,
    exclut strictement les arêtes en travaux/maintenance/déploiement,
    et retourne un graphe NetworkX (DiGraph orienté pour la route, Graph pour la fibre).
    """
    csv_filename = "routes.csv" if view == "routier" else "fibre.csv"
    file_path = BASE_DIR / csv_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Fichier {csv_filename} introuvable. Générez le réseau d'abord.")

    G = nx.DiGraph() if view == "routier" else nx.Graph()

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u_raw = row.get("u")
            v_raw = row.get("v")
            if u_raw is None or v_raw is None:
                continue

            u = int(u_raw) if str(u_raw).isdigit() else u_raw
            v = int(v_raw) if str(v_raw).isdigit() else v_raw

            weight = float(row.get("distance_km") or row.get("temps_normal") or row.get("cost") or 1)
            statut = str(row.get("statut", "")).lower()

            G.add_node(u)
            G.add_node(v)

            # Exclusion stricte des zones en travaux, maintenance ou déploiement
            if any(kw in statut for kw in ["travaux", "maintenance", "deploiement"]):
                continue

            # Ajout de l'arête (respectant le sens unique pour le routier via DiGraph)
            G.add_edge(u, v, weight=weight)

    return G


@router.get("/sites")
def get_root_sites():
    file_path = BASE_DIR / "sites.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier sites.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")


@router.get("/routes")
def get_root_routes():
    file_path = BASE_DIR / "routes.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier routes.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")


@router.get("/fibre")
def get_root_fibre():
    file_path = BASE_DIR / "fibre.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier fibre.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")


def extract_params(request: RunRequest):
    graph_data = request.graph or {}
    start = request.start if request.start is not None else graph_data.get("start")
    target = request.target if request.target is not None else graph_data.get("target")

    if start is not None and str(start).isdigit():
        start = int(start)
    if target is not None and str(target).isdigit():
        target = int(target)

    return start, target, graph_data


@router.post("/run/{algo_name}")
def run_algorithm_generic(algo_name: str, request: RunRequest, view: str = Query("routier")):
    """
    Exécute l'algorithme demandé en chargeant proprement les données source via NetworkX,
    en filtrant les travaux et en respectant les sens uniques.
    """
    try:
        start, target, graph_data = extract_params(request)
        G = load_networkx_graph_from_csv(view)

        if start is not None and start not in G:
            raise HTTPException(status_code=400, detail=f"Sommet de départ {start} introuvable ou en travaux.")
        if target is not None and target not in G:
            raise HTTPException(status_code=400, detail=f"Sommet d'arrivée {target} introuvable ou en travaux.")

        nodes = list(G.nodes)
        edges = [{"source": u, "v": v, "target": v, "weight": data["weight"]} for u, v, data in G.edges(data=True)]

        prepared_graph = {
            "nodes": nodes,
            "edges": edges,
            "start": start,
            "target": target
        }

        if algo_name == "bellman_ford":
            return bellman_ford.run(prepared_graph)
        elif algo_name == "bfs":
            return bfs.run(prepared_graph)
        elif algo_name == "dfs":
            return dfs.run(prepared_graph)
        elif algo_name == "dijkstra":
            return dijkstra.run(prepared_graph)
        elif algo_name == "floyd_warshall":
            return floyd_warshall.run(prepared_graph)
        elif algo_name == "kruskal":
            return kruskal.run(prepared_graph)
        elif algo_name == "prim":
            return prim.run(prepared_graph)
        else:
            raise HTTPException(status_code=404, detail=f"Algorithme {algo_name} inconnu.")

    except HTTPException as he:
        raise he
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))