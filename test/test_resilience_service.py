import pytest
from unittest.mock import patch
import networkx as nx
from app.algorithme import resilience_service as rs

class TestResilienceService:
    def setup_method(self, method):
        print(f"\n[SETUP] Initialisation test resilience_service : {method.__name__}")

    def teardown_method(self, method):
        print(f"\n[TEARDOWN] Nettoyage test resilience_service : {method.__name__}")

    def test_parse_pairs(self):
        pairs = rs._parse_pairs("1->2, 3-4")
        assert pairs == [(1, 2), (3, 4)]

    @patch("app.algorithme.resilience_service.load_networkx_graph_from_csv")
    def test_generer_rapport_diagnostic(self, mock_load):
        # Simulation de graphes routier et fibre
        G = nx.DiGraph()
        G.add_node(1, type="caserne", nom="Caserne Centrale")
        G.add_node(2, type="hopital", nom="Hôpital Nord")
        G.add_edge(1, 2, temps_normal=5.0, distance_km=2.0, statut="ouvert")

        F = nx.Graph()
        F.add_node(1)
        F.add_node(2)
        F.add_edge(1, 2, cost=10.0, statut="ouvert")

        mock_load.side_effect = [G, F]

        report = rs.generer_rapport_diagnostic("routier")
        assert report["nb_sites"] == 2
        assert report["casernes_reference"] == [1]

    @patch("app.algorithme.resilience_service.load_networkx_graph_from_csv")
    def test_acm_couts_egaux_service(self, mock_load):
        F = nx.Graph()
        F.add_edge("A", "B", cost=1.0)
        F.add_edge("B", "C", cost=2.0)
        F.add_edge("A", "C", cost=3.0)
        mock_load.return_value = F

        res = rs.acm_couts_egaux_service()
        assert "nb_aretes" in res
        assert res["nb_aretes"] == 3