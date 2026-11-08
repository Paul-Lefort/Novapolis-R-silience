import pytest
from app.algorithme.prim import run as prim_run

class TestPrimAlgorithm:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation Prim : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Nettoyage Prim : {method.__name__}")

    def test_prim_mst(self, sample_fibre_data):
        response = prim_run(sample_fibre_data)
        result = response["result"]

        assert result["cost"] == pytest.approx(4.5)
        assert len(result["mst_edges"]) == 3
        assert response["step_count"] >= 1