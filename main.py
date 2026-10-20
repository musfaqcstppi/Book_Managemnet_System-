"""
BookStore API: STARTER. This is the file you work in today.

Run:    fastapi dev main.py
Shop:   http://127.0.0.1:8000/        (features unlock as you build them)
Docs:   http://127.0.0.1:8000/docs
Check:  pytest -k cp03                (runs the tests for one checkpoint)

How to work:
  * Each checkpoint starts with "# TODO CPn". Do them in order.
  * Uncomment the code (select it, then Ctrl+/ in VS Code), replace every ___,
    save, and watch the shop unlock.
  * Some checkpoints come back to an endpoint you already wrote. They say so.
  * Add imports at the top as you need them. The comments tell you which.
"""

from fastapi import FastAPI

import data
# TODO CP1: import your models from models.py as you create them, for example:
# from models import Genre
from ui_setup import setup_ui

app = FastAPI(
    title="BookStore API",
    description="The backend for the BookStore web shop.",
    version="1.0.0",
)
setup_ui(app)  # serves the web UI at "/" (given, do not edit)


# ======================================================================
# TODO CP0 · First steps (Lesson 1)
#   GET /api  →  {"store": "BookStore", "message": "Welcome to the BookStore API", "status": "online"}
#   Then open http://127.0.0.1:8000/docs and press "Try it out".
# ======================================================================
@app.get("/api")
def welcome():
    return {"store": "BookStore", "message": "Welcome To My Book Store!", "status": "online"}


# ======================================================================
# TODO CP1 · Path parameters (Lesson 2)
#   1. In models.py, finish the Genre enum (TODO CP1 there) and import Genre above.
#   2. GET /api/books/{book_id}  → one book.
#      data.get_book_or_404(book_id) returns it (and raises a 404 for unknown IDs).
#   3. GET /api/genres/{genre}   → the books in that genre: data.books_by_genre(genre)
# ======================================================================
# @app.get("/api/books/{`___`}")
# def read_book(book_id: ____):
#     return data.get_book_or_404(book_id)


# @app.get("/api/genres/{genre}")
# def books_in_genre(genre: ____):
#     return data.books_by_genre(genre)


# ======================================================================
# TODO CP2 · Query parameters (Lesson 3)
#   GET /api/books?skip=0&limit=10&genre=fantasy&in_stock=true
#     skip: int, default 0         limit: int, default 10
#     genre: optional Genre        in_stock: optional bool
#   data.list_books(...) returns {"total": ..., "skip": ..., "limit": ..., "items": [...]}
# ======================================================================
# @app.get("/api/books")
# def list_books(skip: int = ___, limit: int = ___, genre: ___ | None = None, in_stock: ___ | None = None):
#     return data.list_books(skip=skip, limit=limit, genre=genre, in_stock=in_stock)


# ======================================================================
# TODO CP3 · Request body (Lesson 4)
#   1. In models.py, write the BookCreate model (TODO CP3 there) and import it above.
#   2. POST /api/books with a BookCreate body → data.add_book(book.model_dump())
# ======================================================================
# @app.___("/api/books")
# def create_book(book: ___):
#     return data.add_book(book.___())


# ======================================================================
# TODO CP4 · Query & Path validations (Lessons 5–6)   ← changes code you already wrote
#   Imports:  from typing import Annotated      and add Path, Query to the fastapi import.
#
#   In list_books (CP2) use these parameters:
#       skip: Annotated[int, Query(ge=___)] = 0,
#       limit: Annotated[int, Query(ge=1, le=___)] = 10,          # at most 50 per page
#       genre: Genre | None = None,
#       in_stock: bool | None = None,
#       q: Annotated[str | None, Query(min_length=___, max_length=___)] = None,   # 3 to 50
#       tags: Annotated[list[str] | None, Query(alias="___")] = None,             # ?tag=a&tag=b
#   and pass  q=q, tag=tags  to data.list_books(...).
#
#   In read_book (CP1) use:
#       book_id: Annotated[int, Path(title="Book ID", ge=___)]
# ======================================================================


# ======================================================================
# TODO CP5 · Multiple parameters (Lesson 7)
#   Add Body to the fastapi import. Write the Review model in models.py (TODO CP5 there).
#
#   PUT /api/books/{book_id}?notify=true
#     path:   book_id (int, at least 1)
#     body:   {"book": {...a BookCreate...}, "change_note": "Price updated"}
#             → two body values: a BookCreate called `book`, and a str `change_note`
#               declared with Body(min_length=3, max_length=200)
#     query:  notify: bool, default False
#     return  data.update_book(book_id, book.model_dump(), change_note, notify)
#
#   POST /api/books/{book_id}/reviews
#     body:   {"review": {"user": "Sami", "rating": 5, "comment": "Great!"}}
#             → ONE model, but sent under a "review" key: use Body(embed=True)
#     return  data.add_review(book_id, review.model_dump())
#
#   GET /api/books/{book_id}/reviews
#     return  data.list_reviews(book_id)
# ======================================================================
# @app.put("/api/books/{book_id}")
# def update_book(...):
#     ...
#
#
# @app.post("/api/books/{book_id}/reviews")
# def add_review(...):
#     ...
#
#
# @app.get("/api/books/{book_id}/reviews")
# def list_reviews(...):
#     ...


