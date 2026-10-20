from conftest import ok


def test_cp02_default_page(client):
    body = ok(client.get("/api/books")).json()
    assert body["total"] == 16
    assert body["skip"] == 0 and body["limit"] == 10
    assert len(body["items"]) == 10


def test_cp02_skip_and_limit(client):
    body = ok(client.get("/api/books", params={"skip": 10, "limit": 4})).json()
    assert [b["id"] for b in body["items"]] == [11, 12, 13, 14]


def test_cp02_filter_by_genre(client):
    body = ok(client.get("/api/books", params={"genre": "fantasy"})).json()
    assert body["total"] == 3


def test_cp02_filter_by_stock(client):
    assert ok(client.get("/api/books", params={"in_stock": "false"})).json()["total"] == 3
    assert ok(client.get("/api/books", params={"in_stock": "true"})).json()["total"] == 13


def test_cp02_types_are_validated(client):
    ok(client.get("/api/books", params={"limit": "ten"}), 422)
