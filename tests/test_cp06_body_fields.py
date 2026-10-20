import pytest

from conftest import BOOK, ok


@pytest.mark.parametrize("change", [
    {"price": 0},
    {"price": -10},
    {"price": 10001},
    {"title": ""},
    {"title": "x" * 121},
    {"author": "A"},
    {"description": "x" * 501},
])
def test_cp06_book_field_rules(client, change):
    ok(client.post("/api/books", json={**BOOK, **change}), 422)


def test_cp06_valid_book_still_works(client):
    ok(client.post("/api/books", json={**BOOK, "price": 10000}), 200, 201)


@pytest.mark.parametrize("rating", [0, 6])
def test_cp06_rating_between_1_and_5(client, rating):
    ok(client.post("/api/books/1/reviews", json={"review": {"user": "Sami", "rating": rating}}), 422)


def test_cp06_review_user_length(client):
    ok(client.post("/api/books/1/reviews", json={"review": {"user": "S", "rating": 5}}), 422)


def test_cp06_fields_show_up_in_docs(client):
    price = client.get("/openapi.json").json()["components"]["schemas"]["BookCreate"]["properties"]["price"]
    assert price.get("exclusiveMinimum") == 0
