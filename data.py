"""
BookStore in-memory "database" and helpers.

GIVEN CODE: you do not need to edit this file.

Everything here is plain Python. Your job in main.py is the FastAPI part:
declaring endpoints, parameters and models, then calling these helpers.

Some helpers raise HTTPException (for example a 404 when a book does not
exist). You will learn how that works in lesson 23, "Handling Errors".
"""

import csv
import hashlib
import io
import shutil
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Demo exchange rate used by the X-Currency header (not a live rate).
BDT_PER_USD = 122

COUPONS = {"SAVE10": Decimal("0.10"), "STUDENT15": Decimal("0.15")}

_SEED_BOOKS = [
    {"title": "Fluent Python", "author": "Luciano Ramalho", "genre": "programming", "price": 4200,
     "tags": ["python", "advanced"], "description": "Idiomatic Python, from data models to concurrency."},
    {"title": "Automate the Boring Stuff with Python", "author": "Al Sweigart", "genre": "programming", "price": 2100,
     "tags": ["python", "beginner"], "description": "Practical scripts for everyday computer chores."},
    {"title": "Clean Code", "author": "Robert C. Martin", "genre": "programming", "price": 2900,
     "tags": ["craft", "best-practices"], "description": "Habits for writing code other people can read."},
    {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "genre": "programming",
     "price": 4800, "tags": ["databases", "advanced"], "in_stock": False,
     "description": "How storage, replication and streams really work."},
    {"title": "The Hobbit", "author": "J. R. R. Tolkien", "genre": "fantasy", "price": 850,
     "tags": ["classic", "adventure"], "description": "A reluctant hobbit joins a quest for dragon gold."},
    {"title": "A Wizard of Earthsea", "author": "Ursula K. Le Guin", "genre": "fantasy", "price": 720,
     "tags": ["classic", "magic"], "description": "A young mage must face the shadow he released."},
    {"title": "The Name of the Wind", "author": "Patrick Rothfuss", "genre": "fantasy", "price": 1350,
     "tags": ["magic", "adventure"], "in_stock": False,
     "description": "A legendary figure tells the true story of his life."},
    {"title": "Pather Panchali", "author": "Bibhutibhushan Bandyopadhyay", "genre": "fiction", "price": 450,
     "tags": ["bengali", "classic"], "description": "Childhood and hardship in a Bengal village."},
    {"title": "Nineteen Eighty-Four", "author": "George Orwell", "genre": "fiction", "price": 600,
     "tags": ["classic", "dystopia"], "description": "Life under total surveillance and rewritten truth."},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "genre": "fiction", "price": 680,
     "tags": ["classic"], "description": "A child's view of justice in a small Southern town."},
    {"title": "A Brief History of Time", "author": "Stephen Hawking", "genre": "science", "price": 900,
     "tags": ["physics", "space"], "description": "Black holes, the big bang and the nature of time."},
    {"title": "The Selfish Gene", "author": "Richard Dawkins", "genre": "science", "price": 950,
     "tags": ["biology", "evolution"], "description": "Evolution explained from the gene's point of view."},
    {"title": "Sapiens", "author": "Yuval Noah Harari", "genre": "history", "price": 1100,
     "tags": ["humanity", "bestseller"], "description": "A brief history of humankind."},
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "genre": "history", "price": 1050,
     "tags": ["civilization"], "in_stock": False,
     "description": "Why some societies came to dominate others."},
    {"title": "The Little Prince", "author": "Antoine de Saint-Exupéry", "genre": "children", "price": 380,
     "tags": ["classic", "illustrated"], "description": "A pilot meets a small traveller from another planet."},
    {"title": "Charlotte's Web", "author": "E. B. White", "genre": "children", "price": 420,
     "tags": ["classic", "animals"], "description": "A pig, a spider and a friendship that saves a life."},
]

BOOKS: dict[int, dict] = {}
REVIEWS: dict[int, list[dict]] = {}
ORDERS: dict[uuid.UUID, dict] = {}
USERS: dict[str, dict] = {}
BOOK_REQUESTS: list[dict] = []
CHANGE_LOG: list[dict] = []
_next_id = 1


def _new_book(book_data: dict) -> dict:
    """Fill in the internal fields every stored book has."""
    global _next_id
    price = float(book_data["price"])
    book = {
        "id": _next_id,
        "title": book_data["title"],
        "author": book_data["author"],
        "genre": _plain(book_data["genre"]),
        "price": price,
        "currency": "BDT",
        "in_stock": book_data.get("in_stock", True),
        "description": book_data.get("description"),
        "tags": sorted(set(book_data.get("tags") or [])),
        "cover_url": book_data.get("cover_url"),
        "rating": None,
        "review_count": 0,
        # Internal fields: these must NOT be shown to customers (checkpoint 10).
        "cost_price": round(price * 0.62, 2),
        "supplier": book_data.get("supplier", "Dhaka Book Distributors Ltd."),
    }
    BOOKS[_next_id] = book
    REVIEWS[_next_id] = []
    _next_id += 1
    return book


