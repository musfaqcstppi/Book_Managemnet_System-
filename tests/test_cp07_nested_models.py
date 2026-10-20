import uuid

from conftest import BOOK, ok

ORDER = {
    "customer": {"name": "Rina Akter", "email": "rina@example.com"},
    "items": [{"book_id": 2, "quantity": 2}, {"book_id": 5}],
    "coupons": ["SAVE10", "SAVE10"],
    "deliver_by": "2026-12-01",
}


def test_cp07_place_order(client):
    order = ok(client.post("/api/orders", json=ORDER), 200, 201).json()
    uuid.UUID(order["order_id"])            # a real UUID
    assert order["created_at"]              # a datetime
    assert order["items"][1]["quantity"] == 1  # default quantity
    assert order["coupons"] == ["SAVE10"]   # a set removes duplicates
    assert float(order["total"]) == 4545.0  # (2*2100 + 850) - 10%
    assert order["deliver_by"] == "2026-12-01"


def test_cp07_nested_validation(client):
    ok(client.post("/api/orders", json={**ORDER, "items": []}), 422)
    ok(client.post("/api/orders", json={**ORDER, "items": [{"book_id": 2, "quantity": 11}]}), 422)
    ok(client.post("/api/orders", json={**ORDER, "customer": {"name": "Rina", "email": "not-an-email"}}), 422)
    ok(client.post("/api/orders", json={**ORDER, "deliver_by": "next week"}), 422)


def test_cp07_read_order_by_uuid(client):
    order_id = ok(client.post("/api/orders", json=ORDER), 200, 201).json()["order_id"]
    assert ok(client.get(f"/api/orders/{order_id}")).json()["order_id"] == order_id
    ok(client.get("/api/orders/not-a-uuid"), 422)
    ok(client.get(f"/api/orders/{uuid.uuid4()}"), 404)


def test_cp07_book_tags_are_a_set(client):
    created = ok(client.post("/api/books", json={**BOOK, "tags": ["python", "python", "intro"]}), 200, 201).json()
    assert sorted(created["tags"]) == ["intro", "python"]
