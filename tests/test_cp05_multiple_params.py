import data
from conftest import BOOK, ok


def test_cp05_update_book_with_path_body_and_query(client):
    payload = {"book": {**BOOK, "title": "Fluent Python, 2nd ed."}, "change_note": "New edition"}
    updated = ok(client.put("/api/books/1", params={"notify": "true"}, json=payload)).json()
    assert updated["title"] == "Fluent Python, 2nd ed."
    assert data.CHANGE_LOG[-1]["note"] == "New edition"
    assert data.CHANGE_LOG[-1]["notified"] is True


def test_cp05_notify_defaults_to_false(client):
    ok(client.put("/api/books/2", json={"book": BOOK, "change_note": "Fix"}))
    assert data.CHANGE_LOG[-1]["notified"] is False


def test_cp05_change_note_is_required(client):
    ok(client.put("/api/books/1", json={"book": BOOK}), 422)


def test_cp05_update_unknown_book(client):
    response = ok(client.put("/api/books/999", json={"book": BOOK, "change_note": "Nope"}), 404)
    assert response.json()["detail"] == "Book 999 not found"


def test_cp05_review_is_embedded(client):
    review = {"user": "Sami", "rating": 5, "comment": "Loved it"}
    created = ok(client.post("/api/books/5/reviews", json={"review": review}), 200, 201).json()
    assert created["user"] == "Sami"
    # without the "review" key the body must be rejected, because of Body(embed=True)
    ok(client.post("/api/books/5/reviews", json=review), 422)


def test_cp05_list_reviews_and_rating(client):
    client.post("/api/books/5/reviews", json={"review": {"user": "Sami", "rating": 5}})
    client.post("/api/books/5/reviews", json={"review": {"user": "Rina", "rating": 4}})
    reviews = ok(client.get("/api/books/5/reviews")).json()
    assert [r["user"] for r in reviews] == ["Sami", "Rina"]
    assert ok(client.get("/api/books/5")).json()["rating"] == 4.5
