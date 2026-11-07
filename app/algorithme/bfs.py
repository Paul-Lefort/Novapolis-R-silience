from collections import deque
from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")

    visited = {n: False for n in nodes}
    queue = deque([start])
    visited[start] = True
    parent = {n: None for n in nodes}
    steps = []

    steps.append(event("initialize", "Initialisation BFS",
                       f"Départ de la recherche en largeur (BFS) depuis {start}.",
                       current_node=start, queue=list(queue), visited=visited.copy(), active_edge=None))

    while queue:
        u = queue.popleft()
        steps.append(event("visit", "Exploration du sommet",
                           f"Visite du sommet {u}.",
                           current_node=u, queue=list(queue), visited=visited.copy(), active_edge=None))

        for v, eid, w in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                queue.append(v)
                steps.append(event("discover", "Sommet découvert",
                                   f"Découverte du sommet {v} depuis {u} via l'arête {eid}.",
                                   current_node=u, candidate_node=v, active_edge=eid, queue=list(queue),
                                   visited=visited.copy()))
            else:
                steps.append(event("check", "Arête ignorée",
                                   f"Sommet {v} déjà visité.",
                                   current_node=u, candidate_node=v, active_edge=eid, queue=list(queue),
                                   visited=visited.copy()))

    steps.append(event("complete", "BFS Terminé", "Exploration en largeur terminée.", visited=visited.copy()))
    return make_response(graph, steps, {"visited": visited, "parent": parent})