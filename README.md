# BookStore API: project brief

## The client

**BookStore** is a small bookshop in Dhaka that is moving online. Their designer has
already built the web shop (the pages, buttons and forms). What they do not have is the
**backend**: the API that the shop talks to.

Your job today is to build that API with **FastAPI**. You will not touch any HTML,
CSS or JavaScript. You only write Python, in two files:

| File | You… |
|---|---|
| `main.py` | write the endpoints (path operations) |
| `models.py` | write the Pydantic models |
| `data.py` | **do not edit**: the in-memory “database” and helper functions you call |
| `ui_setup.py`, `static/` | **do not edit**: serves the web shop |
| `tests/` | **do not edit**: one test file per checkpoint |

Every feature in the shop is **locked** until you build the endpoint behind it.
The shop checks your API every 3 seconds, so features unlock as soon as you save.

---

## Setup (once)

You need **Python 3.10 or newer**.

```bash
cd bookstore
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## Every time you work

```bash
fastapi dev main.py
```

| Open | What you see |
|---|---|
| http://127.0.0.1:8000/ | the web shop |
| http://127.0.0.1:8000/docs | interactive API docs (Swagger UI), generated from your code |
| http://127.0.0.1:8000/redoc | the same docs, ReDoc style |

Check a checkpoint in a second terminal (with the virtual environment active):

```bash
pytest -k cp03        # one checkpoint
pytest                # everything
```

In the shop, the **Checkpoints** button (top right) shows your progress, and the
**Request log** bar at the bottom shows every request the shop sends and what your API
answered. Click a row to see the details. It is the best place to understand a `422`.

---

## User stories

As a **customer** I want to…
1. see that the shop is online *(CP0)*
2. open a book’s page and browse books by genre *(CP1)*
3. page through all books, filter by genre and stock *(CP2)*
4. search by title or author and filter by tags *(CP4)*
5. read and write reviews *(CP5)*
6. put books in a cart and place an order, then track it *(CP7)*
7. see prices in BDT or USD *(CP8)*
8. get recommendations for my favourite genre *(CP8)*
9. create an account without my password ever being sent back *(CP10)*
10. log in *(CP12)*, and request a book the shop does not have *(CP12)*

As **shop staff** I want to…
1. add books *(CP3)* and edit them with a change note *(CP5)*
2. be sure that bad data (negative prices, empty titles…) is rejected *(CP6)*
3. never show our cost price or supplier to customers *(CP10)*
4. delete books *(CP11)*
5. upload cover images and import books from a CSV file *(CP13)*

---

## API contract

All prices are stored in **BDT**. The `X-Currency: USD` header converts them (demo rate: 122 BDT = 1 USD).

| CP | Method | Path | Input | Success |
|---|---|---|---|---|
| 0 | GET | `/api` | n/a | `{"store", "message", "status": "online"}` |
| 1 | GET | `/api/books/{book_id}` | path `book_id` (int, ≥ 1 from CP4) | one book |
| 1 | GET | `/api/genres/{genre}` | path `genre`: fiction · fantasy · science · history · programming · children | list of books |
| 2 | GET | `/api/books` | query `skip`, `limit`, `genre`, `in_stock` (+ `q`, `tag` from CP4) | `{"total", "skip", "limit", "items"}` |
| 3 | POST | `/api/books` | JSON body: `BookCreate` | the new book (201 from CP11) |
| 5 | PUT | `/api/books/{book_id}` | path + body `{"book": BookCreate, "change_note": str}` + query `notify` | the updated book |
| 5 | POST | `/api/books/{book_id}/reviews` | body `{"review": {"user", "rating", "comment"}}` | the new review (201 from CP11) |
| 5 | GET | `/api/books/{book_id}/reviews` | n/a | list of reviews |
| 7 | POST | `/api/orders` | body: `OrderCreate` (customer, items, coupons, deliver_by) | the order with `order_id` (UUID), `created_at`, `total` (201 from CP11) |
| 7 | GET | `/api/orders/{order_id}` | path `order_id` (UUID) | the order |
| 8 | GET | `/api/recommendations` | cookie `preferred_genre` (optional) | list of 4 books |
| 8 | GET | `/api/client-info` | headers `User-Agent`, `Accept-Language` (+ `X-Currency` from CP9) | the header values |
| 10 | POST | `/api/users` | body: `UserIn` (username, email, full_name, password) | `UserOut`: **no password** (201 from CP11) |
| 11 | DELETE | `/api/books/{book_id}` | n/a | `204 No Content` |
| 12 | POST | `/api/login` | form fields `username`, `password` | `{"message", "username"}` |
| 12 | POST | `/api/book-requests` | form fields `title`, `author`, `email`, `note` | the stored request (201) |
| 13 | POST | `/api/books/{book_id}/cover` | multipart: image file `file` | `{"book_id", "filename", "content_type", "cover_url"}` |
| 13 | POST | `/api/books/with-cover` | multipart: `title`, `author`, `genre`, `price` + image `cover` | the new book (201) |
| 13 | POST | `/api/books/import` | multipart: CSV file `file` (read as bytes) | `{"imported", "titles", "skipped_lines"}` (201) |

### Validation rules (from CP4 and CP6)

| Where | Rule |
|---|---|
| `q` | 3–50 characters |
| `limit` / `skip` | 1–50 / at least 0 |
| `book_id` | at least 1 |
| Book `title` / `author` | 1–120 / 2–60 characters |
| Book `price` | greater than 0, at most 10 000 |
| Book `description` | at most 500 characters |
| Review `user` / `rating` / `comment` | 2–40 characters / 1–5 / at most 300 characters |
| Order `items` / `quantity` | at least one item / 1–10 each |
| `X-Currency` | `BDT` or `USD` |
| Username / password | 3–20 lowercase letters, digits, `_` / at least 8 characters |

Internal fields `cost_price` and `supplier` exist in the database but must **never** appear
in a response (CP10).

---

## Checkpoints

| CP | Topic | Lessons | Unlocks in the shop |
|---|---|---|---|
| 0 | First steps | 1 | “API online”, welcome banner |
| 1 | Path parameters | 2 | Genres page, book pages |
| 2 | Query parameters | 3 | All books: paging and filters |
| 3 | Request body | 4 | Add book |
| 4 | Query & Path validations | 5–6 | Search, tags |
| 5 | Multiple parameters | 7 | Edit book, reviews |
| 6 | Body fields | 8 | Field error messages |
| 7 | Nested models & extra types | 9–10 | Checkout, order tracking |
| 8 | Cookies & headers | 11–12 | Currency switch, recommendations |
| 9 | Parameter models | 13–15 | (refactor) |
| 10 | Response models | 16–17 | Sign up; the leak warning disappears |
| 11 | Status codes | 18 | Delete book |
| 12 | Forms | 19, 22 | Log in, request a book |
| 13 | Files | 20–21 | Cover uploads, CSV import |

Demo account (already in the database): **rina / bookworm123**.
Coupon codes: **SAVE10** (10% off), **STUDENT15** (15% off).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `fastapi: command not found` | Activate the virtual environment, or run `python -m fastapi dev main.py` |
| The shop says **API offline** | The server is not running, or it crashed: look at the terminal for a Python error |
| `NameError: name 'Genre' is not defined` | Add the import at the top of `main.py` |
| Everything is a `422` | Open the request log and read `detail`: it says which field failed and why |
| A feature stays locked | Check the method and path match the contract exactly, then save the file |
| Uploads fail with “python-multipart” | `pip install python-multipart` (it is included in `fastapi[standard]`) |

All data lives in memory: restarting the server restores the original 16 books.
