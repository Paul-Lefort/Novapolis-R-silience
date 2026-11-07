import networkx as nx
from .common import prepare_networkx_graph, event, make_response


def run(graph_data):
    G, start, _ = prepare_networkx_graph(graph_data, network_type="fibre")

    if len(G.nodes) == 0:
        raise ValueError("Le graphe est vide.")

    # Si aucun sommet de départ n'est fourni, on prend le premier nœud du graphe par défaut
    if not start or start not in G:
        start = list(G.nodes)[0]

    steps = []
    steps.append(event("initialize", "Initialisation de Prim", f"Démarrage de l'arbre à partir du sommet {start}."))

    try:
        # Utilisation de NetworkX pour Prim
        mst_g = nx.minimum_spanning_tree(G, algorithm="prim", weight="weight")

        # Extraction des arêtes et du coût total
        total_weight = sum(d.get("weight", 0) for u, v, d in mst_g.edges(data=True))

        # Parcours en profondeur (DFS) ou liste des sommets pour l'affichage visuel
        path_nodes = list(nx.dfs_preorder_nodes(mst_g, source=start))

        steps.append(event("complete", "MST Prim calculé",
                           f"Arbre couvrant minimum de Prim généré (coût total : {total_weight})."))

        return make_response(graph_data, steps, {
            "path": path_nodes,
            "cost": total_weight,
            "mst_edges": [{"source": u, "target": v, "weight": d.get("weight")} for u, v, d in mst_g.edges(data=True)]
        })
    except Exception as exc:
        raise ValueError(f"Erreur lors du calcul de Prim : {str(exc)}")