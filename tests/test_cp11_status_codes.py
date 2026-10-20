from conftest import BOOK, ok
from test_cp07_nested_models import ORDER
from test_cp10_response_models import USER


def test_cp11_creates_return_201(client):
    ok(client.post("/api/books", json=BOOK), 201)
    ok(client.post("/api/orders", json=ORDER), 201)
    ok(client.post("/api/users", json=USER), 201)
    ok(client.post("/api/books/1/reviews", json={"review": {"user": "Sami", "rating": 5}}), 201)


def test_cp11_delete_returns_204(client):
    response = ok(client.delete("/api/books/3"), 204)
    assert response.content == b""
    ok(client.get("/api/books/3"), 404)


def test_cp11_delete_unknown_book(client):
    response = ok(client.delete("/api/books/999"), 404)
    assert response.json()["detail"] == "Book 999 not found"
