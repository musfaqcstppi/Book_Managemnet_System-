from conftest import ok


def test_cp00_welcome_message(client):
    body = ok(client.get("/api")).json()
    assert body == {"store": "BookStore", "message": "Welcome to the BookStore API", "status": "online"}


def test_cp00_docs_are_generated(client):
    ok(client.get("/docs"))
    assert "/api" in ok(client.get("/openapi.json")).json()["paths"]
