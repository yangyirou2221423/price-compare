"""Test bootstrap: use an isolated SQLite database and seed catalogue."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "pricecompare_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()

ROOT = Path(__file__).resolve().parents[2]
os.environ["PRICECOMPARE_DB_PATH"] = str(TEST_DB)
os.environ["PRICECOMPARE_SEED_PATH"] = str(ROOT / "data" / "seed" / "catalog.json")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
