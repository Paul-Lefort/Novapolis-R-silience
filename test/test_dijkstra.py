import pytest
from app.algorithme.dijkstra import run as dijkstra_run

class TestDijkstraAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation Dijkstra : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage Dijkstra : {method.__name__}")

    def test_dijkstra_shortest_path(self, sample_graph_data):
        response = dijkstra_run(sample_graph_data)
        result = response["result"]

        assert result["path"] == ["A", "B", "C", "D"]
        assert result["cost"] == pytest.approx(4.0)
        assert response["step_count"] >= 1

    def test_dijkstra_missing_target(self, sample_graph_data):
        bad_data = sample_graph_data.copy()
        bad_data["target"] = "Z"
        with pytest.raises(ValueError, match="introuvable"):
            dijkstra_run(bad_data)