def _plain(value):
    """Turn an Enum member into its plain value; leave anything else alone."""
    return getattr(value, "value", value)


def reset() -> None:
    """Restore the seed data. Called once at start-up and before each test."""
    global _next_id
    BOOKS.clear(); REVIEWS.clear(); ORDERS.clear(); USERS.clear()
    BOOK_REQUESTS.clear(); CHANGE_LOG.clear()
    _next_id = 1
    for seed in _SEED_BOOKS:
        _new_book(seed)
    USERS["rina"] = {"username": "rina", "email": "rina@example.com", "full_name": "Rina Akter",
                     "hashed_password": fake_hash("bookworm123")}


# ---------- books ----------

def get_book_or_404(book_id: int) -> dict:
    if book_id not in BOOKS:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return deepcopy(BOOKS[book_id])


def list_books(skip: int = 0, limit: int = 10, genre=None, in_stock: bool | None = None,
               q: str | None = None, tag: list[str] | None = None) -> dict:
    """Filter, then paginate. Returns {"total", "skip", "limit", "items"}."""
    genre = _plain(genre)
    items = list(BOOKS.values())
    if genre:
        items = [b for b in items if b["genre"] == genre]
    if in_stock is not None:
        items = [b for b in items if b["in_stock"] == in_stock]
    if q:
        needle = q.lower()
        items = [b for b in items if needle in b["title"].lower() or needle in b["author"].lower()]
    if tag:
        wanted = {t.lower() for t in tag}
        items = [b for b in items if wanted <= set(b["tags"])]
    return {"total": len(items), "skip": skip, "limit": limit,
            "items": deepcopy(items[skip: skip + limit])}


def books_by_genre(genre) -> list[dict]:
    genre = _plain(genre)
    return deepcopy([b for b in BOOKS.values() if b["genre"] == genre])


def all_tags() -> list[str]:
    return sorted({t for b in BOOKS.values() for t in b["tags"]})


def add_book(book_data: dict) -> dict:
    return deepcopy(_new_book(book_data))


def update_book(book_id: int, book_data: dict, change_note: str = "", notify: bool = False) -> dict:
    book = BOOKS.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    for key in ("title", "author", "price", "in_stock", "description"):
        if key in book_data:
            book[key] = book_data[key]
    if "genre" in book_data:
        book["genre"] = _plain(book_data["genre"])
    if "tags" in book_data:
        book["tags"] = sorted(set(book_data["tags"] or []))
    book["price"] = float(book["price"])
    CHANGE_LOG.append({"book_id": book_id, "note": change_note, "notified": notify,
                       "at": datetime.now(timezone.utc)})
    return deepcopy(book)


def delete_book(book_id: int) -> None:
    get_book_or_404(book_id)
    del BOOKS[book_id]
    REVIEWS.pop(book_id, None)


def convert_price(book: dict, currency: str = "BDT") -> dict:
    """Return a copy of one book with its price in BDT or USD."""
    book = deepcopy(book)
    if currency == "USD" and book.get("currency", "BDT") == "BDT":
        book["price"] = round(book["price"] / BDT_PER_USD, 2)
        book["currency"] = "USD"
    return book


def convert_prices(books: list[dict], currency: str = "BDT") -> list[dict]:
    return [convert_price(b, currency) for b in books]


def recommend(preferred_genre=None, count: int = 4) -> list[dict]:
    """Highest-rated, in-stock books, from the preferred genre first."""
    preferred_genre = _plain(preferred_genre)
    books = [b for b in BOOKS.values() if b["in_stock"]]
    books.sort(key=lambda b: (b["genre"] != preferred_genre, -(b["rating"] or 0), b["price"]))
    return deepcopy(books[:count])


# ---------- reviews ----------

def add_review(book_id: int, review: dict) -> dict:
    book = BOOKS.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    stored = {"id": len(REVIEWS[book_id]) + 1, "book_id": book_id, **review,
              "created_at": datetime.now(timezone.utc)}
    REVIEWS[book_id].append(stored)
    ratings = [r["rating"] for r in REVIEWS[book_id]]
    book["rating"] = round(sum(ratings) / len(ratings), 1)
    book["review_count"] = len(ratings)
    return deepcopy(stored)


def list_reviews(book_id: int) -> list[dict]:
    get_book_or_404(book_id)
    return deepcopy(REVIEWS[book_id])


