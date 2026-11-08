"""
Plus courts chemins écrits à la main : Dijkstra (référence), Bellman-Ford, Floyd-Warshall.

Bellman-Ford et Floyd-Warshall détectent les circuits absorbants (de poids total négatif)
et distinguent trois états pour chaque distance :
    "fini"         -> valeur numérique fiable
    "moins_infini" -> peut être diminuée indéfiniment (circuit absorbant sur un chemin source -> sommet)
    "inaccessible" -> aucun chemin
Une distance « moins_infini » n'est jamais renvoyée comme un nombre fini.
"""
import heapq
import time

from .traversal import reachable_from

INF = float("inf")


def _state(value):
    if value == INF:
        return "inaccessible"
    if value == -INF:
        return "moins_infini"
    return "fini"


def describe(value):
    """{'etat': ..., 'valeur': nombre ou None} : sérialisable en JSON."""
    etat = _state(value)
    return {"etat": etat, "valeur": round(value, 6) if etat == "fini" else None}


def _rebuild(pred, source, target):
    path, node, guard = [], target, 0
    while node is not None and guard <= len(pred) + 1:
        path.append(node)
        if node == source:
            return path[::-1]
        node = pred.get(node)
        guard += 1
    return None


# ---------------------------------------------------------------- Dijkstra

def dijkstra(nodes, edges, source):
    """Dijkstra avec tas binaire. Poids strictement non négatifs exigés."""
    adj = {n: [] for n in nodes}
    for u, v, w in edges:
        if w < 0:
            raise ValueError("Dijkstra n'accepte pas les poids négatifs (utiliser Bellman-Ford).")
        adj[u].append((v, w))

    dist = {n: INF for n in nodes}
    pred = {n: None for n in nodes}
    dist[source] = 0
    heap = [(0, 0, source)]
    counter = 1  # départage les égalités sans comparer les sommets
    while heap:
        d, _, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v], pred[v] = nd, u
                heapq.heappush(heap, (nd, counter, v))
                counter += 1
    return dist, pred


# ---------------------------------------------------------------- Bellman-Ford

def bellman_ford(nodes, edges, source):
    """
    Renvoie (dist, pred, info). dist[v] vaut -inf si un circuit absorbant est accessible
    depuis la source ET permet d'atteindre v.
    info = {circuit_accessible: bool, circuit: [sommets] ou None}
    """
    dist = {n: INF for n in nodes}
    pred = {n: None for n in nodes}
    dist[source] = 0

    for _ in range(len(dist) - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v], pred[v] = dist[u] + w, u
                changed = True
        if not changed:
            break

    # |V|-ième passe : toute relaxation possible révèle un circuit absorbant accessible
    witnesses = [v for u, v, w in edges if dist[u] != INF and dist[u] + w < dist[v]]
    info = {"circuit_accessible": bool(witnesses), "circuit": None}

    if witnesses:
        adj = {n: [] for n in nodes}
        for u, v, _ in edges:
            adj[u].append(v)
        for n in reachable_from(adj, witnesses):
            dist[n] = -INF
        info["circuit"] = _extract_cycle(pred, witnesses[0], len(dist))
    return dist, pred, info


def _extract_cycle(pred, start, n):
    node = start
    for _ in range(n):            # n pas en arrière : on est forcément dans le circuit
        if pred.get(node) is None:
            return None
        node = pred[node]
    cycle, cur = [node], pred[node]
    while cur is not None and cur != node:
        cycle.append(cur)
        cur = pred[cur]
    cycle.append(node)
    return cycle[::-1]


def has_negative_cycle(nodes, edges):
    """Circuit absorbant n'importe où dans le graphe (source virtuelle reliée à tous à coût 0)."""
    dist = {n: 0 for n in nodes}
    pred = {n: None for n in nodes}
    last = None
    for _ in range(len(dist)):
        last = None
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v], pred[v] = dist[u] + w, u
                last = v
        if last is None:
            return False, None
    return True, _extract_cycle(pred, last, len(dist))


# ---------------------------------------------------------------- Floyd-Warshall

