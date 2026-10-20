from conftest import ok


def test_cp09_query_model_forbids_extra_params(client):
    response = ok(client.get("/api/books", params={"colour": "blue"}), 422)
    assert "extra_forbidden" in response.text


def test_cp09_query_model_keeps_all_filters(client):
    body = ok(client.get("/api/books", params={"genre": "programming", "in_stock": "true", "q": "python",
                                               "tag": ["beginner"], "limit": 5})).json()
    assert body["total"] == 1
    ok(client.get("/api/books", params={"q": "py"}), 422)


def test_cp09_cookie_model(client):
    client.cookies.set("preferred_genre", "children")
    assert ok(client.get("/api/recommendations")).json()[0]["genre"] == "children"


def test_cp09_header_model(client):
    info = ok(client.get("/api/client-info", headers={"X-Currency": "USD", "Accept-Language": "en"})).json()
    assert info["x_currency"] == "USD"
    assert info["accept_language"] == "en"