# ---------- orders ----------

def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_order(order: dict) -> dict:
    """order = OrderCreate.model_dump(). Prices are always in BDT."""
    lines = []
    subtotal = Decimal("0")
    for item in order["items"]:
        book = BOOKS.get(item["book_id"])
        if book is None:
            raise HTTPException(status_code=404, detail=f"Book {item['book_id']} not found")
        if not book["in_stock"]:
            raise HTTPException(status_code=409, detail=f"'{book['title']}' is out of stock")
        unit = _money(book["price"])
        line_total = unit * item["quantity"]
        subtotal += line_total
        lines.append({"book_id": book["id"], "title": book["title"], "quantity": item["quantity"],
                      "unit_price": unit, "line_total": line_total})
    codes = sorted({c.strip().upper() for c in order.get("coupons") or []})
    rate = max((COUPONS.get(c, Decimal("0")) for c in codes), default=Decimal("0"))
    discount = _money(subtotal * rate)
    stored = {
        "order_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
        "customer": order["customer"],
        "items": lines,
        "coupons": codes,
        "subtotal": subtotal,
        "discount": discount,
        "total": subtotal - discount,
        "currency": "BDT",
        "deliver_by": order.get("deliver_by"),
        "status": "received",
    }
    ORDERS[stored["order_id"]] = stored
    return deepcopy(stored)


def get_order_or_404(order_id: uuid.UUID) -> dict:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return deepcopy(ORDERS[order_id])


# ---------- users ----------

def fake_hash(password: str) -> str:
    """NOT real password security. Real hashing comes in the security lessons."""
    return "fakehash$" + hashlib.sha256(password.encode()).hexdigest()[:20]


def save_user(user: dict) -> dict:
    """user = UserInDB.model_dump() (must include hashed_password)."""
    if "hashed_password" not in user or "password" in user:
        raise HTTPException(status_code=500, detail="Store hashed_password only, never the plain password")
    if user["username"] in USERS:
        raise HTTPException(status_code=409, detail=f"Username '{user['username']}' is already taken")
    USERS[user["username"]] = deepcopy(user)
    return deepcopy(user)


def verify_user(username: str, password: str) -> dict:
    user = USERS.get(username)
    if user is None or user["hashed_password"] != fake_hash(password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return deepcopy(user)


# ---------- book requests (form model) ----------

def save_book_request(request: dict) -> dict:
    stored = {"id": len(BOOK_REQUESTS) + 1, **request, "status": "pending",
              "created_at": datetime.now(timezone.utc)}
    BOOK_REQUESTS.append(stored)
    return deepcopy(stored)


# ---------- files ----------

def _check_image(file: UploadFile) -> str:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail=f"'{file.filename}' is not an image")
    suffix = Path(file.filename or "cover.png").suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        suffix = ".png"
    return suffix


def save_cover(book_id: int, file: UploadFile) -> str:
    """Save an uploaded image as the book's cover and return its URL."""
    book = BOOKS.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    suffix = _check_image(file)
    name = f"book-{book_id}-{uuid.uuid4().hex[:8]}{suffix}"
    with open(UPLOAD_DIR / name, "wb") as out:
        shutil.copyfileobj(file.file, out)
    book["cover_url"] = f"/uploads/{name}"
    return book["cover_url"]


def add_book_with_cover(book_data: dict, cover: UploadFile | None = None) -> dict:
    if cover is not None and cover.filename:
        _check_image(cover)
    book = _new_book(book_data)
    if cover is not None and cover.filename:
        save_cover(book["id"], cover)
    return deepcopy(BOOKS[book["id"]])


def import_csv(content: bytes) -> dict:
    """Import books from CSV bytes with columns: title,author,genre,price[,tags]."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="The file must be UTF-8 text")
    reader = csv.DictReader(io.StringIO(text))
    required = {"title", "author", "genre", "price"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise HTTPException(status_code=400, detail="CSV needs the columns: title, author, genre, price")
    valid_genres = {"fiction", "fantasy", "science", "history", "programming", "children"}
    imported, skipped = [], []
    for line_no, row in enumerate(reader, start=2):
        try:
            price = float(row["price"])
            genre = row["genre"].strip().lower()
            if not row["title"].strip() or genre not in valid_genres or price <= 0:
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            skipped.append(line_no)
            continue
        tags = [t.strip().lower() for t in (row.get("tags") or "").split(";") if t.strip()]
        book = _new_book({"title": row["title"].strip(), "author": row["author"].strip(),
                          "genre": genre, "price": price, "tags": tags})
        imported.append(book["title"])
    return {"imported": len(imported), "titles": imported, "skipped_lines": skipped,
            "size_bytes": len(content)}


reset()
