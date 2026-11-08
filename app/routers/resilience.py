import logging
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from typing import Optional

from app.algorithme.resilience_service import (
    acm_couts_egaux_service,
    calculer_intervention_service,
    comparer_algorithmes_service,
    evaluer_scenarios_service,
    generer_rapport_diagnostic,
)
from app.algorithme import shortest_paths as sp

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/resilience", tags=["resilience"])


@router.get("/report")
def rapport_diagnostic(view: str = Query("routier")):
    """Renvoie les indicateurs globaux d'accessibilité et de connectivité."""
    logger.info(f"[RESILIENCE] Génération du rapport de diagnostic (vue: {view})")
    try:
        data = generer_rapport_diagnostic(view)
        return {"result": data}
    except Exception as e:
        logger.error(f"[RESILIENCE] Erreur lors de la génération du rapport : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'analyse du réseau.")


@router.post("/intervention")
async def calcul_intervention(
        start: str = Form(...),
        target: str = Form(...),
        view: str = Form("routier"),
        algo: str = Form("dijkstra"),
        critere: str = Form("temps_normal"),
        manual_arcs: Optional[str] = Form(None),
        scenario_file: Optional[UploadFile] = File(None),
):
    """Calcule l'itinéraire de secours après application de perturbations."""
    logger.info(f"[RESILIENCE] Calcul intervention de {start} vers {target} via {algo}")

    if algo not in ("dijkstra", "bellman_ford", "floyd_warshall"):
        raise HTTPException(status_code=400, detail=f"Algorithme inconnu : {algo}")

    scenario_bytes = None
    if scenario_file:
        try:
            scenario_bytes = await scenario_file.read()
        except Exception as e:
            logger.error(f"[RESILIENCE] Erreur de lecture du fichier de scénario : {e}")
            raise HTTPException(status_code=400, detail="Fichier de scénario illisible.")

    try:
        result_data = calculer_intervention_service(start, target, view, algo, critere, manual_arcs, scenario_bytes)
        return {"result": result_data}
    except ValueError as ve:
        logger.warning(f"[RESILIENCE] Paramètre invalide : {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[RESILIENCE] Échec du calcul d'intervention : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du calcul.")


@router.get("/negative-cycle-tests")
def tests_circuits_absorbants():
    """Exécute les jeux de tests internes sur les circuits de poids négatif."""
    logger.info("[RESILIENCE] Exécution des tests de circuits absorbants")
    tests = sp.run_all_tests()
    return {"result": {"tests": tests, "tous_reussis": all(t["reussi"] for t in tests)}}


@router.get("/compare-algos")
def comparer_algorithmes(start: str, target: str, view: str = Query("routier"), critere: str = Query("temps_normal")):
    """Dijkstra, Bellman-Ford et Floyd-Warshall sur la même instance (+ BFS comme repère)."""
    logger.info(f"[RESILIENCE] Comparaison des algorithmes de {start} vers {target}")
    try:
        return {"result": comparer_algorithmes_service(start, target, view, critere)}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[RESILIENCE] Échec de la comparaison : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors de la comparaison.")


@router.get("/scenarios")
def evaluer_scenarios(
        nb_demandes: int = Query(30, ge=1, le=500),
        critere: str = Query("temps_normal"),
        axe: Optional[str] = Query(None, description="Arcs routiers à fermer, ex : 3->16,16->3"),
        troncon: Optional[str] = Query(None, description="Tronçon de fibre en panne, ex : 4-9"),
        types_sensibles: Optional[str] = Query(None, description="Types de sites sensibles, ex : hopital,ecole"),
):
    """Trois scénarios (normal, axe routier fermé, panne de fibre) sur les mêmes demandes."""
    logger.info(f"[RESILIENCE] Évaluation des scénarios ({nb_demandes} demandes, critère {critere})")
    try:
        return {"result": evaluer_scenarios_service(nb_demandes, critere, axe, troncon, types_sensibles)}
    except ValueError as ve:
        logger.warning(f"[RESILIENCE] Paramètre invalide : {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[RESILIENCE] Échec de l'évaluation des scénarios : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'évaluation des scénarios.")


@router.get("/fibre-ties")
def acm_a_couts_egaux():
    """Coûts égaux : pourquoi plusieurs arbres couvrants minimaux peuvent coexister."""
    logger.info("[RESILIENCE] Analyse des coûts égaux de la fibre")
    try:
        return {"result": acm_couts_egaux_service()}
    except Exception as e:
        logger.error(f"[RESILIENCE] Échec de l'analyse des coûts égaux : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'analyse des coûts égaux.")