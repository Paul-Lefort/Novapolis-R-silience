"""
Parcours de graphes écrits à la main (sans networkx) : BFS et DFS itératifs.

Un graphe est représenté par une liste d'adjacence : {sommet: [voisins, ...]}.
Tous les sommets doivent figurer comme clés (voir `adjacency`).

Utilisation dans le projet :
  1. sites accessibles depuis une ou plusieurs casernes  -> reachable_from (BFS multi-sources)
  2. composantes connexes du réseau de fibre             -> connected_components (DFS)
  3. itinéraire minimisant le nombre d'arcs              -> bfs_path (BFS)
  4. cycles orientés du réseau routier                   -> find_directed_cycle (DFS à 3 couleurs)
  5. sites isolés / non atteignables                     -> degrés + reachable_from
"""
from collections import deque


def adjacency(G, directed=None):
    """Convertit un graphe networkx en liste d'adjacence (tous les sommets présents)."""
    directed = G.is_directed() if directed is None else directed
    if directed:
        return {n: list(G.successors(n)) for n in G.nodes}
    return {n: list(G.neighbors(n)) for n in G.nodes}


def undirected_view(adj):
    """Liste d'adjacence où chaque arc est aussi pris dans l'autre sens (connexité faible)."""
    und = {n: set(vs) for n, vs in adj.items()}
    for u, vs in adj.items():
        for v in vs:
            und.setdefault(v, set()).add(u)
    return {n: list(vs) for n, vs in und.items()}


# ---------------------------------------------------------------- BFS

def bfs(adj, source):
    """Parcours en largeur. Renvoie (ordre de visite, parent, profondeur en arcs)."""
    order, parent, depth = [], {source: None}, {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in adj.get(u, []):
            if v not in parent:
                parent[v] = u
                depth[v] = depth[u] + 1
                queue.append(v)
    return order, parent, depth


def bfs_path(adj, source, target):
    """Chemin minimisant le nombre d'arcs (None s'il n'existe pas)."""
    if source == target:
        return [source]
    _, parent, _ = bfs(adj, source)
    if target not in parent:
        return None
    path, node = [], target
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


def reachable_from(adj, sources):
    """BFS multi-sources : ensemble des sommets atteignables depuis au moins une source."""
    seen = set(s for s in sources if s in adj)
    queue = deque(seen)
    while queue:
        u = queue.popleft()
        for v in adj.get(u, []):
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


# ---------------------------------------------------------------- DFS

def dfs(adj, source):
    """Parcours en profondeur itératif (ordre préfixe)."""
    order, seen = [], {source}
    stack = [(source, iter(adj.get(source, [])))]
    order.append(source)
    while stack:
        node, it = stack[-1]
        for nxt in it:
            if nxt not in seen:
                seen.add(nxt)
                order.append(nxt)
                stack.append((nxt, iter(adj.get(nxt, []))))
                break
        else:
            stack.pop()
    return order


def connected_components(adj):
    """Composantes connexes d'un graphe NON orienté, par DFS. Triées par taille décroissante."""
    seen, components = set(), []
    for start in adj:
        if start in seen:
            continue
        comp = dfs(adj, start)
        seen.update(comp)
        components.append(comp)
    components.sort(key=len, reverse=True)
    return components


def find_directed_cycle(adj):
    """
    Détecte un cycle orienté par DFS à trois couleurs (blanc / gris / noir).
    Un arc vers un sommet « gris » (en cours de visite) ferme un cycle.
    Renvoie la liste [a, b, ..., a] ou None si le graphe est acyclique.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}
    parent = {}
    for root in adj:
        if color[root] != WHITE:
            continue
        color[root] = GREY
        stack = [(root, iter(adj[root]))]
        while stack:
            node, it = stack[-1]
            for nxt in it:
                state = color.get(nxt, WHITE)
                if state == WHITE:
                    color[nxt] = GREY
                    parent[nxt] = node
                    stack.append((nxt, iter(adj.get(nxt, []))))
                    break
                if state == GREY:
                    cycle, cur = [node], node
                    while cur != nxt:
                        cur = parent[cur]
                        cycle.append(cur)
                    cycle.reverse()
                    cycle.append(nxt)
                    return cycle
            else:
                color[node] = BLACK
                stack.pop()
    return None


def strongly_connected_components(adj):
    """Composantes fortement connexes (Kosaraju, deux DFS itératifs)."""
    order, seen = [], set()
    for s in adj:
        if s in seen:
            continue
        seen.add(s)
        stack = [(s, iter(adj[s]))]
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, iter(adj.get(nxt, []))))
                    break
            else:
                order.append(node)
                stack.pop()

    reverse = {n: [] for n in adj}
    for u, vs in adj.items():
        for v in vs:
            reverse.setdefault(v, []).append(u)

    components, seen = [], set()
    for s in reversed(order):
        if s in seen:
            continue
        seen.add(s)
        comp, stack = [], [s]
        while stack:
            n = stack.pop()
            comp.append(n)
            for m in reverse.get(n, []):
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        components.append(comp)
    components.sort(key=len, reverse=True)
    return components
