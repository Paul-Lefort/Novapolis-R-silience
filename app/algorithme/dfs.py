from .common import prepare_graph, event, make_response


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    start = graph.get("start")
    if start not in adj:
        raise ValueError("Indiquez un sommet de départ existant dans 'start'.")

    visited = {n: False for n in nodes}
    parent = {n: None for n in nodes}
    steps = []

    def dfs(u):
        visited[u] = True
        steps.append(
            event("visit", "Visite du sommet", f"Visite récursive de {u}.", current_node=u, visited=visited.copy()))
        for v, eid, w in adj[u]:
            if not visited[v]:
                parent[v] = u
                steps.append(
                    event("discover", "Arête explorée", f"Traversée de l'arête {eid} vers {v}.", current_node=u,
                          candidate_node=v, active_edge=eid, visited=visited.copy()))
                dfs(v)
            else:
                steps.append(
                    event("check", "Arête ignorée", f"Sommet {v} déjà visité.", current_node=u, candidate_node=v,
                          active_edge=eid, visited=visited.copy()))

    steps.append(event("initialize", "Initialisation DFS", f"Début du DFS depuis {start}.", current_node=start,
                       visited=visited.copy()))
    dfs(start)
    steps.append(event("complete", "DFS Terminé", "Exploration en profondeur terminée.", visited=visited.copy()))
    return make_response(graph, steps, {"visited": visited, "parent": parent})