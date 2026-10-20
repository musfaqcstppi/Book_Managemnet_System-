from conftest import BOOK, ok


def test_cp03_create_book(client):
    created = ok(client.post("/api/books", json=BOOK), 200, 201).json()
    assert created["id"] == 17
    assert created["title"] == "Think Python"
    assert created["in_stock"] is True
    assert ok(client.get("/api/books/17")).json()["author"] == "Allen B. Downey"


def test_cp03_defaults_are_applied(client):
    minimal = {"title": "Dune", "author": "Frank Herbert", "genre": "fantasy", "price": 990}
    created = ok(client.post("/api/books", json=minimal), 200, 201).json()
    assert created["in_stock"] is True
    assert created["description"] is None


def test_cp03_missing_field_is_rejected(client):
    ok(client.post("/api/books", json={k: v for k, v in BOOK.items() if k != "title"}), 422)


def test_cp03_wrong_type_is_rejected(client):
    ok(client.post("/api/books", json={**BOOK, "price": "cheap"}), 422)
    ok(client.post("/api/books", json={**BOOK, "genre": "cooking"}), 422)
