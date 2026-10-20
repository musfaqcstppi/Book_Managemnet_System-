"""Shared test setup. GIVEN CODE: no need to edit.

Run one checkpoint:   pytest -k cp03
Run everything:       pytest
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

import data  # noqa: E402
from main import app  # noqa: E402

BOOK = {"title": "Think Python", "author": "Allen B. Downey", "genre": "programming",
        "price": 1650, "in_stock": True, "description": "Learn to think like a programmer."}


@pytest.fixture
def client(tmp_path, monkeypatch):
    data.reset()
    monkeypatch.setattr(data, "UPLOAD_DIR", tmp_path)  # keep test uploads out of uploads/
    with TestClient(app) as c:
        yield c


def ok(response, *codes):
    """Assert the status code, showing the server's answer when it is wrong."""
    codes = codes or (200,)
    assert response.status_code in codes, (
        f"expected status {' or '.join(map(str, codes))}, got {response.status_code}: {response.text[:300]}")
    return response
