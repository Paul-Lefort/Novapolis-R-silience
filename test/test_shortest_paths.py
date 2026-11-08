import pytest
from app.algorithme import shortest_paths as sp

class TestShortestPathsModule:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation test shortest_paths : {method.__name__}")

    def teardown_method(self, method):
        print(f"\n[TEARDOWN] Nettoyage test shortest_paths : {method.__name__}")

    def test_dijkstra_basic(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 2.0), ("A", "C", 5.0)]
        dist, pred = sp.dijkstra(nodes, edges, "A")
        assert dist["C"] == 3.0
        path = sp._rebuild(pred, "A", "C")
        assert path == ["A", "B", "C"]

    def test_dijkstra_negative_weight_raises(self):
        nodes = ["A", "B"]
        edges = [("A", "B", -1.0)]
        with pytest.raises(ValueError, match="poids négatifs"):
            sp.dijkstra(nodes, edges, "A")

    def test_bellman_ford_with_negative_cycle(self):
        nodes = ["S", "A", "B"]
        edges = [("S", "A", 1.0), ("A", "B", -2.0), ("B", "A", -1.0)]
        dist, pred, info = sp.bellman_ford(nodes, edges, "S")
        assert info["circuit_accessible"] is True
        assert dist["B"] == float("-inf")

    def test_floyd_warshall(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 2.0), ("B", "C", 3.0), ("A", "C", 10.0)]
        dist, nxt, idx, names, negatifs = sp.floyd_warshall(nodes, edges)
        assert dist[idx["A"]][idx["C"]] == 5.0

    def test_run_all_module_tests(self):
        results = sp.run_all_tests()
        assert len(results) > 0
        assert all("reussi" in r for r in results)