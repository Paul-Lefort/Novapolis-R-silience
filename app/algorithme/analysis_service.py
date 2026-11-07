import networkx as nx


def analyser_indicateurs_reseau(G_routier: nx.DiGraph, G_fibre: nx.Graph, casernes: list):
    """
    Exécute les 5 indicateurs exigés par le cahier des charges en utilisant DFS et BFS.
    """

    # 1. Sites accessibles depuis les casernes (Accessibilité orientée via BFS/DFS)
    sites_accessibles = set()
    for caserne in casernes:
        if caserne in G_routier:
            # nx.single_source_shortest_path_length utilise un BFS orienté
            accessibles = nx.single_source_shortest_path_length(G_routier, source=caserne).keys()
            sites_accessibles.update(accessibles)

    # 2. Composantes connexes du réseau fibre (Graphe non orienté)
    composantes_fibre = list(nx.connected_components(G_fibre))

    # 3. Itinéraire minimisant le nombre d'arcs (BFS non pondéré)
    def trouver_chemin_min_arcs(start, target):
        try:
            return nx.shortest_path(G_routier, source=start, target=target, weight=None)
        except nx.NetworkXNoPath:
            return []

    # 4. Détection des cycles orientés dans le réseau routier
    cycles_detectes = False
    try:
        nx.find_cycle(G_routier, orientation="original")
        cycles_detectes = True
    except nx.NetworkXNoException:
        cycles_detectes = False

    # 5. Sites isolés (degré 0) et non atteignables depuis les casernes
    tous_les_sites = set(G_routier.nodes)
    sites_isoles = [n for n, d in G_routier.degree() if d == 0]
    sites_non_atteignables = list(tous_les_sites - sites_accessibles)

    return {
        "accessibilite_casernes": list(sites_accessibles),
        "composantes_fibre": [list(c) for c in composantes_fibre],
        "cycles_orientes": cycles_detectes,
        "sites_isoles": sites_isoles,
        "sites_non_atteignables": sites_non_atteignables,
        "fonction_chemin_arcs": trouver_chemin_min_arcs
    }