import networkx as nx
from app.routers.api import load_networkx_graph_from_csv


def analyser_indicateurs_reseau(view: str = "routier"):
    """
    Exécute les 5 indicateurs d'analyse globale du réseau.
    - Détection automatique des casernes (type == 'caserne' ou fallback).
    - Accessibilité par BFS depuis l'ensemble des casernes.
    - Composantes connexes de la fibre par DFS.
    - Détection des cycles orientés par DFS / Tri topologique.
    - Identification des sites isolés (degré 0) et non atteignables.
    """
    print("[DEBUG_ANALYSIS] Début de l'analyse globale du réseau...")

    G_routier = load_networkx_graph_from_csv("routier")  # DiGraph (orienté)
    G_fibre = load_networkx_graph_from_csv("fibre")      # Graph (non orienté)

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

    # 1. Détection automatique des casernes (type == 'caserne' ou fallback sur les 2 premiers nœuds)
    casernes = [
        n for n, d in G_routier.nodes(data=True)
        if str(d.get('type', '')).lower() == 'caserne'
    ]
    if not casernes:
        nodes_list = list(G_routier.nodes)
        casernes = nodes_list[:2] if len(nodes_list) >= 2 else nodes_list

    # --- INDICATEUR 1 : Sites accessibles depuis les casernes (BFS) ---
    sites_accessibles = set()
    for caserne in casernes:
        if caserne in G_routier:
            accessibles = nx.descendants(G_routier, caserne)
            accessibles.add(caserne)
            sites_accessibles.update(accessibles)

    # --- INDICATEUR 2 : Composantes connexes du réseau fibre (DFS) ---
    composantes_fibre = list(nx.connected_components(G_fibre)) if len(G_fibre.nodes) > 0 else []

    # --- INDICATEUR 4 : Cycles orientés dans le réseau routier (DFS) ---
    cycles_detectes = not nx.is_directed_acyclic_graph(G_routier)

    # --- INDICATEUR 5 : Sites isolés & Sites non atteignables ---
    tous_les_sites = set(G_routier.nodes)

    # Sites isolés au sens strict (aucun arc entrant ni sortant)
    sites_isoles = [n for n in G_routier.nodes if G_routier.degree(n) == 0]

    # Sites non atteignables depuis AUCUNE des casernes de référence
    sites_non_atteignables = list(tous_les_sites - sites_accessibles)

    print("[DEBUG_ANALYSIS] Analyse globale terminée avec succès.")

    return {
        "casernes_reference": casernes,
        "nb_sites_accessibles": len(sites_accessibles),
        "accessibilite_casernes": list(sites_accessibles),
        "nb_composantes_fibre": len(composantes_fibre),
        "composantes_fibre": [list(c) for c in composantes_fibre],
        "cycles_orientes": cycles_detectes,
        "sites_isoles": sites_isoles,
        "sites_non_atteignables": sites_non_atteignables
    }