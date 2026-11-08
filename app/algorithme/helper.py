import csv
import logging
from pathlib import Path
from typing import Any, Optional, Tuple, Dict, List
import networkx as nx
from fastapi import HTTPException

# Logger centralisé pour tous les algorithmes
logger = logging.getLogger("uvicorn.error")

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def parse_node_id(value: Any) -> Any:
    """Standardise les IDs : '12' -> 12, 'A3' -> 'A3'."""
    value_str = str(value).strip()
    return int(value_str) if value_str.isdigit() else value_str


def _parse_numeric(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_networkx_graph_from_csv(view: str = "routier") -> nx.Graph:
    """Charge le graphe depuis les fichiers CSV générés sur le serveur."""
    csv_filename = "routes.csv" if view == "routier" else "fibre.csv"
    file_path = BASE_DIR / csv_filename

    logger.info(f"[HELPER] Chargement CSV de la vue '{view}'")

    if not file_path.exists():
        logger.error(f"[HELPER] Fichier introuvable : {file_path}")
        raise HTTPException(status_code=404, detail=f"{csv_filename} introuvable. Générez le réseau d'abord.")

    G = nx.DiGraph() if view == "routier" else nx.Graph()

    # 1. Ajout des sommets
    sites_path = BASE_DIR / "sites.csv"
    if sites_path.exists():
        with open(sites_path, mode="r", encoding="utf-8-sig") as f:
            for site in csv.DictReader(f):
                if site.get("id"):
                    G.add_node(parse_node_id(site["id"]), type=str(site.get("type", "")), nom=str(site.get("nom", "")))

    # 2. Ajout des arêtes
    count_exclus = 0
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not row.get("u") or not row.get("v"): continue

            u, v = parse_node_id(row["u"]), parse_node_id(row["v"])
            statut = str(row.get("statut", "")).lower()

            G.add_node(u)
            G.add_node(v)

            # Filtre des routes impraticables
            if any(kw in statut for kw in ["travaux", "maintenance", "deploiement"]):
                count_exclus += 1
                continue

            weight = float(row.get("distance_km") or row.get("temps_normal") or row.get("cost") or 1)
            cost = _parse_numeric(row.get("cost"))

            G.add_edge(
                u, v, weight=weight,
                distance_km=_parse_numeric(row.get("distance_km")),
                temps_normal=_parse_numeric(row.get("temps_normal")),
                temps_pointe=_parse_numeric(row.get("temps_pointe")),
                cost=cost if cost is not None else weight,
                statut=statut,
            )

    logger.info(f"[HELPER] CSV Chargé : {len(G.nodes)} noeuds, {len(G.edges)} arêtes (Exclus: {count_exclus})")
    return G


def prepare_networkx_graph(graph_data: Dict[str, Any], network_type: str = "routier") -> Tuple[nx.Graph, Any, Any]:
    """Charge le graphe à partir d'un payload JSON interactif."""
    logger.info(f"[HELPER] Préparation du graphe depuis payload JSON ({network_type})")

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    start = parse_node_id(graph_data.get("start")) if graph_data.get("start") is not None else None
    target = parse_node_id(graph_data.get("target")) if graph_data.get("target") is not None else None

    G = nx.DiGraph() if network_type == "routier" else nx.Graph()
    for n in nodes:
        G.add_node(parse_node_id(n))

    count_exclus = 0
    for e in edges:
        u, v = parse_node_id(e.get("source")), parse_node_id(e.get("target"))
        weight, statut = float(e.get("weight", 1)), str(e.get("statut", "")).lower()

        if any(kw in statut for kw in ["travaux", "maintenance", "deploiement"]):
            count_exclus += 1
            continue

        if u in G and v in G:
            if G.has_edge(u, v) and weight >= G[u][v].get("weight", float("inf")):
                continue
            G.add_edge(u, v, weight=weight, id=e.get("id"))

    logger.debug(f"[HELPER] JSON chargé : {len(G.nodes)} noeuds, {len(G.edges)} arêtes (Exclus: {count_exclus})")
    return G, start, target


def event(step_type: str, title: str, description: str, **kwargs) -> Dict[str, Any]:
    base = {"type": step_type, "title": title, "description": description}
    base.update(kwargs)
    return base


def make_response(graph_data: Dict[str, Any], steps: List[Dict[str, Any]], result_data: Any) -> Dict[str, Any]:
    return {"step_count": len(steps), "steps": steps, "result": result_data}