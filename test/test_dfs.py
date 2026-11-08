import pytest
from app.algorithme.dfs import run as dfs_run

class TestDFSAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation DFS : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage DFS : {method.__name__}")

    def test_dfs_execution(self, sample_graph_data):
        response = dfs_run(sample_graph_data)
        result = response["result"]

        assert set(result["visited_nodes"]) == {"A", "B", "C", "D"}
        assert result["visited_nodes"][0] == "A"
        assert "dfs_edges" in result
        assert response["step_count"] >= 1

    def test_dfs_invalid_start(self):
        invalid_data = {"nodes": ["A"], "edges": [], "start": "Z"}
        with pytest.raises(ValueError, match="introuvable"):
            dfs_run(invalid_data)