from conftest import ok

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
CSV = (b"title,author,genre,price,tags\n"
       b"Dune,Frank Herbert,fantasy,990,classic;space\n"
       b"Bad Row,Nobody,cooking,100,\n")


def test_cp13_upload_cover(client):
    body = ok(client.post("/api/books/2/cover", files={"file": ("cover.png", PNG, "image/png")})).json()
    assert body["filename"] == "cover.png"
    assert body["content_type"] == "image/png"
    assert body["cover_url"].startswith("/uploads/")
    assert ok(client.get("/api/books/2")).json()["cover_url"] == body["cover_url"]


def test_cp13_cover_must_be_an_image(client):
    ok(client.post("/api/books/2/cover", files={"file": ("notes.txt", b"hello", "text/plain")}), 400)


def test_cp13_book_and_cover_in_one_form(client):
    fields = {"title": "Dune", "author": "Frank Herbert", "genre": "fantasy", "price": "990"}
    book = ok(client.post("/api/books/with-cover", data=fields, files={"cover": ("dune.png", PNG, "image/png")}), 201).json()
    assert book["title"] == "Dune" and book["cover_url"].startswith("/uploads/")
    ok(client.post("/api/books/with-cover", data={**fields, "price": "-1"},
                   files={"cover": ("dune.png", PNG, "image/png")}), 422)


def test_cp13_import_csv_bytes(client):
    body = ok(client.post("/api/books/import", files={"file": ("books.csv", CSV, "text/csv")}), 201).json()
    assert body["imported"] == 1
    assert body["titles"] == ["Dune"]
    assert body["skipped_lines"] == [3]


def test_cp13_file_is_required(client):
    ok(client.post("/api/books/import"), 422)