def floyd_warshall(nodes, edges):
    """
    Renvoie (dist, nxt, idx, negatifs) :
      dist[i][j] matrice des distances, nxt[i][j] successeur pour reconstruire le chemin,
      negatifs = indices des sommets situés sur un circuit absorbant (dist[i][i] < 0).
    """
    nodes = list(nodes)
    n = len(nodes)
    idx = {v: i for i, v in enumerate(nodes)}
    dist = [[INF] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        i, j = idx[u], idx[v]
        if w < dist[i][j]:
            dist[i][j], nxt[i][j] = w, j

    for k in range(n):
        row_k = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == INF:
                continue
            row_i = dist[i]
            for j in range(n):
                cand = dik + row_k[j]
                if cand < row_i[j]:
                    row_i[j] = cand
                    nxt[i][j] = nxt[i][k]

    negatifs = [i for i in range(n) if dist[i][i] < 0]
    return dist, nxt, idx, nodes, negatifs


def fw_value(dist, negatifs, i, j):
    """Distance i -> j avec -inf si un circuit absorbant se trouve sur un chemin i -> k -> j."""
    if dist[i][j] == INF:
        return INF
    for k in negatifs:
        if dist[i][k] != INF and dist[k][j] != INF:
            return -INF
    return dist[i][j]


def fw_path(nxt, idx, nodes, source, target):
    i, j = idx[source], idx[target]
    if i == j:
        return [source]
    if nxt[i][j] is None:
        return None
    path, guard = [source], 0
    while i != j and guard <= len(nodes):
        i = nxt[i][j]
        path.append(nodes[i])
        guard += 1
    return path if i == j else None


# ---------------------------------------------------------------- Interface commune

def path_cost(edges_map, path):
    return sum(edges_map[(path[i], path[i + 1])] for i in range(len(path) - 1))


def solve(algo, nodes, edges, source, target, fw_max_nodes=250):
    """
    Exécute `algo` ('dijkstra' | 'bellman_ford' | 'floyd_warshall') et renvoie un dict uniforme :
      {algo, statut, accessible, cost, nb_arcs, path, temps_ms, remarque, circuit_absorbant}
    statut : 'ok' | 'inaccessible' | 'moins_infini' | 'ignore'
    """
    start = time.perf_counter()
    out = {"algo": algo, "statut": "ok", "accessible": False, "cost": None, "nb_arcs": 0,
           "path": [], "remarque": "", "circuit_absorbant": False}
    best = {}
    for u, v, w in edges:                      # arcs parallèles : on garde le moins cher
        if (u, v) not in best or w < best[(u, v)]:
            best[(u, v)] = w
    edges = [(u, v, w) for (u, v), w in best.items()]

    try:
        if algo == "dijkstra":
            dist, pred = dijkstra(nodes, edges, source)
            value, path = dist.get(target, INF), None
            if value != INF:
                path = _rebuild(pred, source, target)
        elif algo == "bellman_ford":
            dist, pred, info = bellman_ford(nodes, edges, source)
            value, path = dist.get(target, INF), None
            out["circuit_absorbant"] = info["circuit_accessible"]
            if _state(value) == "fini":
                path = _rebuild(pred, source, target)
        elif algo == "floyd_warshall":
            if len(list(nodes)) > fw_max_nodes:
                out.update(statut="ignore",
                           remarque=f"Ignoré : {len(list(nodes))} sommets > {fw_max_nodes} (complexité O(V³)).")
                out["temps_ms"] = 0.0
                return out
            dist, nxt, idx, names, negatifs = floyd_warshall(nodes, edges)
            value = fw_value(dist, negatifs, idx[source], idx[target])
            out["circuit_absorbant"] = any(dist[idx[source]][k] != INF for k in negatifs)
            path = fw_path(nxt, idx, names, source, target) if _state(value) == "fini" else None
        else:
            raise ValueError(f"Algorithme inconnu : {algo}")
    except ValueError as exc:
        out.update(statut="ignore", remarque=str(exc))
        out["temps_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return out

    etat = _state(value)
    if etat == "fini" and path:
        out.update(accessible=True, cost=round(value, 4), nb_arcs=len(path) - 1, path=path)
    elif etat == "moins_infini":
        out.update(statut="moins_infini",
                   remarque="Circuit absorbant accessible : la distance peut être diminuée indéfiniment, aucun coût fini.")
    else:
        out.update(statut="inaccessible")
    out["temps_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return out


# ---------------------------------------------------------------- Jeux de tests (module 3)

TEST_CASES = [
    {
        "id": "absorbant_accessible",
        "titre": "Circuit absorbant accessible depuis la source",
        "description": "Le circuit A → B → C → A vaut 2 − 4 + 1 = −1 et la source S peut l'atteindre. "
                       "Les distances de A, B, C et D (en aval) n'ont pas de minimum fini.",
        "nodes": ["S", "A", "B", "C", "D"],
        "edges": [("S", "A", 1), ("A", "B", 2), ("B", "C", -4), ("C", "A", 1), ("C", "D", 1)],
        "source": "S",
        "attendu": {"circuit_existe": True, "circuit_accessible": True,
                    "etats": {"S": "fini", "A": "moins_infini", "B": "moins_infini",
                              "C": "moins_infini", "D": "moins_infini"}},
    },
    {
        "id": "absorbant_non_accessible",
        "titre": "Circuit absorbant NON accessible depuis la source",
        "description": "Le circuit X → Y → Z → X vaut 1 − 3 + 1 = −1 mais aucun chemin ne relie S à ce circuit : "
                       "les distances de S, A et B restent finies (0, 2, 5).",
        "nodes": ["S", "A", "B", "X", "Y", "Z"],
        "edges": [("S", "A", 2), ("A", "B", 3), ("X", "Y", 1), ("Y", "Z", -3), ("Z", "X", 1)],
        "source": "S",
        "attendu": {"circuit_existe": True, "circuit_accessible": False,
                    "etats": {"S": "fini", "A": "fini", "B": "fini",
                              "X": "inaccessible", "Y": "inaccessible", "Z": "inaccessible"}},
    },
    {
        "id": "temoin_sans_circuit",
        "titre": "Témoin : arc négatif mais aucun circuit",
        "description": "Un arc de poids négatif n'implique pas de circuit absorbant : B → A vaut −1 "
                       "mais le graphe est acyclique, toutes les distances sont finies.",
        "nodes": ["S", "A", "B", "C"],
        "edges": [("S", "A", 4), ("S", "B", 2), ("B", "A", -1), ("A", "C", 3)],
        "source": "S",
        "attendu": {"circuit_existe": False, "circuit_accessible": False,
                    "etats": {"S": "fini", "A": "fini", "B": "fini", "C": "fini"}},
    },
]


def run_test_case(case):
    nodes, edges, source = case["nodes"], case["edges"], case["source"]

    bf_dist, _, bf_info = bellman_ford(nodes, edges, source)
    fw_dist, _, idx, names, negatifs = floyd_warshall(nodes, edges)
    exists, any_cycle = has_negative_cycle(nodes, edges)
    s = idx[source]
    fw_values = {n: fw_value(fw_dist, negatifs, s, idx[n]) for n in nodes}
    fw_accessible = any(fw_dist[s][k] != INF for k in negatifs)

    etats_bf = {n: _state(bf_dist[n]) for n in nodes}
    etats_fw = {n: _state(fw_values[n]) for n in nodes}
    attendu = case["attendu"]

    checks = {
        "bellman_ford_etats": etats_bf == attendu["etats"],
        "floyd_warshall_etats": etats_fw == attendu["etats"],
        "circuit_existe": exists == attendu["circuit_existe"],
        "circuit_accessible_bf": bf_info["circuit_accessible"] == attendu["circuit_accessible"],
        "circuit_accessible_fw": fw_accessible == attendu["circuit_accessible"],
    }
    return {
        "id": case["id"],
        "titre": case["titre"],
        "description": case["description"],
        "source": source,
        "aretes": [{"u": u, "v": v, "poids": w} for u, v, w in edges],
        "attendu": attendu,
        "circuit_existe": exists,
        "circuit_trouve": any_cycle,
        "bellman_ford": {
            "circuit_accessible": bf_info["circuit_accessible"],
            "distances": {n: describe(bf_dist[n]) for n in nodes},
        },
        "floyd_warshall": {
            "circuit_accessible": fw_accessible,
            "sommets_sur_circuit": [names[i] for i in negatifs],
            "distances": {n: describe(fw_values[n]) for n in nodes},
        },
        "verifications": checks,
        "reussi": all(checks.values()),
    }


def run_all_tests():
    return [run_test_case(c) for c in TEST_CASES]
