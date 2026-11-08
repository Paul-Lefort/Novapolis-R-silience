import pytest
from app.algorithme.kruskal import run as kruskal_run

class TestKruskalAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation Kruskal : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage Kruskal : {method.__name__}")

    def test_kruskal_mst(self, sample_fibre_data):
        response = kruskal_run(sample_fibre_data)
        result = response["result"]

        assert result["cost"] == pytest.approx(4.5)
        assert len(result["mst_edges"]) == 3
        assert response["step_count"] >= 1