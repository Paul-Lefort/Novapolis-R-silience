from app.database import get_db
from app.main import app


class FakeSession:
    def execute(self, *_):
        class R:
            def scalar(self):
                return "8.0-test"
        return R()


def test_home(client):
    assert client.get("/").status_code == 200


def test_check_db(client):
    app.dependency_overrides[get_db] = lambda: FakeSession()
    r = client.get("/api/check-db")
    app.dependency_overrides.clear()
    assert r.json() == {"status": "success", "mysql_version": "8.0-test"}