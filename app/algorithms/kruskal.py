from .common import prepare_graph, event, make_response


class UnionFind:
    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1
            return True
        return False


def run(graph):
    nodes, adj, edges = prepare_graph(graph)
    sorted_edges = sorted(edges, key=lambda e: e["weight"])
    uf = UnionFind(nodes)
    mst = []
    steps = []

    steps.append(event("initialize", "Initialisation Kruskal", "Arêtes triées par poids croissants."))

    for edge in sorted_edges:
        u, v, w, eid = edge["source"], edge["target"], edge["weight"], edge["id"]
        if uf.union(u, v):
            mst.append(edge)
            steps.append(
                event("add_edge", "Arête ajoutée au MST", f"Arête {eid} ({u} - {v}) ajoutée.", active_edge=eid))
        else:
            steps.append(event("skip_edge", "Arête ignorée (cycle)", f"Arête {eid} crée un cycle.", active_edge=eid))

    return make_response(graph, steps, {"mst": mst, "total_weight": sum(e["weight"] for e in mst)})