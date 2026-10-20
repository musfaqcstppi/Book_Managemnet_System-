from conftest import ok


def test_cp04_search(client):
    body = ok(client.get("/api/books", params={"q": "python"})).json()
    assert body["total"] == 2


def test_cp04_search_too_short(client):
    ok(client.get("/api/books", params={"q": "py"}), 422)


def test_cp04_search_too_long(client):
    ok(client.get("/api/books", params={"q": "x" * 51}), 422)


def test_cp04_repeated_tag_parameter(client):
    assert ok(client.get("/api/books", params={"tag": ["python"]})).json()["total"] == 2
    assert ok(client.get("/api/books", params={"tag": ["python", "beginner"]})).json()["total"] == 1


def test_cp04_limit_and_skip_bounds(client):
    ok(client.get("/api/books", params={"limit": 51}), 422)
    ok(client.get("/api/books", params={"limit": 0}), 422)
    ok(client.get("/api/books", params={"skip": -1}), 422)


def test_cp04_book_id_must_be_positive(client):
    ok(client.get("/api/books/0"), 422)
    ok(client.get("/api/books/-5"), 422)
