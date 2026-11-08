import pytest
from app.algorithme.bellman_ford import run as bellman_ford_run

class TestBellmanFordAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation Bellman-Ford : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage Bellman-Ford : {method.__name__}")

    def test_bellman_ford_path(self, sample_graph_data):
        response = bellman_ford_run(sample_graph_data)
        result = response["result"]

        assert result["path"] == ["A", "B", "C", "D"]
        assert result["cost"] == pytest.approx(4.0)
        assert result["negative_cycle"] is False
        assert response["step_count"] >= 1