import pytest
from app.algorithme.helper import parse_node_id, prepare_networkx_graph, event, make_response

class TestHelperModule:
    def setup_method(self, method):
        print(f"\n[SETUP] Début du test helper : {method.__name__}")

    def teardown_method(self, method):
        print(f"[TEARDOWN] Fin du test helper : {method.__name__}")

    def test_parse_node_id(self):
        assert parse_node_id("42") == 42
        assert parse_node_id("A3") == "A3"

    def test_prepare_networkx_graph(self, sample_graph_data):
        G, start, target = prepare_networkx_graph(sample_graph_data, "routier")
        assert list(G.nodes()) == ["A", "B", "C", "D"]
        assert start == "A"
        assert target == "D"
        assert G.number_of_edges() == 4

    def test_event_and_response(self, sample_graph_data):
        ev = event("info", "Test", "Description")
        res = make_response(sample_graph_data, [ev], {"ok": True})
        assert res["step_count"] == 1
        assert res["result"]["ok"] is True