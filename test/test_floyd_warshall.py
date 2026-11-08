import pytest
from app.algorithme.floyd_warshall import run as floyd_warshall_run

class TestFloydWarshallAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation Floyd-Warshall : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage Floyd-Warshall : {method.__name__}")

    def test_floyd_warshall_execution(self, sample_graph_data):
        response = floyd_warshall_run(sample_graph_data)
        result = response["result"]

        assert result["path"] == ["A", "B", "C", "D"]
        assert result["cost"] == pytest.approx(4.0)
        assert "all_pairs_distances" in result
        assert response["step_count"] >= 1