import data
from conftest import BOOK, ok

INTERNAL = {"cost_price", "supplier"}
USER = {"username": "sami_99", "email": "sami@example.com", "full_name": "Sami Rahman", "password": "secret123"}


def no_internal(book):
    leaked = INTERNAL & set(book)
    assert not leaked, f"internal fields leaked to customers: {leaked}"


def test_cp10_list_hides_internal_fields(client):
    for book in ok(client.get("/api/books")).json()["items"]:
        no_internal(book)


def test_cp10_other_book_endpoints_hide_internal_fields(client):
    no_internal(ok(client.get("/api/books/1")).json())
    for book in ok(client.get("/api/genres/history")).json():
        no_internal(book)
    for book in ok(client.get("/api/recommendations")).json():
        no_internal(book)
    no_internal(ok(client.post("/api/books", json=BOOK), 200, 201).json())
    no_internal(ok(client.put("/api/books/1", json={"book": BOOK, "change_note": "Edit"})).json())


def test_cp10_register_never_returns_passwords(client):
    user = ok(client.post("/api/users", json=USER), 200, 201).json()
    assert user == {"username": "sami_99", "email": "sami@example.com", "full_name": "Sami Rahman"}
    stored = data.USERS["sami_99"]
    assert "password" not in stored and stored["hashed_password"].startswith("fakehash$")


def test_cp10_register_validation(client):
    ok(client.post("/api/users", json={**USER, "username": "Sami Rahman"}), 422)
    ok(client.post("/api/users", json={**USER, "password": "short"}), 422)
    ok(client.post("/api/users", json={**USER, "username": "rina"}), 409)
