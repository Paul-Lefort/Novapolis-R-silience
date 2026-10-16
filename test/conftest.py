import os

os.environ.setdefault("DATABASE_URL", "sqlite://")  # avant l'import de l'app

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)