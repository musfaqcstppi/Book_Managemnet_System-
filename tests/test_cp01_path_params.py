from conftest import ok


def test_cp01_read_one_book(client):
    book = ok(client.get("/api/books/1")).json()
    assert book["id"] == 1
    assert book["title"] == "Fluent Python"


def test_cp01_book_id_is_converted_to_int(client):
    # "abc" is not an int, so FastAPI rejects it before your code runs
    ok(client.get("/api/books/abc"), 422)


def test_cp01_unknown_book_is_404(client):
    response = ok(client.get("/api/books/999"), 404)
    assert response.json()["detail"] == "Book 999 not found"


def test_cp01_books_in_genre(client):
    books = ok(client.get("/api/genres/fantasy")).json()
    assert len(books) == 3
    assert all(b["genre"] == "fantasy" for b in books)


def test_cp01_genre_must_be_in_the_enum(client):
    ok(client.get("/api/genres/cooking"), 422)