# ======================================================================
# TODO CP6 · Body fields (Lesson 8)
#   All the work is in models.py (TODO CP6 there). Then try a negative price in the shop.
# ======================================================================


# ======================================================================
# TODO CP7 · Nested models & extra types (Lessons 9–10)
#   1. models.py: Customer, OrderItem, OrderCreate, and tags on BookCreate (TODO CP7 there).
#   2. POST /api/orders              body: OrderCreate → data.create_order(order.model_dump())
#   3. GET  /api/orders/{order_id}   order_id is a UUID (from uuid import UUID)
#                                    → data.get_order_or_404(order_id)
# ======================================================================
# @app.post("/api/orders")
# def create_order(...):
#     ...
#
#
# @app.get("/api/orders/{order_id}")
# def read_order(...):
#     ...


# ======================================================================
# TODO CP8 · Cookies & headers (Lessons 11–12)   ← also changes code you already wrote
#   Add Cookie, Header to the fastapi import. In models.py add Currency (TODO CP8 there).
#   1. list_books and read_book get a header parameter:
#          x_currency: Annotated[Currency, Header()] = "BDT"
#      and convert prices before returning:
#          list_books:  result["items"] = data.convert_prices(result["items"], x_currency)
#          read_book:   return data.convert_price(book, x_currency)
#   2. GET /api/recommendations   optional cookie preferred_genre (a Genre)
#                                 → data.recommend(preferred_genre)
#   3. GET /api/client-info       optional headers user_agent and accept_language
#                                 → {"user_agent": ..., "accept_language": ...}
# ======================================================================
# @app.get("/api/recommendations")
# def recommendations(...):
#     ...
#
#
# @app.get("/api/client-info")
# def client_info(...):
#     ...


# ======================================================================
# TODO CP9 · Parameter models (Lessons 13–15)   ← a refactor, no new endpoints
#   Write BookFilter, Preferences and ClientHeaders in models.py (TODO CP9 there), then:
#     list_books:       replace the six query parameters with one model parameter
#                       and call data.list_books(**filters.model_dump())
#     recommendations:  take the cookie as a Preferences model
#     client_info:      take the headers as a ClientHeaders model and return it
#   Done when an unknown query parameter, e.g. /api/books?colour=blue, returns 422.
# ======================================================================


# ======================================================================
# TODO CP10 · Response models (Lessons 16–17)
#   1. models.py: BookOut, BookList, UserBase, UserIn, UserOut, UserInDB (TODO CP10 there).
#   2. Customers must never see cost_price or supplier. Give every endpoint that
#      returns books a response model (list_books, read_book, books_in_genre,
#      create_book, update_book, recommendations).
#   3. POST /api/users   body: UserIn   response: UserOut
#        Build a UserInDB from the input plus hashed_password=data.fake_hash(...),
#        save it with data.save_user(...), and return it.
# ======================================================================


# ======================================================================
# TODO CP11 · Status codes (Lesson 18)
#   1. 201 Created for: POST /api/books, /api/orders, /api/users, /api/books/{book_id}/reviews
#   2. DELETE /api/books/{book_id}  → 204 No Content, using data.delete_book(book_id)
# ======================================================================


# ======================================================================
# TODO CP12 · Forms (Lessons 19, 22)
#   1. POST /api/login         form fields: username, password
#        user = data.verify_user(username, password)
#        return {"message": "Welcome back, <full name or username>!", "username": ...}
#   2. models.py: BookRequestForm (TODO CP12 there).
#      POST /api/book-requests  the whole form as one model, 201
#        → data.save_book_request(...)
# ======================================================================


# ======================================================================
# TODO CP13 · Files (Lessons 20–21)
#   1. POST /api/books/{book_id}/cover   one uploaded image called "file"
#        cover_url = data.save_cover(book_id, file)
#        return {"book_id", "filename", "content_type", "cover_url"}
#   2. POST /api/books/with-cover        form fields title, author, genre, price
#        (same rules as BookCreate) + an image called "cover"; 201; returns a BookOut
#        → data.add_book_with_cover(book_data, cover)
#   3. POST /api/books/import            a CSV file called "file", read as bytes; 201
#        → data.import_csv(file)
# ======================================================================
