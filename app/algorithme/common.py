import networkx as nx

def prepare_networkx_graph(graph_data, network_type="routier"):
    """
    Prépare un graphe NetworkX à partir des données du payload JSON.
    - routier -> Graphe orienté (nx.DiGraph), filtre les travaux et saturations si besoin.
    - fibre -> Graphe non orienté (nx.Graph), filtre les maintenances et déploiements.
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    start = graph_data.get("start")
    target = graph_data.get("target")

    # Choix du type de graphe : orienté pour la route, non orienté pour la fibre
    if network_type == "routier":
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    G.add_nodes_from(nodes)

    for e in edges:
        u = e.get("source")
        v = e.get("target")
        weight = float(e.get("weight", 1))
        statut = str(e.get("statut", "")).lower()

        # Exclusion stricte des éléments en travaux, maintenance ou déploiement
        if any(kw in statut for kw in ["travaux", "maintenance", "deploiement"]):
            continue

        if u in G and v in G:
            # Évite d'écraser un poids si l'arête existe déjà, ou prend le minimum
            if G.has_edge(u, v):
                if weight < G[u][v].get("weight", float("inf")):
                    G[u][v]["weight"] = weight
            else:
                G.add_edge(u, v, weight=weight, id=e.get("id"))

    return G, start, target

def event(step_type, title, description, **kwargs):
    """Génère un dictionnaire standardisé pour une étape de l'algorithme."""
    base = {
        "type": step_type,
        "title": title,
        "description": description
    }
    base.update(kwargs)
    return base

def make_response(graph_data, steps, result_data):
    """Formate la réponse finale pour l'API FastAPI."""
    return {
        "step_count": len(steps),
        "steps": steps,
        "result": result_data
    }