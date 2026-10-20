from conftest import ok


def test_cp08_currency_header_on_list(client):
    body = ok(client.get("/api/books", params={"limit": 1}, headers={"X-Currency": "USD"})).json()
    book = body["items"][0]
    assert book["currency"] == "USD"
    assert book["price"] == round(4200 / 122, 2)


def test_cp08_currency_header_on_detail(client):
    assert ok(client.get("/api/books/1", headers={"X-Currency": "USD"})).json()["currency"] == "USD"
    assert ok(client.get("/api/books/1")).json()["currency"] == "BDT"


def test_cp08_unknown_currency_rejected(client):
    ok(client.get("/api/books", headers={"X-Currency": "EUR"}), 422)


def test_cp08_preferred_genre_cookie(client):
    client.cookies.set("preferred_genre", "science")
    books = ok(client.get("/api/recommendations")).json()
    assert books[0]["genre"] == "science"


def test_cp08_recommendations_without_cookie(client):
    assert len(ok(client.get("/api/recommendations")).json()) == 4


def test_cp08_client_info_headers(client):
    info = ok(client.get("/api/client-info", headers={"User-Agent": "Classroom/1.0", "Accept-Language": "bn-BD"})).json()
    assert info["user_agent"] == "Classroom/1.0"
    assert info["accept_language"] == "bn-BD"
