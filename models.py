"""
BookStore Pydantic models: STARTER. You add models here as the checkpoints ask.

Add imports as you need them, for example:
    from datetime import date
    from enum import Enum
    from typing import Literal
"""

from pydantic import BaseModel, Field  # noqa: F401

# A simple email pattern: use it as Field(pattern=EMAIL_PATTERN)
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ======================================================================
# TODO CP1 · Genre: the six genres the shop sells
# ======================================================================
# class Genre(str, ____):
#     fiction = "fiction"
#     fantasy = "___"
#     science = "science"
#     history = "history"
#     programming = "programming"
#     children = "children"


# ======================================================================
# TODO CP3 · BookCreate: what the client sends to add a book
# ======================================================================
# class BookCreate(___):
#     title: ___
#     author: str
#     genre: ___
#     price: float
#     in_stock: bool = ___          # in stock unless the client says otherwise
#     description: str | None = ___ # optional


# ======================================================================
# TODO CP5 · Review
#   user (str) · rating (int) · comment (optional str)
# ======================================================================


# ======================================================================
# TODO CP6 · Field rules: come back to BookCreate and Review
#   BookCreate:  title 1–120 chars · author 2–60 chars · price > 0 and ≤ 10000
#                description at most 500 chars
#   Review:      user 2–40 chars · rating 1–5 · comment at most 300 chars
# ======================================================================


# ======================================================================
# TODO CP7 · Nested models
#   BookCreate gets:  tags: set[str] = set()
#   Customer:     name (2–60 chars) · email (EMAIL_PATTERN) · phone (optional)
#   OrderItem:    book_id (at least 1) · quantity (default 1, between 1 and 10)
#   OrderCreate:  customer: Customer · items: list[OrderItem] (at least one)
#                 coupons: set[str] = set() · deliver_by: date | None = None
# ======================================================================


# ======================================================================
# TODO CP8 · Currency: the only values allowed in the X-Currency header
#   Currency = Literal["BDT", "USD"]
# ======================================================================


# ======================================================================
# TODO CP9 · Parameter models
#   BookFilter:     model_config = {"extra": "forbid"}
#                   skip, limit, genre, in_stock, q (same rules as in list_books)
#                   tag: list[str] = []
#   Preferences:    preferred_genre: Genre | None = None
#   ClientHeaders:  user_agent, accept_language (optional str)
#                   x_currency: Currency = "BDT"
# ======================================================================


# ======================================================================
# TODO CP10 · Response models
#   BookOut:   id, title, author, genre, price, currency = "BDT", in_stock,
#              description (optional), tags: list[str] = [], cover_url (optional),
#              rating (optional float), review_count: int = 0
#              → no cost_price and no supplier!
#   BookList:  total, skip, limit, items: list[BookOut]
#   UserBase:  username (3–20 chars, pattern r"^[a-z0-9_]+$") · email (EMAIL_PATTERN)
#              full_name (optional)
#   UserIn(UserBase):    password (at least 8 chars)
#   UserOut(UserBase):   nothing extra
#   UserInDB(UserBase):  hashed_password: str
# ======================================================================


# ======================================================================
# TODO CP12 · BookRequestForm: the "Request a book" form
#   title (1–120 chars) · author (optional) · email (EMAIL_PATTERN)
#   note (optional, at most 300 chars)
# ======================================================================
