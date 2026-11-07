from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")

    distances = {n: float("inf") for n in nodes}
    distances[start] = 0
    parent = {n: None for n in nodes}
    steps = []

    def visible_distances():
        return {n: (value if value != float("inf") else None)
                for n, value in distances.items()}

    # prepare_graph valide un graphe non orienté : chaque arête représente
    # deux arcs pour les relaxations de Bellman-Ford.
    arcs = []
    for edge in edges:
        arcs.append((edge["source"], edge["target"], edge["weight"], edge["id"]))
        arcs.append((edge["target"], edge["source"], edge["weight"], edge["id"]))

    steps.append(event(
        "initialize", "Initialisation Bellman-Ford",
        f"Initialisation des distances depuis le sommet {start}.",
        current_node=start, distances=visible_distances(),
        parent=parent.copy(), active_edge=None, iteration=0
    ))

    for iteration in range(1, len(nodes)):
        updated = False
        steps.append(event(
            "iteration", f"Itération {iteration}",
            f"Début de l'itération {iteration} de relaxation des arêtes.",
            distances=visible_distances(), parent=parent.copy(),
            active_edge=None, iteration=iteration
        ))

        for u, v, weight, eid in arcs:
            steps.append(event(
                "check", "Vérification de l'arc",
                f"Vérification de l'arc {u} → {v} (arête {eid}).",
                current_node=u, candidate_node=v, active_edge=eid,
                distances=visible_distances(), parent=parent.copy(),
                iteration=iteration
            ))

            if distances[u] != float("inf") and distances[u] + weight < distances[v]:
                old_distance = distances[v]
                distances[v] = distances[u] + weight
                parent[v] = u
                updated = True
                steps.append(event(
                    "relax", "Distance améliorée",
                    f"La distance de {v} passe de {old_distance} à {distances[v]} via {u}.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    distances=visible_distances(), parent=parent.copy(),
                    iteration=iteration
                ))
            else:
                steps.append(event(
                    "skip", "Aucune amélioration",
                    f"Aucune amélioration de la distance vers {v}.",
                    current_node=u, candidate_node=v, active_edge=eid,
                    distances=visible_distances(), parent=parent.copy(),
                    iteration=iteration
                ))

        if not updated:
            steps.append(event(
                "early_stop", "Arrêt anticipé",
                "Aucune distance n'a été améliorée. L'algorithme peut s'arrêter.",
                distances=visible_distances(), parent=parent.copy(),
                iteration=iteration
            ))
            break

    negative_cycle = False
    for u, v, weight, eid in arcs:
        if distances[u] != float("inf") and distances[u] + weight < distances[v]:
            negative_cycle = True
            steps.append(event(
                "negative_cycle", "Cycle négatif détecté",
                f"Un cycle de poids négatif est détecté via l'arête {eid} ({u} → {v}).",
                current_node=u, candidate_node=v, active_edge=eid,
                distances=visible_distances(), parent=parent.copy()
            ))
            break

    if not negative_cycle:
        steps.append(event(
            "complete", "Bellman-Ford terminé",
            "Aucun cycle de poids négatif accessible depuis le sommet de départ.",
            distances=visible_distances(), parent=parent.copy()
        ))

    return make_response(graph, steps, {
        "distances": visible_distances(),
        "parent": parent,
        "negative_cycle": negative_cycle
    })
