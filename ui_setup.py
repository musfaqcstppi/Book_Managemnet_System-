"""
Serves the BookStore web UI from FastAPI.

GIVEN CODE: you do not need to edit this file.
(Serving static files is lesson 44; for today, just know that this makes
http://127.0.0.1:8000/ show the shop, and /uploads show uploaded covers.)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"


def setup_ui(app: FastAPI) -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")
