import pytest
from app.algorithme.bfs import run as bfs_run

class TestBFSAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation BFS : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage BFS : {method.__name__}")

    def test_bfs_execution(self, sample_graph_data):
        response = bfs_run(sample_graph_data)
        result = response["result"]

        assert set(result["visited_nodes"]) == {"A", "B", "C", "D"}
        assert result["visited_nodes"][0] == "A"
        assert "bfs_edges" in result
        assert response["step_count"] >= 1

    def test_bfs_invalid_start(self):
        invalid_data = {"nodes": ["A"], "edges": [], "start": "Z"}
        with pytest.raises(ValueError, match="introuvable"):
            bfs_run(invalid_data)