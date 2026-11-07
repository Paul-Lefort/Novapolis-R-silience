import io
import pandas as pd
import networkx as nx
from fastapi import APIRouter, Form, File, UploadFile
from typing import Optional, Dict, Any

from app.routers.analysis import reconstruct_path_details
from app.routers.api import load_networkx_graph_from_csv

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def analyser_indicateurs_reseau(view: str = "routier"):
    """
    Exécute les 5 indicateurs d'analyse globale du réseau en partant de tous
    les sommets et en soustrayant au fur et à mesure les sites atteints par chaque caserne.
    """
    print("[DEBUG_ANALYSIS] Début de l'analyse globale du réseau...")

    G_routier = load_networkx_graph_from_csv("routier")  # DiGraph
    G_fibre = load_networkx_graph_from_csv("fibre")  # Graph

    if len(G_routier.nodes) == 0:
        return {
            "casernes_reference": [],
            "nb_sites_accessibles": 0,
            "accessibilite_casernes": [],
            "nb_composantes_fibre": 0,
            "composantes_fibre": [],
            "cycles_orientes": False,
            "sites_isoles": [],
            "sites_non_atteignables": []
        }

    # 1. Identification robuste et sécurisée de TOUTES les casernes
    found_casernes = []
    for n, d in G_routier.nodes(data=True):
        site_type = str(d.get('type', '')).lower()
        if 'caserne' in site_type:
            found_casernes.append(n)

    if not found_casernes:
        nodes_list = list(G_routier.nodes)
        found_casernes = nodes_list[:2] if len(nodes_list) >= 2 else nodes_list

    casernes = found_casernes
    print(f"[DEBUG_ANALYSIS] Casernes détectées : {len(casernes)} (IDs : {casernes})")

    # 2. Approche par soustraction (via le graphe non orienté pour éviter les blocages de sens uniques)
    G_non_oriente = G_routier.to_undirected()
    sites_non_atteignables = set(G_routier.nodes)

    for caserne in casernes:
        if caserne in G_non_oriente:
            try:
                accessibles = set(nx.node_connected_component(G_non_oriente, caserne))
            except Exception:
                accessibles = set(nx.single_source_shortest_path_length(G_non_oriente, caserne).keys())

            sites_non_atteignables.difference_update(accessibles)

    tous_les_sites = set(G_routier.nodes)
    sites_accessibles = tous_les_sites - sites_non_atteignables
    sites_non_atteignables_list = list(sites_non_atteignables)

    # 3. Autres indicateurs (Fibre, Cycles, Isolation)
    composantes_fibre = list(nx.connected_components(G_fibre)) if len(G_fibre.nodes) > 0 else []
    cycles_detectes = not nx.is_directed_acyclic_graph(G_routier)
    sites_isoles = [n for n in G_routier.nodes if G_routier.degree(n) == 0]

    print(
        f"[DEBUG_ANALYSIS] Total casernes : {len(casernes)} | Sites accessibles : {len(sites_accessibles)} | Non atteignables : {len(sites_non_atteignables_list)}")

    return {
        "casernes_reference": casernes,
        "nb_sites_accessibles": len(sites_accessibles),
        "accessibilite_casernes": list(sites_accessibles),
        "nb_composantes_fibre": len(composantes_fibre),
        "composantes_fibre": [list(c) for c in composantes_fibre],
        "cycles_orientes": cycles_detectes,
        "sites_isoles": sites_isoles,
        "sites_non_atteignables": sites_non_atteignables_list
    }
@router.get("/report")
def get_analysis_report(view: str = "routier"):
    data = analyser_indicateurs_reseau(view)
    return {"result": data}


@router.post("/calcul-intervention")
async def calcul_intervention_endpoint(
        start: str = Form(...),
        target: str = Form(...),
        view: str = Form("routier"),
        manual_arcs: Optional[str] = Form(None),
        scenario_file: Optional[UploadFile] = File(None)
):
    G_base = load_networkx_graph_from_csv(view)

    start_node = int(start) if str(start).isdigit() else start
    target_node = int(target) if str(target).isdigit() else target

    if start_node not in G_base or target_node not in G_base:
        return {"result": {"accessible": False, "message": "Sommets introuvables dans le graphe."}}

    # 1. Avant perturbation
    try:
        path_init = nx.dijkstra_path(G_base, source=start_node, target=target_node, weight="weight")
        res_avant = reconstruct_path_details(G_base, path_init, weight_attr="weight")
        res_avant["accessible"] = True
    except nx.NetworkXNoPath:
        res_avant = {"accessible": False, "cost": None, "nb_arcs": 0, "path": []}

    # 2. Construction du graphe perturbé
    G_perturbe = G_base.copy()
    arcs_fermes_appliques = []

    # Application du scénario CSV
    if scenario_file:
        try:
            contents = await scenario_file.read()
            df = pd.read_csv(io.BytesIO(contents))
            for _, row in df.iterrows():
                u, v = row['u'], row['v']
                u = int(u) if str(u).isdigit() else u
                v = int(v) if str(v).isdigit() else v
                action = str(row.get('action', 'fermer')).lower()

                if G_perturbe.has_edge(u, v):
                    if action in ['fermer', 'desactiver']:
                        G_perturbe.remove_edge(u, v)
                        arcs_fermes_appliques.append([u, v])
                    elif action == 'modifier' and 'nouveau_temps_pointe' in row:
                        G_perturbe[u][v]['weight'] = float(row['nouveau_temps_pointe'])
        except Exception as exc:
            print(f"[ERROR SCENARIO UPLOAD] {exc}")

    # Saisie manuelle d'arcs (ex: "3->16, 8->10")
    if manual_arcs:
        pairs = [p.strip() for p in manual_arcs.split(',') if '->' in p]
        for pair in pairs:
            parts = pair.split('->')
            u = int(parts[0].strip()) if parts[0].strip().isdigit() else parts[0].strip()
            v = int(parts[1].strip()) if parts[1].strip().isdigit() else parts[1].strip()
            if G_perturbe.has_edge(u, v):
                G_perturbe.remove_edge(u, v)
                arcs_fermes_appliques.append([u, v])

    # 3. Après perturbation
    try:
        path_perturbe = nx.dijkstra_path(G_perturbe, source=start_node, target=target_node, weight="weight")
        res_apres = reconstruct_path_details(G_perturbe, path_perturbe, weight_attr="weight")
        res_apres["accessible"] = True
    except nx.NetworkXNoPath:
        res_apres = {"accessible": False, "cost": None, "nb_arcs": 0, "path": []}

    # 4. Retards
    retard_absolu = None
    retard_relatif = None
    if res_avant["accessible"] and res_apres["accessible"]:
        retard_absolu = round(res_apres["cost"] - res_avant["cost"], 2)
        if res_avant["cost"] > 0:
            retard_relatif = round((retard_absolu / res_avant["cost"]) * 100, 2)
        else:
            retard_relatif = 0.0

    return {
        "result": {
            "start": start_node,
            "target": target_node,
            "arcs_fermes_appliques": arcs_fermes_appliques,
            "avant_perturbation": res_avant,
            "apres_perturbation": res_apres,
            "degradation": {
                "retard_absolu": retard_absolu,
                "retard_relatif_pct": retard_relatif
            }
        }
    }