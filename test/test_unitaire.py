import pytest

from app.algorithme.helper import prepare_networkx_graph

from app.algorithme.bfs import run as bfs_run
from app.algorithme.dfs import run as dfs_run
from app.algorithme.dijkstra import run as dijkstra_run
from app.algorithme.bellman_ford import run as bellman_ford_run
from app.algorithme.floyd_warshall import run as floyd_warshall_run
from app.algorithme.kruskal import run as kruskal_run
from app.algorithme.prim import run as prim_run


@pytest.fixture
def sample_graph_data():
    """
    Graphe de test :
        A --1-- B --2-- C --1-- D
         \\________4________/
    Le graphe est orienté pour les algorithmes de parcours/plus court chemin
    (sens source -> target), et traité comme non orienté par Prim/Kruskal.
    """
    return {
        "directed": False,
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            {"id": "e1", "source": "A", "target": "B", "weight": 1.0, "status": "disponible"},
            {"id": "e2", "source": "B", "target": "C", "weight": 2.0, "status": "disponible"},
            {"id": "e3", "source": "A", "target": "C", "weight": 4.0, "status": "disponible"},
            {"id": "e4", "source": "C", "target": "D", "weight": 1.0, "status": "disponible"},
        ],
        "start": "A",
        "target": "D",
    }


def test_prepare_graph_validation(sample_graph_data):
    # Récupération du graphe NetworkX et des autres éléments retournés
    G, start, edges = prepare_networkx_graph(sample_graph_data)
    
    # On convertit les nœuds du graphe NetworkX en liste Python pour la comparaison
    assert list(G.nodes()) == ["A", "B", "C", "D"]
    assert len(G.edges()) == 4


def test_bfs_returns_expected_traversal(sample_graph_data):
    response = bfs_run(sample_graph_data)

    assert response["result"]["visited_nodes"] == ["A", "B", "C", "D"]
    assert response["result"]["bfs_edges"] == [("A", "B"), ("A", "C"), ("C", "D")]
    assert response["step_count"] == 2
    assert response["steps"][-1]["type"] == "complete"


def test_dfs_returns_expected_traversal(sample_graph_data):
    response = dfs_run(sample_graph_data)

    assert response["result"]["visited_nodes"] == ["A", "B", "C", "D"]
    assert response["result"]["dfs_edges"] == [("A", "B"), ("B", "C"), ("C", "D")]
    assert response["step_count"] == 2
    assert response["steps"][-1]["type"] == "complete"


def test_dijkstra_returns_shortest_path_and_cost(sample_graph_data):
    response = dijkstra_run(sample_graph_data)

    assert response["result"]["path"] == ["A", "B", "C", "D"]
    assert response["result"]["cost"] == pytest.approx(4.0)
    assert response["step_count"] == 2


def test_bellman_ford_returns_shortest_path_and_cost(sample_graph_data):
    response = bellman_ford_run(sample_graph_data)

    assert response["result"]["path"] == ["A", "B", "C", "D"]
    assert response["result"]["cost"] == pytest.approx(4.0)
    assert response["result"]["negative_cycle"] is False
    assert response["step_count"] == 2


def test_floyd_warshall_returns_expected_path_and_all_distances(sample_graph_data):
    response = floyd_warshall_run(sample_graph_data)
    result = response["result"]

    assert result["path"] == ["A", "B", "C", "D"]
    assert result["cost"] == pytest.approx(4.0)
    assert result["all_pairs_distances"] == {
        "A": {"A": 0, "B": 1.0, "C": 3.0, "D": 4.0},
        "B": {"B": 0, "C": 2.0, "D": 3.0},
        "C": {"C": 0, "D": 1.0},
        "D": {"D": 0},
    }
    assert response["step_count"] == 2


def test_kruskal_returns_expected_mst(sample_graph_data):
    response = kruskal_run(sample_graph_data)
    result = response["result"]

    assert result["cost"] == pytest.approx(4.0)
    assert len(result["mst_edges"]) == 3  # Un arbre couvrant minimal pour 4 nœuds connectés possède 3 arêtes
    assert response["step_count"] == 2


def test_prim_returns_expected_mst(sample_graph_data):
    response = prim_run(sample_graph_data)
    result = response["result"]

    assert result["cost"] == pytest.approx(4.0)
    assert len(result["mst_edges"]) == 3
    assert response["step_count"] == 2