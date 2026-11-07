import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Optional
import networkx as nx

import logging

logger = logging.getLogger("uvicorn.error")

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
    logger.info(f"[DEBUG LOAD] Chemin complet visé : {file_path} | Existe : {file_path.exists()}")

    if not file_path.exists():
        logger.error(f"[DEBUG LOAD] ERREUR : Fichier {csv_filename} introuvable.")
        raise HTTPException(status_code=404, detail=f"Fichier {csv_filename} introuvable. Générez le réseau d'abord.")

    G = nx.DiGraph() if view == "routier" else nx.Graph()

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        logger.info(f"[DEBUG LOAD] En-têtes CSV détectés pour {csv_filename} : {reader.fieldnames}")

        count_lignes = 0
        count_sans_uv = 0
        count_exclus_statut = 0

        for row in reader:
            count_lignes += 1
            u_raw = row.get("u")
            v_raw = row.get("v")
            if u_raw is None or v_raw is None:
                count_sans_uv += 1
                continue

            u = int(u_raw) if str(u_raw).isdigit() else u_raw
            v = int(v_raw) if str(v_raw).isdigit() else v_raw

            weight = float(row.get("distance_km") or row.get("temps_normal") or row.get("cost") or 1)
            statut = str(row.get("statut", "")).lower()

            G.add_node(u)
            G.add_node(v)

            if any(kw in statut for kw in ["travaux", "maintenance", "deploiement"]):
                count_exclus_statut += 1
                continue

            G.add_edge(u, v, weight=weight)

    logger.info(
        f"[DEBUG LOAD] Bilan {csv_filename} -> Lignes lues: {count_lignes} | Sans u/v: {count_sans_uv} | Exclus statut: {count_exclus_statut} | Noeuds finaux: {len(G.nodes)} | Arêtes finales: {len(G.edges)}"
    )
    return G

@router.get("/sites")
def get_root_sites():
    file_path = BASE_DIR / "sites.csv"
    logger.info(f"[DEBUG API] Requête /sites - Fichier existe: {file_path.exists()}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier sites.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")


@router.get("/routes")
def get_root_routes():
    file_path = BASE_DIR / "routes.csv"
    logger.info(f"[DEBUG API] Requête /routes - Fichier existe: {file_path.exists()}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier routes.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")


@router.get("/fibre")
def get_root_fibre():
    file_path = BASE_DIR / "fibre.csv"
    logger.info(f"[DEBUG API] Requête /fibre - Fichier existe: {file_path.exists()}")
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

    logger.info(f"[DEBUG PARAMS] Paramètres extraits -> start: {start}, target: {target}")
    return start, target, graph_data


def execute_algorithm_logic(algo_name: str, request: RunRequest, view: str):
    logger.info(f"[DEBUG ALGO] Exécution de l'algorithme '{algo_name}' sur la vue '{view}'")
    start, target, graph_data = extract_params(request)
    G = load_networkx_graph_from_csv(view)

    if start is not None and start not in G:
        logger.warning(f"[DEBUG ALGO] Sommet de départ {start} introuvable ou en travaux.")
        raise HTTPException(status_code=400, detail=f"Sommet de départ {start} introuvable ou en travaux.")
    if target is not None and target not in G:
        logger.warning(f"[DEBUG ALGO] Sommet d'arrivée {target} introuvable ou en travaux.")
        raise HTTPException(status_code=400, detail=f"Sommet d'arrivée {target} introuvable ou en travaux.")

    nodes = list(G.nodes)
    edges = [{"source": u, "v": v, "target": v, "weight": data["weight"]} for u, v, data in G.edges(data=True)]

    prepared_graph = {
        "nodes": nodes,
        "edges": edges,
        "start": start,
        "target": target
    }

    logger.info(f"[DEBUG ALGO] Lancement effectif de la fonction run() pour {algo_name}")
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
        logger.error(f"[DEBUG ALGO] Algorithme inconnu : {algo_name}")
        raise HTTPException(status_code=404, detail=f"Algorithme {algo_name} inconnu.")


@router.post("/run/{algo_name}")
def run_algorithm_generic(algo_name: str, request: RunRequest, view: str = Query("routier")):
    logger.info(f"[DEBUG API] POST /run/{algo_name}?view={view}")
    try:
        return execute_algorithm_logic(algo_name, request, view)
    except HTTPException as he:
        raise he
    except Exception as exc:
        logger.error(f"[DEBUG API] Erreur inattendue dans /run/{algo_name} : {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/run-network/{algo_name}")
def run_network_algorithm_generic(algo_name: str, request: RunRequest, view: str = Query("routier")):
    logger.info(f"[DEBUG API] POST /run-network/{algo_name}?view={view}")
    try:
        return execute_algorithm_logic(algo_name, request, view)
    except HTTPException as he:
        raise he
    except Exception as exc:
        logger.error(f"[DEBUG API] Erreur inattendue dans /run-network/{algo_name} : {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/analysis/report")
def get_network_analysis_report(view: Optional[str] = Query("routier")):
    """
    Génère le rapport complet des 5 indicateurs pour l'interface et le rapport.
    """
    logger.info(f"[DEBUG_API] GET /analysis/report avec view={view}")
    try:
        from app.algorithme.analysis_service import analyser_indicateurs_reseau

        selected_view = view if view in ["routier", "fibre"] else "routier"
        logger.info(f"[DEBUG_API] Appel de analyser_indicateurs_reseau pour la vue : {selected_view}")

        resultats = analyser_indicateurs_reseau(selected_view)

        return {
            "status": "success",
            "view": selected_view,
            "casernes_reference": resultats.get("casernes_reference", []),
            "nb_sites_accessibles": len(resultats.get("accessibilite_casernes", [])),
            "nb_composantes_fibre": len(resultats.get("composantes_fibre", [])),
            "cycles_orientes": resultats.get("cycles_orientes", False),
            "sites_isoles": resultats.get("sites_isoles", []),
            "sites_non_atteignables": resultats.get("sites_non_atteignables", [])
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"ERREUR API REPORT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne d'analyse: {str(e)}")