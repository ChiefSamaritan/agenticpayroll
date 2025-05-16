import pytest
from app.main import app
from app.database.connection import AsyncSessionLocal
from fastapi.testclient import TestClient

@pytest.fixture
async def async_db_session():
    async with AsyncSessionLocal() as session:
        yield session