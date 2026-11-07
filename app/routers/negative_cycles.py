import networkx as nx
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List
from app.routers.api import load_networkx_graph_from_csv

router = APIRouter(prefix="/api/analysis", tags=["negative-cycles"])


@router.get("/detect-absorbent-cycles")
def detect_absorbent_cycles(start: str = Query(...), view: str = Query("routier")):
    """
    Module 3 : Détection de circuits absorbants (poids négatifs) et vérification
    de leur accessibilité depuis la source spécifiée.
    """
    G = load_networkx_graph_from_csv(view)

    start_node = int(start) if str(start).isdigit() else start
    if start_node not in G:
        raise HTTPException(status_code=400, detail=f"Sommet de départ ({start_node}) introuvable.")

    has_negative_cycle = False
    cycle_nodes = []
    accessible_from_source = False
    method_used = "bellman_ford"

    # 1. Utilisation de Bellman-Ford pour détecter les cycles absorbants
    try:
        # networkx.bellman_ford_predecessor_and_distance lève NetworkXUnbounded
        # s'il y a un circuit absorbant accessible depuis la source.
        nx.bellman_ford_predecessor_and_distance(G, source=start_node, weight="weight")
    except nx.NetworkXUnbounded:
        has_negative_cycle = True
        accessible_from_source = True
        method_used = "Bellman-Ford (Accessible depuis la source)"
    except Exception:
        pass

    # 2. Si non détecté depuis la source, vérification globale sur tout le graphe
    if not has_negative_cycle:
        for node in G.nodes():
            try:
                nx.bellman_ford_predecessor_and_distance(G, source=node, weight="weight")
            except nx.NetworkXUnbounded:
                has_negative_cycle = True
                accessible_from_source = False  # Existe dans le graphe mais pas depuis cette source
                method_used = "Bellman-Ford (Inaccessible depuis la source)"
                break
            except Exception:
                pass

    # 3. Vérification complémentaire avec Floyd-Warshall (diagonales < 0)
    if not has_negative_cycle:
        try:
            # Floyd-Warshall détecte les cycles négatifs si distance(u, u) < 0
            distances = nx.floyd_warshall(G, weight="weight")
            for u in G.nodes():
                if u in distances and distances[u][u] < 0:
                    has_negative_cycle = True
                    method_used = "Floyd-Warshall (Matrice des distances)"
                    # Vérifier si u est accessible depuis start_node
                    if nx.has_path(G, start_node, u):
                        accessible_from_source = True
                    break
        except Exception:
            pass

    return {
        "result": {
            "has_negative_cycle": has_negative_cycle,
            "accessible_from_source": accessible_from_source if has_negative_cycle else None,
            "method_used": method_used if has_negative_cycle else "Aucun circuit absorbant détecté",
            "message": (
                f"Attention : Circuit absorbant détecté ({method_used}). Les distances peuvent être diminuées indéfiniment."
                if has_negative_cycle else
                "Réseau stable : Aucun circuit absorbant détecté. Les temps/coûts sont valides."
            )
        }
    }