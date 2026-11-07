
from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)

    start = graph.get("start")

    if start not in adj:
        raise ValueError(
            "Indiquez un sommet de départ existant dans 'start'."
        )

    # Initialisation des distances et des prédécesseurs
    distances = {n: float("inf") for n in nodes}
    distances[start] = 0

    parent = {n: None for n in nodes}
    steps = []

    steps.append(
        event(
            "initialize",
            "Initialisation Bellman-Ford",
            f"Initialisation des distances depuis le sommet {start}.",
            current_node=start,
            distances=distances.copy(),
            parent=parent.copy(),
            active_edge=None,
            iteration=0
        )
    )

    # Relaxation des arêtes pendant |V| - 1 itérations maximum
    for iteration in range(1, len(nodes)):

        updated = False

        steps.append(
            event(
                "iteration",
                f"Itération {iteration}",
                f"Début de l'itération {iteration} de relaxation des arêtes.",
                distances=distances.copy(),
                parent=parent.copy(),
                active_edge=None,
                iteration=iteration
            )
        )

        for edge in edges:

            # Compatibilité avec les arêtes orientées
            u = edge["source"]
            v = edge["target"]
            weight = edge["weight"]
            eid = edge["id"]

            steps.append(
                event(
                    "check",
                    "Vérification de l'arête",
                    f"Vérification de l'arête {eid} : {u} → {v}.",
                    current_node=u,
                    candidate_node=v,
                    active_edge=eid,
                    distances=distances.copy(),
                    parent=parent.copy(),
                    iteration=iteration
                )
            )

            if distances[u] != float("inf"):

                new_distance = distances[u] + weight

                if new_distance < distances[v]:

                    old_distance = distances[v]

                    distances[v] = new_distance
                    parent[v] = u
                    updated = True

                    steps.append(
                        event(
                            "relax",
                            "Distance améliorée",
                            f"La distance de {v} passe de {old_distance} à {new_distance} via {u}.",
                            current_node=u,
                            candidate_node=v,
                            active_edge=eid,
                            distances=distances.copy(),
                            parent=parent.copy(),
                            iteration=iteration
                        )
                    )

                else:

                    steps.append(
                        event(
                            "skip",
                            "Aucune amélioration",
                            f"Aucune amélioration de la distance vers {v}.",
                            current_node=u,
                            candidate_node=v,
                            active_edge=eid,
                            distances=distances.copy(),
                            parent=parent.copy(),
                            iteration=iteration
                        )
                    )

        # Arrêt anticipé si aucune distance n'a été améliorée
        if not updated:

            steps.append(
                event(
                    "early_stop",
                    "Arrêt anticipé",
                    "Aucune distance n'a été améliorée. L'algorithme peut s'arrêter.",
                    distances=distances.copy(),
                    parent=parent.copy(),
                    iteration=iteration
                )
            )

            break

    # Détection des cycles de poids négatif accessibles depuis start
    negative_cycle = None

    for edge in edges:

        u = edge["source"]
        v = edge["target"]
        weight = edge["weight"]
        eid = edge["id"]

        if (
            distances[u] != float("inf")
            and distances[u] + weight < distances[v]
        ):

            negative_cycle = True

            steps.append(
                event(
                    "negative_cycle",
                    "Cycle négatif détecté",
                    f"Un cycle de poids négatif est détecté via l'arête {eid} : {u} → {v}.",
                    current_node=u,
                    candidate_node=v,
                    active_edge=eid,
                    distances=distances.copy(),
                    parent=parent.copy()
                )
            )

            break

    if negative_cycle is None:
        negative_cycle = False

        steps.append(
            event(
                "complete",
                "Bellman-Ford terminé",
                "Aucun cycle de poids négatif accessible depuis le sommet de départ.",
                distances=distances.copy(),
                parent=parent.copy()
            )
        )

    return make_response(
        graph,
        steps,
        {
            "distances": distances,
            "parent": parent,
            "negative_cycle": negative_cycle
        }
    )
