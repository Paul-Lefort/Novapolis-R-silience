"""Construction d'un graphe géographiquement cohérent (partagé routes / fibre).

Principes :
  - arêtes courtes uniquement (voisins proches), donc pas de lignes traversant la carte
  - AUCUN croisement d'arêtes (graphe planaire)
  - degré max 3 par sommet, graphe connexe
  - distances réelles en km (haversine), avec correction de la longitude
"""
import csv
import heapq
import math
import random
from collections import defaultdict

import networkx as nx

R_TERRE_KM = 6371.0088


def lire_sites(filepath):
    """Retourne {id: (lat, lon)}."""
    sites = {}
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            sites[int(row["id"])] = (float(row["latitude"]), float(row["longitude"]))
    return sites


def haversine_km(a, b):
    la1, lo1 = map(math.radians, a)
    la2, lo2 = map(math.radians, b)
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_TERRE_KM * math.asin(math.sqrt(h))


# ---------- géométrie : détection de croisements ----------
def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _se_croisent(p1, p2, p3, p4):
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    return d1 * d2 < 0 and d3 * d4 < 0


class _GrilleAretes:
    """Index spatial pour ne tester que les arêtes voisines."""

    def __init__(self, taille, pts):
        self.t, self.pts = taille, pts
        self.cases = defaultdict(list)

    def _cases(self, p, q):
        x0, x1 = sorted((p[0], q[0]))
        y0, y1 = sorted((p[1], q[1]))
        for i in range(int(x0 // self.t), int(x1 // self.t) + 1):
            for j in range(int(y0 // self.t), int(y1 // self.t) + 1):
                yield (i, j)

    def ajouter(self, u, v):
        for c in self._cases(self.pts[u], self.pts[v]):
            self.cases[c].append((u, v))

    def croise(self, u, v):
        p, q = self.pts[u], self.pts[v]
        vus = set()
        for c in self._cases(p, q):
            for a, b in self.cases.get(c, ()):
                if (a, b) in vus or a in (u, v) or b in (u, v):
                    continue
                vus.add((a, b))
                if _se_croisent(p, q, self.pts[a], self.pts[b]):
                    return True
        return False


# ---------- construction ----------
def construire_graphe(sites, nombre_aretes=None, degre_max=3, jitter=0.0, k_voisins=10):
    """Graphe non orienté planaire, connexe, degré <= degre_max.

    jitter : bruit sur les poids (0.3 = jusqu'à +30 %) pour que deux réseaux
             (routes / fibre) ne soient pas identiques tout en restant locaux.
    """
    ids = list(sites)
    n = len(ids)
    lat0 = sum(la for la, _ in sites.values()) / n
    coslat = math.cos(math.radians(lat0))
    pts = {i: (sites[i][1] * coslat, sites[i][0]) for i in ids}  # plan local (degrés)

    max_possible = (degre_max * n) // 2
    cible = max_possible if nombre_aretes is None else min(nombre_aretes, max_possible)
    cible = max(cible, n - 1)

    # candidats : k plus proches voisins de chaque site
    cand = set()
    for u in ids:
        pu = pts[u]
        proches = heapq.nsmallest(
            k_voisins,
            (v for v in ids if v != u),
            key=lambda v: (pts[v][0] - pu[0]) ** 2 + (pts[v][1] - pu[1]) ** 2,
        )
        for v in proches:
            cand.add((min(u, v), max(u, v)))
    poids = {e: math.dist(pts[e[0]], pts[e[1]]) * (1 + random.uniform(0, jitter)) for e in cand}
    ordre = sorted(cand, key=poids.get)

    xs = [p[0] for p in pts.values()]
    ys = [p[1] for p in pts.values()]
    taille = max(max(xs) - min(xs), max(ys) - min(ys), 1e-9) / max(1, math.sqrt(n)) * 2
    grille = _GrilleAretes(taille, pts)

    G = nx.Graph()
    G.add_nodes_from(ids)

    def ajouter(u, v):
        G.add_edge(u, v)
        grille.ajouter(u, v)

    # 1) ossature (Kruskal avec plafond de degré) -> arbre local
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in ordre:
        if G.degree[u] >= degre_max or G.degree[v] >= degre_max:
            continue
        ru, rv = find(u), find(v)
        if ru == rv or grille.croise(u, v):
            continue
        parent[ru] = rv
        ajouter(u, v)

    # 2) rattachement des composantes restantes (plus courte liaison possible)
    comps = list(nx.connected_components(G))
    while len(comps) > 1:
        comps.sort(key=len)
        libres = [u for u in comps[0] if G.degree[u] < degre_max]
        autres = [v for c in comps[1:] for v in c if G.degree[v] < degre_max]
        paires = heapq.nsmallest(
            40, ((math.dist(pts[u], pts[v]), u, v) for u in libres for v in autres)
        )
        _, u, v = next((p for p in paires if not grille.croise(p[1], p[2])), paires[0])
        ajouter(u, v)
        comps = list(nx.connected_components(G))

    # 3) arêtes de maillage supplémentaires (courtes, sans croisement)
    for u, v in ordre:
        if G.number_of_edges() >= cible:
            break
        if G.has_edge(u, v) or G.degree[u] >= degre_max or G.degree[v] >= degre_max:
            continue
        if grille.croise(u, v):
            continue
        ajouter(u, v)

    return G


def orienter(G):
    """Faiblement connexe, NON fortement connexe : un site « source » n'a que des arcs sortants."""
    source = random.choice(list(G.nodes))
    DG = nx.DiGraph()
    DG.add_nodes_from(G.nodes)
    for u, v in G.edges():
        if v == source or (u != source and random.random() < 0.5):
            u, v = v, u
        DG.add_edge(u, v)
    return DG