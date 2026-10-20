from conftest import ok


def test_cp12_login_with_form_data(client):
    body = ok(client.post("/api/login", data={"username": "rina", "password": "bookworm123"})).json()
    assert body["message"] == "Welcome back, Rina Akter!"


def test_cp12_login_wrong_password(client):
    ok(client.post("/api/login", data={"username": "rina", "password": "nope"}), 401)


def test_cp12_login_rejects_json(client):
    # Form() fields must come as form data, not as a JSON body
    ok(client.post("/api/login", json={"username": "rina", "password": "bookworm123"}), 422)


def test_cp12_book_request_form_model(client):
    created = ok(client.post("/api/book-requests", data={"title": "Dune", "email": "sami@example.com"}), 201).json()
    assert created["id"] == 1 and created["status"] == "pending"


def test_cp12_book_request_validation(client):
    ok(client.post("/api/book-requests", data={"title": "Dune"}), 422)
    ok(client.post("/api/book-requests", data={"title": "Dune", "email": "nope"}), 422)
