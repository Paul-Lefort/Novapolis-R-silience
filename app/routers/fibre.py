import networkx as nx
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Form, UploadFile, File
from typing import Dict, Any, List, Optional
import io
from app.routers.api import load_networkx_graph_from_csv

router = APIRouter(prefix="/api/fibre", tags=["fibre"])


def calculer_acm_reseau(algo: str = "kruskal", weight_attr: str = "cost") -> Dict[str, Any]:
    """
    Exécute Kruskal ou Prim sur le réseau Fibre (graphe non orienté).
    Calcule l'ACM ou la Forêt Couvrante si le graphe comporte plusieurs composantes connexes.
    """
    G_fibre = load_networkx_graph_from_csv("fibre")  # Graph non orienté

    if len(G_fibre.nodes) == 0:
        return {
            "algo": algo,
            "cost_total": 0.0,
            "nb_edges_acm": 0,
            "edges_acm": [],
            "est_connexe": True,
            "nb_composantes": 0,
            "composantes_non_raccordees": []
        }

    # 1. Vérification de la connexité et découpage en composantes
    composantes = [list(c) for c in nx.connected_components(G_fibre)]
    est_connexe = len(composantes) == 1

    # 2. Exécution de l'algorithme (Kruskal ou Prim)
    if algo == "kruskal":
        mst_graph = nx.minimum_spanning_tree(G_fibre, algorithm="kruskal", weight=weight_attr)
    elif algo == "prim":
        mst_graph = nx.minimum_spanning_tree(G_fibre, algorithm="prim", weight=weight_attr)
    else:
        raise HTTPException(status_code=400, detail=f"Algorithme inconnu : {algo}")

    # 3. Extraction des tronçons retenus et du coût total
    edges_acm = []
    cost_total = 0.0

    for u, v, data in mst_graph.edges(data=True):
        cost = float(data.get(weight_attr, 1.0))
        cost_total += cost
        edges_acm.append({
            "u": u,
            "v": v,
            "cost": round(cost, 2),
            "statut": data.get("statut", "actif")
        })

    # Identification des composantes isolées si le graphe est non connexe
    composantes_non_raccordees = composantes[1:] if len(composantes) > 1 else []

    return {
        "algo": algo,
        "cost_total": round(cost_total, 2),
        "nb_edges_acm": len(edges_acm),
        "edges_acm": edges_acm,
        "est_connexe": est_connexe,
        "nb_composantes": len(composantes),
        "composantes_non_raccordees": composantes_non_raccordees
    }


@router.get("/acm")
def get_acm_endpoint(algo: str = Query("kruskal")):
    """
    Endpoint pour récupérer l'ACM avec Kruskal ou Prim.
    """
    return {"result": calculer_acm_reseau(algo=algo)}


@router.get("/comparer")
def comparer_kruskal_prim():
    """
    Exécute et compare Kruskal et Prim sur la même instance de réseau fibre.
    """
    res_kruskal = calculer_acm_reseau("kruskal")
    res_prim = calculer_acm_reseau("prim")

    coherence = abs(res_kruskal["cost_total"] - res_prim["cost_total"]) < 1e-4

    return {
        "result": {
            "coherence_cout_total": coherence,
            "kruskal": res_kruskal,
            "prim": res_prim
        }
    }


@router.post("/simuler-panne-troncon")
def simuler_panne_troncon(u: str = Form(...), v: str = Form(...), weight_attr: str = "cost"):
    """
    Étudie une panne : retire un tronçon de l'arbre couvrant minimal, puis cherche
    le tronçon de raccordement de secours le moins coûteux disponible dans le graphe initial.
    """
    G_fibre = load_networkx_graph_from_csv("fibre")

    u_node = int(u) if str(u).isdigit() else u
    v_node = int(v) if str(v).isdigit() else v

    if not G_fibre.has_edge(u_node, v_node):
        raise HTTPException(status_code=400, detail=f"Le tronçon ({u_node}, {v_node}) n'existe pas dans le réseau.")

    # 1. Calcul de l'ACM initial (Kruskal)
    mst_initial = nx.minimum_spanning_tree(G_fibre, algorithm="kruskal", weight=weight_attr)

    if not mst_initial.has_edge(u_node, v_node):
        return {
            "result": {
                "impact_acm": False,
                "message": f"Le tronçon ({u_node}, {v_node}) ne fait pas partie de l'arbre couvrant minimal initial."
            }
        }

    # 2. Suppression du tronçon de l'ACM initial
    mst_rompu = mst_initial.copy()
    mst_rompu.remove_edge(u_node, v_node)

    # La suppression d'une arête d'un arbre le sépare exactement en 2 composantes connexes
    comp_a, comp_b = list(nx.connected_components(mst_rompu))

    # 3. Recherche du tronçon de secours le moins coûteux dans le graphe initial G_fibre
    troncon_secours = None
    min_secours_cost = float("inf")

    for x, y, data in G_fibre.edges(data=True):
        # Exclure le tronçon en panne
        if (x == u_node and y == v_node) or (x == v_node and y == u_node):
            continue

        # Le tronçon de secours doit relier la composante A à la composante B
        if (x in comp_a and y in comp_b) or (x in comp_b and y in comp_a):
            cost = float(data.get(weight_attr, 1.0))
            if cost < min_secours_cost:
                min_secours_cost = cost
                troncon_secours = {"u": x, "v": y, "cost": round(cost, 2)}

    raccordement_possible = troncon_secours is not None
    nouveau_cout_total = None
    if raccordement_possible:
        nouveau_cout_total = round(
            sum(d.get(weight_attr, 1.0) for _, _, d in mst_rompu.edges(data=True)) + min_secours_cost, 2
        )

    return {
        "result": {
            "impact_acm": True,
            "troncon_en_panne": {"u": u_node, "v": v_node},
            "raccordement_possible": raccordement_possible,
            "troncon_secours": troncon_secours,
            "surcout": round(min_secours_cost - G_fibre[u_node][v_node].get(weight_attr, 1.0), 2) if raccordement_possible else None,
            "nouveau_cout_total": nouveau_cout_total
        }
    }