import pytest
import networkx as nx
from app.algorithme import traversal as tr


class TestTraversalModule:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation test traversal : {method.__name__}")

    def teardown_method(self, method):
        print(f"\n[TEARDOWN] Nettoyage test traversal : {method.__name__}")

    def test_adjacency_and_undirected_view(self):
        G = nx.DiGraph()
        G.add_edge("A", "B")
        adj = tr.adjacency(G)
        assert adj == {"A": ["B"], "B": []}

        und = tr.undirected_view(adj)
        assert set(und["A"]) == {"B"}
        assert set(und["B"]) == {"A"}

    def test_bfs_and_path(self):
        adj = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        order, parent, depth = tr.bfs(adj, "A")
        assert order[0] == "A"
        assert set(order) == {"A", "B", "C", "D"}

        path = tr.bfs_path(adj, "A", "D")
        assert path[0] == "A"
        assert path[-1] == "D"
        assert len(path) == 3

    def test_reachable_from(self):
        adj = {"A": ["B"], "B": ["C"], "C": [], "X": ["Y"], "Y": []}
        reachable = tr.reachable_from(adj, ["A"])
        assert reachable == {"A", "B", "C"}

    def test_connected_components(self):
        adj = {"A": ["B"], "B": ["A"], "C": ["D"], "D": ["C"], "E": []}
        comps = tr.connected_components(adj)
        assert len(comps) == 3

    def test_find_directed_cycle(self):
        # Cycle orienté A -> B -> C -> A
        adj = {"A": ["B"], "B": ["C"], "C": ["A"], "D": []}
        cycle = tr.find_directed_cycle(adj)
        assert cycle is not None
        assert cycle[0] == cycle[-1]

        # Graphe acyclique
        adj_acyclic = {"A": ["B"], "B": ["C"], "C": []}
        assert tr.find_directed_cycle(adj_acyclic) is None