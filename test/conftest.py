import pytest

@pytest.fixture
def sample_graph_data():
    """Données de test standardisées pour les réseaux routiers (orientés)."""
    return {
        "network_type": "routier",
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

@pytest.fixture
def sample_fibre_data():
    """Données de test standardisées pour les réseaux de fibre (non orientés)."""
    return {
        "network_type": "fibre",
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            {"id": "f1", "source": "A", "target": "B", "weight": 1.5, "status": "disponible"},
            {"id": "f2", "source": "B", "target": "C", "weight": 2.0, "status": "disponible"},
            {"id": "f3", "source": "A", "target": "C", "weight": 4.0, "status": "disponible"},
            {"id": "f4", "source": "C", "target": "D", "weight": 1.0, "status": "disponible"},
        ],
        "start": "A",
        "target": "D",
    }